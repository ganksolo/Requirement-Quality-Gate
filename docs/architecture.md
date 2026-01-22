# Architecture Overview

> **Updated for Phase 2** - Complete workflow architecture with LangGraph integration.

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────┐
│         Application Layer               │
│  (FastAPI App + Health Endpoint)        │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Configuration Layer             │
│  (Settings + Environment Variables)     │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Schema Layer                    │
│  (Pydantic Models - Data Contracts)     │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Workflow Layer (Phase 2)        │
│  (LangGraph Orchestration)              │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Business Logic Layer            │
│  (Agents + Gates)                       │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Infrastructure Layer            │
│  (LLM Adapter + Config Loader)          │
└─────────────────────────────────────────┘
```

## Key Components

### Application Layer
- **FastAPI App**: HTTP interface with health check
- **API Routes**: Endpoint definitions (Phase 3)

### Configuration Layer
- **Settings**: Environment-based configuration with pydantic-settings
- **Guardrail Config**: YAML-based guardrail configuration

### Schema Layer
- **RequirementPacket**: Input schema for requirements
- **PRD_Draft**: Structured PRD intermediate representation (Phase 2)
- **TicketScoreReport**: Output schema with scoring results
- **AgentState**: LangGraph workflow state container

### Workflow Layer (Phase 2)
- **LangGraph DAG**: Orchestrates the complete workflow
- **Input Guardrail**: Validates and sanitizes input
- **Structuring Agent**: Converts unstructured text to PRD_Draft
- **Fallback Mechanism**: Graceful degradation on failures

### Business Logic Layer
- **Scoring Agent**: LLM-based requirement evaluation
- **Hard Gate**: Deterministic pass/reject logic

### Infrastructure Layer
- **LLM Adapter**: OpenRouter/OpenAI/Gemini integration with retry logic
- **Rubric Loader**: YAML configuration loading

## LangGraph Workflow DAG

```
                    ┌─────────────────┐
                    │     START       │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Input Guardrail │
                    │  • Length check │
                    │  • PII detection│
                    │  • Injection    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Structuring     │
                    │ Agent           │
                    │  • Extract PRD  │
                    │  • Anti-halluc. │
                    └────────┬────────┘
                             │
                   ┌─────────┴─────────┐
                   │                   │
              Success              Failure
                   │                   │
                   └──────┬────────────┘
                          │
                 ┌────────▼────────┐
                 │ Scoring Agent   │
                 │  • Uses PRD or  │
                 │    raw text     │
                 └────────┬────────┘
                          │
                 ┌────────▼────────┐
                 │   Hard Gate     │
                 │  • Check score  │
                 │  • Check blocks │
                 └────────┬────────┘
                          │
                 ┌────────▼────────┐
                 │      END        │
                 └─────────────────┘
```

## Data Flow

### Normal Path (Structuring Success)
```
RequirementPacket → Guardrail → Structuring → PRD_Draft → Scoring → Gate → Decision
```

### Fallback Path (Structuring Failure)
```
RequirementPacket → Guardrail → Structuring (fail) → raw_text → Scoring → Gate → Decision
                                     │
                                     └─ fallback_activated = true
                                     └─ score penalty applied (-5)
```

## Component Responsibilities

| Component | Input | Output | Responsibility |
|-----------|-------|--------|----------------|
| Input Guardrail | Raw text | RequirementPacket | Validate length, detect PII, block prompt injection |
| Structuring Agent | RequirementPacket | PRD_Draft | Extract user story, AC, dependencies; identify gaps |
| Scoring Agent | PRD_Draft or RequirementPacket | TicketScoreReport | Evaluate quality against rubric |
| Hard Gate | TicketScoreReport | GateDecision | Accept/reject based on score and blockers |

## Configuration

### Environment Variables

See `.env.example` for all available configuration options.

Key settings:
- `OPENROUTER_API_KEY`: Required for LLM calls
- `ENABLE_STRUCTURING`: Toggle structuring agent (default: true)
- `ENABLE_GUARDRAIL`: Toggle input guardrail (default: true)
- `MAX_LLM_RETRIES`: LLM retry attempts (default: 3)

### Configuration Files

| File | Purpose |
|------|---------|
| `config/scoring_rubric.yaml` | Scoring rules and weights |
| `config/guardrail_config.yaml` | Guardrail patterns and limits |
| `prompts/structuring_agent_v1.txt` | Structuring agent prompt template |

## Error Handling

### Error Propagation Strategy

1. **Guardrail Errors**: Fail fast, reject input
2. **Structuring Errors**: Log and fallback to raw mode
3. **Scoring Errors**: Retry with exponential backoff, then fail
4. **Gate Errors**: Should never happen (pure logic)

### Retry Logic

Using `tenacity` for exponential backoff:
- Max attempts: 3 (configurable)
- Initial wait: 2 seconds
- Max wait: 10 seconds
- Exponential multiplier: 1

## Security Considerations

- **PII Detection**: Regex-based detection for emails, phones, credit cards
- **Prompt Injection Defense**: Pattern matching for common injection phrases
- **No PII Logging**: Detected PII values are never logged
