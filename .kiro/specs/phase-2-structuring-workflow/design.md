# Design Document: Phase 2 - Structuring & Workflow Pipeline

## Overview

Phase 2 transforms ReqGate from a standalone scoring system into a complete requirement processing pipeline. The design introduces three major components:

1. **Structuring Agent**: An LLM-based component that converts unstructured text into standardized PRD format
2. **Input Guardrail**: A pre-processing layer that validates, sanitizes, and protects against malicious inputs
3. **LangGraph Workflow**: An orchestration layer that connects all components (Guardrail → Structuring → Scoring → Gate) with intelligent fallback mechanisms

The architecture maintains strict separation of concerns: each component operates independently through well-defined schemas, enabling testability, maintainability, and future extensibility.

### Key Design Principles

- **Schema-Driven**: All data flows through Pydantic schemas (no dict passing)
- **Fail-Safe**: Structuring failures trigger fallback to direct scoring
- **Observable**: Every stage logs execution details to AgentState
- **Stateless Nodes**: Each workflow node is a pure function of AgentState
- **Retry-Resilient**: Transient LLM failures are automatically retried

## Architecture

### High-Level Data Flow

```
Input Text
    ↓
[Input Guardrail]
    ↓ (validated RequirementPacket)
[Structuring Agent]
    ↓ (PRD_Draft) ──────┐ (on failure)
    ↓                    ↓
[Scoring Agent] ←────────┘ (fallback: raw text)
    ↓ (TicketScoreReport)
[Hard Gate]
    ↓ (GateDecision)
Output
```

### LangGraph Workflow DAG

```mermaid
graph TD
    Start([Start]) --> Guardrail[Input Guardrail]
    Guardrail --> Structuring[Structuring Agent]
    Structuring -->|Success| Scoring[Scoring Agent]
    Structuring -->|Failure| Scoring
    Scoring --> Gate[Hard Gate]
    Gate --> End([End])
```

### Component Responsibilities

| Component | Input | Output | Responsibility |
|-----------|-------|--------|----------------|
| Input Guardrail | Raw text | RequirementPacket | Validate length, detect PII, block prompt injection |
| Structuring Agent | RequirementPacket | PRD_Draft | Extract user story, AC, dependencies; identify gaps |
| Scoring Agent | PRD_Draft or RequirementPacket | TicketScoreReport | Evaluate quality against rubric |
| Hard Gate | TicketScoreReport | GateDecision | Accept/reject based on score and blockers |

## Components and Interfaces

### 1. PRD_Draft Schema

**Location**: `src/reqgate/schemas/internal.py` (extends existing file from Phase 1)

> **Note**: This file already contains `AgentState` from Phase 1. We extend it with `PRD_Draft`.

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class PRD_Draft(BaseModel):
    """
    Structured PRD draft produced by Structuring Agent.
    
    This is an intermediate representation that bridges unstructured input
    and the scoring process. It may contain incomplete information, which
    is captured in missing_info and clarification_questions fields.
    """
    
    title: str = Field(
        ...,
        min_length=10,
        max_length=200,
        description="Descriptive title starting with an action verb"
    )
    
    user_story: str = Field(
        ...,
        min_length=20,
        description="User story in 'As a X, I want Y, so that Z' format"
    )
    
    acceptance_criteria: List[str] = Field(
        ...,
        min_items=1,
        description="List of discrete acceptance criteria"
    )
    
    edge_cases: List[str] = Field(
        default_factory=list,
        description="Identified edge cases or error scenarios"
    )
    
    resources: List[str] = Field(
        default_factory=list,
        description="Dependencies, related tickets, or external resources"
    )
    
    # Agent self-diagnosis fields
    missing_info: List[str] = Field(
        default_factory=list,
        description="Information gaps identified by the agent"
    )
    
    clarification_questions: List[str] = Field(
        default_factory=list,
        description="Questions to ask the PM for clarification"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Implement user authentication with OAuth2",
                "user_story": "As a user, I want to log in with Google, so that I don't need to create a new password",
                "acceptance_criteria": [
                    "User can click 'Sign in with Google' button",
                    "System redirects to Google OAuth consent screen",
                    "After approval, user is logged into the application"
                ],
                "edge_cases": ["User denies OAuth consent", "Google service is down"],
                "resources": ["OAuth2 RFC 6749", "Google OAuth documentation"],
                "missing_info": ["Session timeout duration not specified"],
                "clarification_questions": ["Should we support other OAuth providers?"]
            }
        }
```

### 2. AgentState Schema

**Location**: `src/reqgate/schemas/internal.py`

```python
from typing import TypedDict, Optional, List
from src.reqgate.schemas.inputs import RequirementPacket
from src.reqgate.schemas.outputs import TicketScoreReport
from src.reqgate.schemas.internal import PRD_Draft

class AgentState(TypedDict):
    """
    Shared state object for LangGraph workflow.
    
    This state flows through all workflow nodes, accumulating results
    and metadata at each stage. Nodes read from and write to this state.
    """
    
    # Input
    packet: RequirementPacket
    
    # Intermediate results
    structured_prd: Optional[PRD_Draft]
    score_report: Optional[TicketScoreReport]
    gate_decision: Optional[bool]
    
    # Control and observability
    current_stage: str
    retry_count: int
    error_logs: List[str]
    fallback_activated: bool
    execution_times: dict[str, float]  # node_name -> seconds
```

### 3. Input Guardrail

**Location**: `src/reqgate/workflow/nodes/input_guardrail.py`

**Interface**:
```python
def input_guardrail_node(state: AgentState) -> AgentState:
    """
    Validates and sanitizes input before processing.
    
    Checks:
    - Length constraints (50-10,000 characters)
    - PII detection (emails, phones, credit cards)
    - Prompt injection patterns
    
    Returns:
        Updated state with validation results or error logs
    
    Raises:
        ValueError: If input fails validation and cannot be sanitized
    """
```

**Implementation Strategy**:
- Use regex patterns for PII detection
- Maintain configurable pattern list for prompt injection
- Log warnings for detected issues (don't always reject)
- Support strict/lenient modes via configuration

**Configuration** (`config/guardrail_config.yaml`):
```yaml
input_guardrail:
  min_length: 50
  max_length: 10000
  
  pii_detection:
    enabled: true
    mode: "lenient"  # strict | lenient
    patterns:
      email: true
      phone: true
      credit_card: true
  
  prompt_injection:
    enabled: true
    action: "reject"  # reject | sanitize | warn
    patterns:
      - "ignore previous instructions"
      - "you are now"
      - "system prompt"
      - "disregard"
```

### 4. Structuring Agent

**Location**: `src/reqgate/workflow/nodes/structuring_agent.py`

**Interface**:
```python
def structuring_agent_node(state: AgentState) -> AgentState:
    """
    Extracts structured PRD from unstructured text.
    
    Uses LLM to parse input and populate PRD_Draft schema.
    Includes anti-hallucination instructions in prompt.
    
    Returns:
        State with structured_prd populated, or error logged if extraction fails
    """
```

**Prompt Template** (`prompts/structuring_agent.txt`):
```
You are a requirements structuring assistant. Your job is to extract structured information from unstructured requirement text.

**CRITICAL RULES**:
1. ONLY extract information explicitly present in the input
2. DO NOT invent, assume, or hallucinate details
3. If information is missing, add it to "missing_info" field
4. If clarification is needed, add specific questions to "clarification_questions"

**Input Text**:
{input_text}

**Your Task**:
Extract the following information and format it as JSON matching this schema:
{prd_draft_schema}

**Guidelines**:
- Title: Start with an action verb (e.g., "Implement", "Add", "Fix")
- User Story: Use "As a [role], I want [feature], so that [benefit]" format
- Acceptance Criteria: Break into discrete, testable statements
- Edge Cases: Identify error scenarios or boundary conditions mentioned
- Resources: Extract any mentioned dependencies, tickets, or documentation
- Missing Info: List any critical information not provided
- Clarification Questions: Ask specific questions to fill gaps

**Example Output**:
{example_prd_draft}

Now extract the structured information from the input text above.
```

**Anti-Hallucination Techniques**:
1. Explicit "DO NOT invent" instructions
2. Require quoting source text for acceptance criteria
3. Validate output against input (check for phrases not in source)
4. Use temperature=0 for deterministic extraction
5. Schema validation catches malformed outputs

### 5. LangGraph Workflow

**Location**: `src/reqgate/workflow/graph.py`

**Interface**:
```python
def create_workflow() -> StateGraph:
    """
    Creates the LangGraph workflow definition.
    
    Returns:
        Compiled StateGraph ready for execution
    """

def run_workflow(
    packet: RequirementPacket,
    config: Optional[WorkflowConfig] = None
) -> AgentState:
    """
    Executes the complete workflow.
    
    Args:
        packet: Input requirement packet
        config: Optional workflow configuration
    
    Returns:
        Final AgentState with all results
    
    Raises:
        WorkflowExecutionError: If workflow fails unrecoverably
    """
```

**Implementation**:
```python
from langgraph.graph import StateGraph, END
from src.reqgate.schemas.internal import AgentState

def create_workflow() -> StateGraph:
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("guardrail", input_guardrail_node)
    workflow.add_node("structuring", structuring_agent_node)
    workflow.add_node("scoring", scoring_agent_node)
    workflow.add_node("gate", hard_gate_node)
    
    # Add edges
    workflow.set_entry_point("guardrail")
    workflow.add_edge("guardrail", "structuring")
    
    # Conditional edge: structuring success → scoring, failure → scoring (fallback)
    workflow.add_conditional_edges(
        "structuring",
        should_fallback,
        {
            "continue": "scoring",
            "fallback": "scoring"
        }
    )
    
    workflow.add_edge("scoring", "gate")
    workflow.add_edge("gate", END)
    
    return workflow.compile()

def should_fallback(state: AgentState) -> str:
    """Routing function for conditional edge."""
    if state.get("structured_prd") is None:
        return "fallback"
    return "continue"
```

### 6. Fallback Mechanism

**Strategy**: When Structuring Agent fails, route directly to Scoring Agent with raw text.

**Implementation**:
```python
def scoring_agent_node(state: AgentState) -> AgentState:
    """
    Scores requirement quality.
    
    Handles two input modes:
    1. Structured mode: Uses PRD_Draft if available
    2. Fallback mode: Uses raw text from RequirementPacket
    """
    if state.get("structured_prd"):
        # Structured mode: format PRD_Draft for scoring
        input_text = format_prd_for_scoring(state["structured_prd"])
    else:
        # Fallback mode: use raw text
        input_text = state["packet"].raw_text
        state["fallback_activated"] = True
        state["error_logs"].append("Structuring failed, using fallback mode")
    
    # Continue with scoring logic...
```

### 7. Retry Logic

**Location**: `src/reqgate/adapters/llm.py` (extend from Phase 1)

**Interface**:
```python
def call_llm_with_retry(
    prompt: str,
    max_retries: int = 3,
    timeout: float = 30.0
) -> str:
    """
    Calls LLM with exponential backoff retry.
    
    Args:
        prompt: Input prompt
        max_retries: Maximum retry attempts
        timeout: Timeout per attempt in seconds
    
    Returns:
        LLM response text
    
    Raises:
        LLMTimeoutError: If all retries exhausted
        LLMRateLimitError: If rate limited after retries
    """
```

**Implementation**:
```python
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def call_llm_with_retry(prompt: str, timeout: float = 30.0) -> str:
    try:
        response = llm_client.generate(
            prompt=prompt,
            timeout=timeout,
            temperature=0
        )
        return response.text
    except TimeoutError:
        logger.warning("LLM call timed out, retrying...")
        raise
    except RateLimitError:
        logger.warning("LLM rate limited, retrying...")
        raise
```

## Data Models

### Workflow Configuration

```python
from pydantic import BaseModel

class WorkflowConfig(BaseModel):
    """Configuration for workflow execution."""
    
    enable_guardrail: bool = True
    enable_structuring: bool = True
    enable_fallback: bool = True
    
    max_retries: int = 3
    llm_timeout: float = 30.0
    
    guardrail_mode: Literal["strict", "lenient"] = "lenient"
    
    class Config:
        json_schema_extra = {
            "example": {
                "enable_guardrail": True,
                "enable_structuring": True,
                "enable_fallback": True,
                "max_retries": 3,
                "llm_timeout": 30.0,
                "guardrail_mode": "lenient"
            }
        }
```

### Error Types

```python
class WorkflowExecutionError(Exception):
    """Base exception for workflow failures."""
    pass

class GuardrailRejectionError(WorkflowExecutionError):
    """Input rejected by guardrail."""
    pass

class StructuringFailureError(WorkflowExecutionError):
    """Structuring agent failed to produce valid output."""
    pass

class LLMTimeoutError(WorkflowExecutionError):
    """LLM call timed out after retries."""
    pass
```


## Testing Strategy

### Unit Tests

1. **PRD_Draft Schema Tests** (`tests/test_prd_draft_schema.py`)
   - Valid PRD with all fields
   - PRD with missing optional fields
   - PRD with invalid title (too short)
   - PRD with empty acceptance criteria

2. **Input Guardrail Tests** (`tests/test_input_guardrail.py`)
   - Text too short (< 50 chars)
   - Text too long (> 10,000 chars)
   - Text containing email addresses
   - Text containing prompt injection patterns
   - Valid text passes through

3. **Structuring Agent Tests** (`tests/test_structuring_agent.py`)
   - Extract from well-formatted text
   - Extract from messy meeting transcript
   - Handle text with missing AC
   - Detect missing information
   - Generate clarification questions
   - Anti-hallucination: verify no invented content

4. **Workflow Tests** (`tests/test_workflow.py`)
   - Happy path: all nodes succeed
   - Fallback path: structuring fails
   - Retry path: LLM timeout then success
   - Error path: guardrail rejects input

### Integration Tests

1. **End-to-End Workflow** (`tests/test_integration_workflow.py`)
   - Input meeting transcript → structured PRD → scored → gated
   - Verify state transitions
   - Verify execution times logged
   - Verify error handling

2. **Fallback Scenario** (`tests/test_fallback_integration.py`)
   - Mock structuring failure
   - Verify scoring continues with raw text
   - Verify fallback flag set
   - Verify score penalty applied

### Property-Based Tests

1. **Structuring Idempotency**
   - Running structuring twice on same input produces same output

2. **Workflow State Consistency**
   - AgentState always contains required fields
   - No state corruption across nodes

## Configuration

### Environment Variables

```bash
# Existing from Phase 1
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o
OPENAI_TIMEOUT=30

# New for Phase 2
ENABLE_STRUCTURING=true
ENABLE_GUARDRAIL=true
GUARDRAIL_MODE=lenient
MAX_LLM_RETRIES=3
STRUCTURING_TIMEOUT=20
```

### Guardrail Configuration

**File**: `config/guardrail_config.yaml`

```yaml
input_guardrail:
  min_length: 50
  max_length: 10000
  
  pii_detection:
    enabled: true
    mode: "lenient"
    patterns:
      email: true
      phone: true
      credit_card: false
  
  prompt_injection:
    enabled: true
    action: "reject"
    patterns:
      - "ignore previous instructions"
      - "you are now"
      - "system prompt"
      - "disregard all"
      - "forget everything"
```

## Performance Considerations

### Latency Budget

| Component | Target (P50) | Target (P95) | Notes |
|-----------|--------------|--------------|-------|
| Input Guardrail | 50ms | 100ms | Regex-based, should be fast |
| Structuring Agent | 10s | 20s | LLM call, main bottleneck |
| Scoring Agent | 10s | 20s | LLM call |
| Hard Gate | 10ms | 50ms | Pure logic, very fast |
| **Total Workflow** | 25s | 50s | Target: under 60s |

### Optimization Strategies

1. **Parallel LLM Calls** (Future)
   - Run structuring and scoring in parallel if structuring is optional
   - Requires async implementation

2. **Prompt Optimization**
   - Keep prompts concise
   - Use structured output format (JSON mode)
   - Minimize few-shot examples

3. **Caching** (Phase 4)
   - Cache structuring results for identical inputs
   - Cache scoring results for identical PRDs

## Security Considerations

### PII Handling

1. **Detection**: Regex patterns for common PII types
2. **Action**: Log warning, optionally redact or reject
3. **Logging**: Never log detected PII values

### Prompt Injection Defense

1. **Pattern Matching**: Detect common injection phrases
2. **Input Sanitization**: Remove or escape suspicious patterns
3. **LLM Instructions**: Include anti-jailbreak instructions in system prompt

### Data Flow Security

```
User Input (untrusted)
    ↓
[Guardrail] ← PII detection, injection blocking
    ↓
[Structuring] ← Anti-hallucination instructions
    ↓
[Scoring] ← Structured data only
    ↓
Output (safe)
```

## Error Handling

### Error Propagation Strategy

1. **Guardrail Errors**: Fail fast, return 400 error
2. **Structuring Errors**: Log and fallback to raw mode
3. **Scoring Errors**: Retry, then fail with 503
4. **Gate Errors**: Should never happen (pure logic)

### Error Response Format

```python
class WorkflowError(BaseModel):
    stage: str  # Which node failed
    error_type: str  # GuardrailRejection, LLMTimeout, etc.
    message: str  # Human-readable error
    retry_count: int
    fallback_activated: bool
```

## Deployment

Phase 2 remains local development only. No deployment changes from Phase 1.

## Migration from Phase 1

### Breaking Changes

None. Phase 2 is additive. All Phase 1 tests must continue to pass.

### File Modifications (Extend, Don't Replace)

| Phase 1 File | Phase 2 Action | Notes |
|--------------|----------------|-------|
| `src/reqgate/schemas/internal.py` | **Extend** | Add `PRD_Draft` schema alongside existing `AgentState` |
| `src/reqgate/schemas/config.py` | **Extend** | Add `WorkflowConfig` alongside existing `RubricScenarioConfig` |
| `src/reqgate/adapters/llm.py` | **Extend** | Add `call_llm_with_retry()` function, keep existing `LLMClient` |
| `src/reqgate/config/settings.py` | **Extend** | Add Phase 2 config fields (enable_structuring, etc.) |
| `.env.example` | **Extend** | Add Phase 2 environment variables |

### New Files

| File | Purpose |
|------|---------|
| `src/reqgate/workflow/` | New workflow module |
| `src/reqgate/workflow/graph.py` | LangGraph workflow definition |
| `src/reqgate/workflow/nodes/` | Workflow node wrappers |
| `src/reqgate/workflow/errors.py` | Workflow-specific exceptions |
| `config/guardrail_config.yaml` | Guardrail configuration |
| `prompts/structuring_agent_v1.txt` | Structuring prompt template |

### AgentState Evolution

Phase 1 `AgentState` is extended (not replaced):

```python
# Phase 1 fields (keep)
packet: RequirementPacket
score_report: Optional[TicketScoreReport]
retry_count: int
error_logs: List[str]
current_stage: str

# Phase 2 additions
structured_prd: Optional[PRD_Draft]      # NEW
gate_decision: Optional[bool]            # NEW
fallback_activated: bool                 # NEW
execution_times: dict[str, float]        # NEW
```

### Backward Compatibility Requirements

1. **Phase 1 API unchanged**: `ScoringAgent.score()` and `HardGate.decide()` signatures must not change
2. **Phase 1 tests pass**: All 82 Phase 1 tests must continue to pass
3. **Schema compatibility**: Existing `RequirementPacket`, `TicketScoreReport`, `ReviewIssue` unchanged
4. **Config compatibility**: Existing `.env` files work without modification (new fields have defaults)

### New Dependencies

Add to `pyproject.toml`:
```toml
[project.dependencies]
langgraph = ">=0.2.0"
tenacity = ">=8.2.0"  # For retry logic
```

> **Note**: Check if `tenacity` is already included via other dependencies before adding.

### Configuration Updates

Add to `.env.example`:
```bash
# Phase 2 Configuration
ENABLE_STRUCTURING=true
ENABLE_GUARDRAIL=true
GUARDRAIL_MODE=lenient
MAX_LLM_RETRIES=3
STRUCTURING_TIMEOUT=20
GUARDRAIL_CONFIG_PATH=config/guardrail_config.yaml
```

Add to `src/reqgate/config/settings.py`:
```python
# Phase 2 Configuration
enable_structuring: bool = True
enable_guardrail: bool = True
guardrail_mode: Literal["strict", "lenient"] = "lenient"
max_llm_retries: int = 3
structuring_timeout: int = 20
guardrail_config_path: str = "config/guardrail_config.yaml"
```


## Future Enhancements (Phase 3+)

- Async workflow execution
- Webhook callbacks for long-running workflows
- Parallel node execution
- Workflow visualization/debugging UI
- A/B testing different structuring prompts

## Appendix: Prompt Templates

### Structuring Agent Prompt (v1.0)

**File**: `prompts/structuring_agent_v1.txt`

```
# Role
You are a requirements structuring assistant. Your job is to extract structured information from unstructured requirement text.

# Critical Rules
1. ONLY extract information explicitly present in the input
2. DO NOT invent, assume, or hallucinate details
3. If information is missing, add it to "missing_info" field
4. If clarification is needed, add specific questions to "clarification_questions"

# Input Text
{input_text}

# Output Schema
You must produce JSON matching this exact schema:
{prd_draft_schema}

# Extraction Guidelines

## Title
- Start with an action verb (e.g., "Implement", "Add", "Fix")
- Be specific and descriptive
- Length: 10-200 characters

## User Story
- Format: "As a [role], I want [feature], so that [benefit]"
- Extract from input or infer from context
- If not clear, mark in missing_info

## Acceptance Criteria
- Break into discrete, testable statements
- Use Given/When/Then format if possible
- Minimum 1 criterion required
- If none found, add to missing_info and clarification_questions

## Edge Cases
- Identify error scenarios mentioned
- Include boundary conditions
- DO NOT invent scenarios not mentioned

## Resources
- Extract URLs, ticket references, documentation links
- Include dependencies mentioned

## Missing Info
- List any critical information not provided
- Be specific about what's missing

## Clarification Questions
- Ask specific questions to fill gaps
- Make questions actionable

# Example Output
{example_json}

# Now Process
Extract structured information from the input text above. Output ONLY valid JSON.
```

### Anti-Hallucination Validation

After LLM returns structured output, validate:

```python
def validate_no_hallucination(
    input_text: str,
    prd_draft: PRD_Draft
) -> List[str]:
    """
    Checks if PRD contains information not in input.
    
    Returns:
        List of suspicious phrases (empty if clean)
    """
    suspicious = []
    
    # Check if AC phrases exist in input
    for ac in prd_draft.acceptance_criteria:
        # Extract key phrases from AC
        key_phrases = extract_key_phrases(ac)
        for phrase in key_phrases:
            if phrase.lower() not in input_text.lower():
                suspicious.append(f"AC contains '{phrase}' not found in input")
    
    return suspicious
```

## Correctness Properties

### Property 1: Workflow Completeness
**Statement**: Every workflow execution must visit all required nodes (guardrail, scoring, gate) regardless of structuring success.

**Test**:
```python
def test_workflow_completeness(input_packet):
    state = run_workflow(input_packet)
    assert "guardrail" in state["execution_times"]
    assert "scoring" in state["execution_times"]
    assert "gate" in state["execution_times"]
```

### Property 2: Fallback Consistency
**Statement**: If structuring fails, fallback_activated must be True and structured_prd must be None.

**Test**:
```python
def test_fallback_consistency(state_after_structuring_failure):
    if state["fallback_activated"]:
        assert state["structured_prd"] is None
    if state["structured_prd"] is None:
        assert state["fallback_activated"] is True
```

### Property 3: State Monotonicity
**Statement**: AgentState fields can only be added or updated, never removed.

**Test**:
```python
def test_state_monotonicity(initial_state, final_state):
    for key in initial_state:
        assert key in final_state
```

### Property 4: No Hallucination
**Statement**: All acceptance criteria in PRD_Draft must reference concepts present in input text.

**Test**:
```python
def test_no_hallucination(input_text, prd_draft):
    for ac in prd_draft.acceptance_criteria:
        key_terms = extract_nouns_and_verbs(ac)
        assert any(term in input_text for term in key_terms)
```

## Decision Log

### Decision 1: LangGraph vs Custom Orchestration
**Chosen**: LangGraph
**Rationale**: 
- Built-in state management
- Conditional edges for fallback logic
- Observable execution traces
- Industry standard for agent workflows

**Alternatives Considered**:
- Custom Python orchestration (too much boilerplate)
- Airflow (overkill for single-machine workflows)

### Decision 2: Fallback Strategy
**Chosen**: Continue to scoring with raw text
**Rationale**:
- Provides degraded but functional service
- Avoids complete workflow failure
- Scoring on raw text still provides value

**Alternatives Considered**:
- Fail entire workflow (too brittle)
- Retry structuring indefinitely (wastes time)

### Decision 3: Guardrail Placement
**Chosen**: First node in workflow
**Rationale**:
- Fail fast on invalid input
- Prevents wasted LLM calls
- Clear separation of concerns

**Alternatives Considered**:
- After structuring (too late, wastes LLM call)
- Integrated into structuring (violates SRP)

### Decision 4: Retry Mechanism
**Chosen**: Exponential backoff with max 3 retries
**Rationale**:
- Handles transient LLM failures
- Exponential backoff prevents thundering herd
- 3 retries balances reliability vs latency

**Alternatives Considered**:
- No retries (too fragile)
- Unlimited retries (could hang forever)
- Fixed delay (doesn't handle rate limits well)
