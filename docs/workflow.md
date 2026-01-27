# Workflow Documentation

> **Phase 2.2 Complete** - Full 7-node LangGraph workflow with Hard Check #1.

## Overview

ReqGate uses LangGraph to orchestrate a multi-stage requirement processing workflow. The workflow transforms raw requirement text into a structured format, evaluates quality, and makes pass/reject decisions.

## Workflow Stages (7 Nodes)

### 1. Input Guardrail

**Purpose**: Validate and sanitize user input before processing.

**Checks**:
- Length constraints (50-10,000 characters)
- PII detection (emails, phones, credit cards)
- Prompt injection patterns

**Modes**:
- `strict`: Reject on any violation
- `lenient`: Warn but continue (except for injection)

**Configuration**: `config/guardrail_config.yaml`

```yaml
input_guardrail:
  min_length: 50
  max_length: 10000
  
  pii_detection:
    enabled: true
    mode: "lenient"
    
  prompt_injection:
    enabled: true
    action: "reject"
```

### 2. Normalize (via RequirementPacket Schema)

**Purpose**: Standardize and validate input data structure.

**Implementation**: This node is implemented through **Pydantic Schema validation** rather than a separate processing node.

**Why Schema-based**:
- All inputs must pass `RequirementPacket` validation before workflow execution
- Pydantic validators automatically clean and standardize data
- Fail-fast: invalid inputs are rejected before entering the workflow
- Schema-Driven architecture principle

**Validation Rules**:
```python
class RequirementPacket(BaseModel):
    raw_text: str = Field(..., min_length=10)  # Length validation
    source_type: Literal["Jira_Ticket", "PRD_Doc", "Meeting_Transcript"]  # Type standardization
    project_key: str = Field(..., pattern=r"^[A-Z]{2,5}$")  # Format validation
    
    @field_validator("raw_text")
    def validate_text(cls, v: str) -> str:
        return v.strip()  # Automatic whitespace normalization
```

> **Note**: The whitepaper's "Normalize" node is fully satisfied by this Schema-based approach.

### 3. Structuring Agent

**Purpose**: Convert unstructured requirement text into standardized PRD format.

**Input**: `RequirementPacket.raw_text`

**Output**: `PRD_Draft` schema containing:
- Title (action verb prefix)
- User Story (As a X, I want Y, so that Z)
- Acceptance Criteria (list)
- Edge Cases (if mentioned)
- Resources (dependencies, links)
- Missing Info (identified gaps)
- Clarification Questions (for PM)

**Anti-Hallucination Measures**:
1. Explicit "DO NOT invent" instructions
2. Temperature=0 for deterministic output
3. Output validation against input
4. Schema validation

**Prompt Template**: `prompts/structuring_agent_v1.txt`

### 4. Structure Check (Hard Check #1)

**Purpose**: Validate PRD structure completeness before scoring.

**Checks**:
1. AC count >= 2 (minimum 2 acceptance criteria)
2. User Story length >= 20 characters
3. Title length 10-200 characters
4. Title starts with action verb (recommended)

**Output**:
- `structure_check_passed`: Boolean flag
- `structure_errors`: List of validation errors

**Implementation**: `workflow/nodes/structure_check.py`

```python
def hard_check_structure_node(state: AgentState) -> AgentState:
    # Deterministic validation (no LLM)
    # Runs after structuring succeeds, skipped in fallback mode
```

**Behavior**:
- If PRD passes all checks: proceed to scoring normally
- If PRD fails checks: continue to scoring with errors recorded
- If no PRD (fallback mode): skip check entirely

### 5. Scoring Agent

**Purpose**: Evaluate requirement quality against rubric.

**Input**:
- Normal mode: Formatted `PRD_Draft`
- Fallback mode: Raw text from `RequirementPacket`

**Output**: `TicketScoreReport` containing:
- Total score (0-100)
- Dimension scores
- Review issues (blocking/non-blocking)

**Rubric Configuration**: `config/scoring_rubric.yaml`

### 6. Hard Gate (Hard Check #2)

**Purpose**: Make deterministic pass/reject decision.

**Logic**:
```python
if blocking_issues > 0 or total_score < threshold:
    return REJECT
else:
    return PASS
```

**Configuration**:
- `DEFAULT_THRESHOLD`: 60 (configurable)

### 7. Formatter

**Purpose**: Package and format the final output.

**Implementation**: Currently inline in `run_workflow()`. Will be extracted to independent node in Phase 3.

**Output**: Final `AgentState` with all results.

## State Management

The workflow uses `AgentState` (TypedDict) to share data between nodes:

```python
class AgentState(TypedDict):
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
    execution_times: dict[str, float]
    
    # Structure check results (Phase 2.2)
    structure_check_passed: Optional[bool]
    structure_errors: List[str]
```

## Fallback Mechanism

When the Structuring Agent fails:

1. Error is logged to `error_logs`
2. `fallback_activated` flag is set to `True`
3. Scoring Agent uses raw text instead of PRD_Draft
4. Score penalty (-5 points) is applied
5. Workflow continues without interruption

## Retry Logic

LLM calls use exponential backoff retry:

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def call_llm_with_retry(...):
    ...
```

**Handled Errors**:
- `LLMTimeoutError`
- `LLMRateLimitError`

## Execution Flow

### Normal Path

```
1. Input Guardrail
   └─ Validates RequirementPacket
   └─ Updates current_stage = "guardrail"
   
2. Normalize (implicit)
   └─ RequirementPacket Schema validation
   
3. Structuring Agent
   └─ Extracts PRD_Draft from raw_text
   └─ Updates structured_prd
   └─ Updates current_stage = "structuring"
   
4. Structure Check (Hard Check #1)
   └─ Validates AC count >= 2
   └─ Validates User Story format
   └─ Updates structure_check_passed, structure_errors
   └─ Updates current_stage = "structure_check"
   
5. Scoring Agent
   └─ Formats PRD_Draft for scoring
   └─ Calls LLM for evaluation
   └─ Updates score_report
   └─ Updates current_stage = "scoring"
   
6. Hard Gate (Hard Check #2)
   └─ Checks blocking_issues
   └─ Checks total_score vs threshold
   └─ Updates gate_decision
   └─ Updates current_stage = "gate"

7. Formatter (inline)
   └─ Packages final output
```

### Fallback Path

```
1. Input Guardrail (same as normal)

2. Normalize (same as normal - Schema validation)

3. Structuring Agent
   └─ LLM call fails
   └─ Logs error to error_logs
   └─ structured_prd remains None
   
4. Structure Check
   └─ Skipped (no PRD to check)
   └─ structure_check_passed = None
   
5. Scoring Agent
   └─ Detects structured_prd is None
   └─ Sets fallback_activated = True
   └─ Uses raw_text for scoring
   └─ Applies -5 score penalty
   
6. Hard Gate (same as normal)

7. Formatter (same as normal)
```

## Performance

### Latency Budget

| Component | Target (P50) | Target (P95) |
|-----------|--------------|--------------|
| Input Guardrail | 50ms | 100ms |
| Structuring Agent | 10s | 20s |
| Scoring Agent | 10s | 20s |
| Hard Gate | 10ms | 50ms |
| **Total Workflow** | 25s | 50s |

### Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `STRUCTURING_TIMEOUT` | 20 | Timeout for structuring LLM call |
| `LLM_TIMEOUT` | 60 | General LLM timeout |
| `MAX_LLM_RETRIES` | 3 | Retry attempts for LLM calls |

## Error Types

```python
# Base exception
class WorkflowExecutionError(Exception): pass

# Specific exceptions
class GuardrailRejectionError(WorkflowExecutionError): pass
class StructuringFailureError(WorkflowExecutionError): pass
class LLMTimeoutError(WorkflowExecutionError): pass
class LLMRateLimitError(WorkflowExecutionError): pass
```

## API Usage

```python
from src.reqgate.workflow.graph import run_workflow
from src.reqgate.schemas.inputs import RequirementPacket

# Create input
packet = RequirementPacket(
    ticket_id="REQ-001",
    raw_text="Your requirement text here...",
    scenario="FEATURE"
)

# Run workflow
final_state = run_workflow(packet)

# Access results
print(final_state["structured_prd"])
print(final_state["score_report"])
print(final_state["gate_decision"])
print(final_state["fallback_activated"])
```

## Testing

### Integration Tests

- `tests/test_workflow_integration.py`: Full workflow tests
- `tests/test_fallback.py`: Fallback mechanism tests

### Test Scenarios

1. **Happy Path**: All nodes succeed
2. **Fallback Path**: Structuring fails
3. **Retry Path**: LLM timeout then success
4. **Error Path**: Guardrail rejects input

## Future Enhancements (Phase 3+)

- HTTP API endpoints
- Async workflow execution
- Parallel node execution
- Webhook callbacks
- A/B testing for prompts
