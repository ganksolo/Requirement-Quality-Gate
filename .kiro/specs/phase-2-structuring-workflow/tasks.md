# Phase 2: Structuring & Workflow Pipeline - Tasks

## Task Overview

Total Tasks: 47 (43 Required + 4 Optional)
Estimated Time: 1 Week

> **Note**: 5 new tasks added for Phase 1 backward compatibility verification (1.1.7, 1.3.5, 4.1.8, 8.1.7, 8.1.8)

## 1. Schema Extensions

### 1.1 Define PRD_Draft Schema
- [x] 1.1.1 Extend src/reqgate/schemas/internal.py with PRD_Draft class (file exists from Phase 1)
- [x] 1.1.2 Add all required fields (title, user_story, acceptance_criteria, etc.)
- [x] 1.1.3 Add validators for title length and format
- [x] 1.1.4 Add validators for user_story format
- [x] 1.1.5 Add example to schema Config
- [x] 1.1.6 Create tests/test_prd_draft_schema.py with validation tests
- [x] 1.1.7 Verify Phase 1 tests still pass after schema extension

### 1.2 Extend AgentState
- [x] 1.2.1 Update AgentState in src/reqgate/schemas/internal.py
- [x] 1.2.2 Add structured_prd field (Optional[PRD_Draft])
- [x] 1.2.3 Add fallback_activated field (bool)
- [x] 1.2.4 Add execution_times field (dict[str, float])
- [x] 1.2.5 Update schemas/__init__.py to export PRD_Draft

### 1.3 Define Workflow Configuration Schema
- [x] 1.3.1 Extend src/reqgate/schemas/config.py with WorkflowConfig class (file exists, contains RubricScenarioConfig)
- [x] 1.3.2 Implement WorkflowConfig class with all configuration fields
- [x] 1.3.3 Add configuration fields (enable_guardrail, max_retries, etc.)
- [x] 1.3.4 Create tests/test_workflow_config.py
- [x] 1.3.5 Update schemas/__init__.py to export WorkflowConfig

## 2. Input Guardrail

### 2.1 Create Guardrail Configuration
- [x] 2.1.1 Create config/guardrail_config.yaml
- [x] 2.1.2 Define length constraints (min_length, max_length)
- [x] 2.1.3 Define PII detection patterns
- [x] 2.1.4 Define prompt injection patterns
- [x] 2.1.5 Add configuration modes (strict/lenient)

### 2.2 Implement Guardrail Logic
- [x] 2.2.1 Create src/reqgate/workflow/__init__.py
- [x] 2.2.2 Create src/reqgate/workflow/nodes/__init__.py
- [x] 2.2.3 Create src/reqgate/workflow/nodes/input_guardrail.py
- [x] 2.2.4 Implement length validation
- [x] 2.2.5 Implement PII detection (regex-based)
- [x] 2.2.6 Implement prompt injection detection
- [x] 2.2.7 Implement guardrail configuration loader
- [x] 2.2.8 Create tests/test_input_guardrail.py

### 2.3 Guardrail Error Handling
- [x] 2.3.1 Define GuardrailRejectionError in src/reqgate/workflow/errors.py
- [x] 2.3.2 Implement error logging
- [x] 2.3.3 Add tests for rejection scenarios

## 3. Structuring Agent

### 3.1 Create Prompt Template
- [x] 3.1.1 Create prompts/ directory
- [x] 3.1.2 Create prompts/structuring_agent_v1.txt
- [x] 3.1.3 Write anti-hallucination instructions
- [x] 3.1.4 Add extraction guidelines
- [x] 3.1.5 Add example output

### 3.2 Implement Structuring Agent
- [x] 3.2.1 Create src/reqgate/workflow/nodes/structuring_agent.py
- [x] 3.2.2 Implement prompt loading and formatting
- [x] 3.2.3 Implement LLM call with PRD_Draft schema
- [x] 3.2.4 Implement output validation
- [x] 3.2.5 Implement anti-hallucination validation
- [x] 3.2.6 Add error handling for LLM failures
- [x] 3.2.7 Create tests/test_structuring_agent.py

### 3.3 Structuring Agent Tests
- [x] 3.3.1 Test extraction from well-formatted text
- [x] 3.3.2 Test extraction from messy meeting transcript
- [x] 3.3.3 Test handling of missing AC
- [x] 3.3.4 Test missing_info detection
- [x] 3.3.5 Test clarification_questions generation
- [x] 3.3.6 Test anti-hallucination (no invented content)

## 4. LLM Retry Logic

### 4.1 Extend LLM Adapter
- [ ] 4.1.1 Check if tenacity is already a dependency, add to pyproject.toml if not
- [ ] 4.1.2 Extend src/reqgate/adapters/llm.py (keep existing LLMClient unchanged)
- [ ] 4.1.3 Implement call_llm_with_retry function
- [ ] 4.1.4 Add exponential backoff configuration
- [ ] 4.1.5 Add timeout handling
- [ ] 4.1.6 Add rate limit handling
- [ ] 4.1.7 Create tests/test_llm_retry.py
- [ ] 4.1.8 Verify Phase 1 LLM tests still pass

### 4.2 Define LLM Error Types
- [ ] 4.2.1 Create LLMTimeoutError in src/reqgate/workflow/errors.py
- [ ] 4.2.2 Create LLMRateLimitError
- [ ] 4.2.3 Add error logging

## 5. LangGraph Workflow

### 5.1 Setup LangGraph
- [ ] 5.1.1 Add langgraph dependency to pyproject.toml
- [ ] 5.1.2 Create src/reqgate/workflow/graph.py
- [ ] 5.1.3 Import StateGraph and END from langgraph

### 5.2 Implement Workflow Nodes
- [ ] 5.2.1 Create input_guardrail_node wrapper
- [ ] 5.2.2 Create structuring_agent_node wrapper
- [ ] 5.2.3 Update scoring_agent_node to handle fallback mode
- [ ] 5.2.4 Create hard_gate_node wrapper
- [ ] 5.2.5 Add execution time tracking to each node

### 5.3 Define Workflow Graph
- [ ] 5.3.1 Implement create_workflow() function
- [ ] 5.3.2 Add all nodes to StateGraph
- [ ] 5.3.3 Define linear edges (guardrail → structuring → scoring → gate)
- [ ] 5.3.4 Implement should_fallback() routing function
- [ ] 5.3.5 Add conditional edge for fallback logic
- [ ] 5.3.6 Compile workflow graph

### 5.4 Workflow Execution
- [ ] 5.4.1 Implement run_workflow() function
- [ ] 5.4.2 Initialize AgentState from RequirementPacket
- [ ] 5.4.3 Execute workflow graph
- [ ] 5.4.4 Handle workflow exceptions
- [ ] 5.4.5 Return final AgentState

## 6. Fallback Mechanism

### 6.1 Implement Fallback Logic
- [ ] 6.1.1 Update scoring_agent_node to detect missing structured_prd
- [ ] 6.1.2 Implement format_prd_for_scoring() helper
- [ ] 6.1.3 Implement fallback mode (use raw_text)
- [ ] 6.1.4 Set fallback_activated flag
- [ ] 6.1.5 Log fallback activation
- [ ] 6.1.6 Apply score penalty for fallback mode

### 6.2 Fallback Tests
- [ ] 6.2.1 Create tests/test_fallback.py
- [ ] 6.2.2 Test fallback activation on structuring failure
- [ ] 6.2.3 Test scoring continues with raw text
- [ ] 6.2.4 Test fallback flag is set correctly
- [ ] 6.2.5 Test score penalty is applied

## 7. Integration & Testing

### 7.1 Workflow Integration Tests
- [ ] 7.1.1 Create tests/test_workflow_integration.py
- [ ] 7.1.2 Test happy path (all nodes succeed)
- [ ] 7.1.3 Test fallback path (structuring fails)
- [ ] 7.1.4 Test retry path (LLM timeout then success)
- [ ] 7.1.5 Test error path (guardrail rejects input)
- [ ] 7.1.6 Verify state transitions
- [ ] 7.1.7 Verify execution times logged

### 7.2 End-to-End Tests
- [ ] 7.2.1 Test with meeting transcript input
- [ ] 7.2.2 Test with well-formatted PRD input
- [ ] 7.2.3 Test with malformed input
- [ ] 7.2.4 Test with PII-containing input
- [ ] 7.2.5 Test with prompt injection attempt

### 7.3 Code Quality
- [ ] 7.3.1 Run ruff check and fix all issues
- [ ] 7.3.2 Run ruff format on all code
- [ ] 7.3.3 Run mypy and fix type errors
- [ ] 7.3.4 Ensure all tests pass with pytest

## 8. Configuration & Documentation

### 8.1 Configuration Updates
- [ ] 8.1.1 Update .env.example with Phase 2 variables
- [ ] 8.1.2 Extend src/reqgate/config/settings.py (keep existing fields unchanged)
- [ ] 8.1.3 Add enable_structuring setting with default True
- [ ] 8.1.4 Add enable_guardrail setting with default True
- [ ] 8.1.5 Add max_llm_retries setting with default 3
- [ ] 8.1.6 Add structuring_timeout setting with default 20
- [ ] 8.1.7 Add guardrail_config_path setting
- [ ] 8.1.8 Verify Phase 1 settings tests still pass

### 8.2 Documentation
- [ ] 8.2.1 Update docs/architecture.md with workflow diagram
- [ ] 8.2.2 Update docs/workflow.md with LangGraph details
- [ ] 8.2.3 Create docs/prompts.md documenting prompt templates
- [ ] 8.2.4 Update README.md with Phase 2 features

## 9. Milestone Verification

### 9.1 Milestone T2: End-to-End Workflow
- [ ] 9.1.1 Prepare meeting transcript sample (300 words)
- [ ] 9.1.2 Create test script to run complete workflow
- [ ] 9.1.3 Verify PRD_Draft is generated
- [ ] 9.1.4 Verify PRD_Draft contains User Story and AC
- [ ] 9.1.5 Verify Scoring Agent uses PRD_Draft
- [ ] 9.1.6 Verify Hard Gate makes correct decision
- [ ] 9.1.7 Verify workflow completes in < 60s
- [ ] 9.1.8 Document test results

### 9.2 Milestone T2.1: Degradation Test
- [ ] 9.2.1 Create test script with mocked structuring failure
- [ ] 9.2.2 Verify workflow doesn't crash
- [ ] 9.2.3 Verify Scoring Agent uses raw text
- [ ] 9.2.4 Verify score penalty applied
- [ ] 9.2.5 Verify error logged
- [ ] 9.2.6 Document test results

## Task Dependencies

```
1.1 → 1.2 → 1.3
1.2 → 2.1 → 2.2 → 2.3
1.2 → 3.1 → 3.2 → 3.3
2.2 → 4.1 → 4.2
3.2 + 4.1 → 5.1 → 5.2 → 5.3 → 5.4
5.4 → 6.1 → 6.2
6.2 → 7.1 → 7.2 → 7.3
7.3 → 8.1 → 8.2 → 9.1 → 9.2
```

## Execution Notes

### Priority Order
1. **Critical Path**: 1.1 → 1.2 → 3.1 → 3.2 → 5.1 → 5.2 → 5.3 → 5.4 → 9.1
2. **Guardrail**: 2.1 → 2.2 → 2.3 (can be done in parallel with Structuring)
3. **Retry Logic**: 4.1 → 4.2 (can be done in parallel)
4. **Testing**: Can be done incrementally with implementation

### Estimated Time per Section
- Section 1 (Schemas): 3 hours
- Section 2 (Guardrail): 4 hours
- Section 3 (Structuring): 6 hours
- Section 4 (Retry): 2 hours
- Section 5 (LangGraph): 5 hours
- Section 6 (Fallback): 3 hours
- Section 7 (Testing): 5 hours
- Section 8 (Config/Docs): 2 hours
- Section 9 (Milestones): 2 hours

**Total: ~32 hours (4-5 days)**

### Testing Strategy
- Write tests immediately after implementing each component
- Use pytest fixtures for common test data
- Mock LLM calls in unit tests
- Use real LLM calls only in integration tests (optional)
- Test fallback scenarios explicitly

### Code Review Checklist
Before marking Phase 2 complete:
- [ ] All required tasks completed
- [ ] All tests passing (including all 82 Phase 1 tests)
- [ ] Code quality checks passing (ruff, mypy)
- [ ] Documentation updated
- [ ] Milestone T2 and T2.1 verified
- [ ] No hardcoded secrets or API keys
- [ ] All schemas have docstrings
- [ ] Error handling implemented
- [ ] Retry logic tested
- [ ] Fallback mechanism tested
- [ ] All Phase 1 APIs unchanged (ScoringAgent.score, HardGate.decide)

## Optional Enhancements

### Optional Tasks
- [ ]*3.2.8 Add confidence scoring to extracted fields
- [ ]*5.4.6 Add workflow visualization/debugging output
- [ ]*7.2.6 Add performance benchmarking tests
- [ ]*8.2.5 Create workflow diagram with mermaid

## Next Steps After Phase 2

Once Phase 2 is complete and Milestones T2/T2.1 are verified:
1. Review and document lessons learned
2. Optimize prompt templates based on test results
3. Create Phase 3 spec (API & Integration)
4. Plan Phase 3 implementation

## Notes

### Key Differences from Phase 1
- Introduces LangGraph for workflow orchestration
- Adds Structuring Agent (new LLM component)
- Implements fallback and retry mechanisms
- More complex state management
- More integration testing required

### Integration with Phase 1
- Reuses all Phase 1 schemas (RequirementPacket, TicketScoreReport)
- Reuses LLM adapter (extends with retry logic)
- Reuses Scoring Agent (updates to handle fallback mode)
- Reuses Hard Gate (no changes needed)
- Reuses configuration system (extends with new settings)

### Common Pitfalls to Avoid
1. **Hallucination**: Ensure Structuring Agent doesn't invent information
2. **State Mutation**: LangGraph nodes should not mutate state in place
3. **Error Swallowing**: Always log errors before fallback
4. **Timeout Handling**: Set reasonable timeouts for LLM calls
5. **Schema Validation**: Always validate LLM outputs against schemas
