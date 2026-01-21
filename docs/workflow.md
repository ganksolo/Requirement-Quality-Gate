# Workflow Documentation

> **Phase 1 Placeholder** - Full workflow documentation will be added in Phase 2 when LangGraph is integrated.

## Current Flow (Phase 1)

```
RequirementPacket
      ↓
[Rubric Loader] → Load Config
      ↓
[Scoring Agent] → Build Prompt → Call LLM → Parse JSON
      ↓
TicketScoreReport
      ↓
[Hard Gate] → Check Blockers → Check Score
      ↓
GateDecision (PASS/REJECT)
```

## Future Flow (Phase 2)

```
Input → Guardrail → Structuring → Scoring → Hard Gate → Output
```

LangGraph will be used to orchestrate the complete workflow with:
- State management
- Error handling
- Retry logic
- Parallel processing
