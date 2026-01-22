# Phase 1: Foundation & Scoring Core - Tasks

## Task Overview

Total Tasks: 35 (32 Required + 3 Optional)
Estimated Time: 1 Week

## 1. Project Setup & Infrastructure

### 1.1 Initialize Project Structure
- [x] 1.1.1 Create directory structure according to design
- [x] 1.1.2 Initialize pyproject.toml with dependencies
- [x] 1.1.3 Create .env.example with all required variables
- [x] 1.1.4 Create .gitignore file
- [x] 1.1.5 Create README.md with setup instructions

### 1.2 Setup Development Tools
- [x] 1.2.1 Configure ruff in pyproject.toml
- [x] 1.2.2 Configure mypy in pyproject.toml
- [x] 1.2.3 Configure pytest in pyproject.toml
- [x] 1.2.4 Create pytest.ini or update pyproject.toml with test config

### 1.3 Create Basic Application
- [x] 1.3.1 Implement src/reqgate/app/main.py with FastAPI app
- [x] 1.3.2 Implement src/reqgate/api/routes.py with /health endpoint
- [x] 1.3.3 Create tests/test_health.py to test health endpoint
- [x] 1.3.4 Verify app can start with uvicorn

## 2. Configuration Layer

### 2.1 Implement Settings
- [x] 2.1.1 Create src/reqgate/config/settings.py with Settings class
- [x] 2.1.2 Add all required configuration fields
- [x] 2.1.3 Implement get_settings() singleton function
- [x] 2.1.4 Create tests/test_settings.py to test configuration loading

### 2.2 Setup Logging
- [x] 2.2.1 Create src/reqgate/observability/logging.py
- [x] 2.2.2 Implement structured logging configuration
- [x] 2.2.3 Add log level configuration from settings
- [ ]*2.2.4 Add request ID tracking (optional)

## 3. Schema Layer

### 3.1 Define Input Schemas
- [x] 3.1.1 Create src/reqgate/schemas/__init__.py
- [x] 3.1.2 Create src/reqgate/schemas/inputs.py
- [x] 3.1.3 Implement RequirementPacket schema with all fields
- [x] 3.1.4 Add validators for RequirementPacket
- [x] 3.1.5 Create tests/test_schemas_inputs.py with validation tests

### 3.2 Define Output Schemas
- [x] 3.2.1 Create src/reqgate/schemas/outputs.py
- [x] 3.2.2 Implement ReviewIssue schema
- [x] 3.2.3 Implement TicketScoreReport schema
- [x] 3.2.4 Add examples to schemas
- [x] 3.2.5 Create tests/test_schemas_outputs.py

### 3.3 Define Internal Schemas
- [x] 3.3.1 Create src/reqgate/schemas/internal.py
- [x] 3.3.2 Implement AgentState TypedDict
- [x] 3.3.3 Update schemas/__init__.py to export all schemas

## 4. Rubric Configuration

### 4.1 Create Rubric File
- [x] 4.1.1 Create config/ directory
- [x] 4.1.2 Create config/scoring_rubric.yaml
- [x] 4.1.3 Define FEATURE scenario rules
- [x] 4.1.4 Define BUG scenario rules
- [x] 4.1.5 Add required_fields and negative_patterns

### 4.2 Implement Rubric Loader
- [x] 4.2.1 Create src/reqgate/gates/__init__.py
- [x] 4.2.2 Create src/reqgate/gates/rules.py
- [x] 4.2.3 Implement RubricLoader class
- [x] 4.2.4 Implement get_rubric_loader() singleton
- [x] 4.2.5 Create tests/test_rubric_loader.py

## 5. LLM Infrastructure

### 5.1 Implement LLM Adapter
- [x] 5.1.1 Create src/reqgate/adapters/__init__.py
- [x] 5.1.2 Create src/reqgate/adapters/llm.py
- [x] 5.1.3 Implement LLMClient abstract base class
- [x] 5.1.4 Implement OpenAIClient
- [x] 5.1.5 Implement get_llm_client() singleton
- [x] 5.1.6 Add error handling for timeout and API errors
- [x] 5.1.7 Create tests/test_llm_adapter.py with mocked tests

## 6. Scoring Agent

### 6.1 Implement Scoring Logic
- [x] 6.1.1 Create src/reqgate/agents/__init__.py
- [x] 6.1.2 Create src/reqgate/agents/scoring.py
- [x] 6.1.3 Implement ScoringAgent class
- [x] 6.1.4 Implement score() method
- [x] 6.1.5 Implement _build_prompt() method
- [x] 6.1.6 Create tests/test_scoring_agent.py with mocked LLM

### 6.2 Create Prompt Templates
- [ ]*6.2.1 Create prompts/ directory (optional)
- [ ]*6.2.2 Extract prompt template to separate file (optional)

## 7. Hard Gate

### 7.1 Implement Gate Logic
- [x] 7.1.1 Create src/reqgate/gates/decision.py
- [x] 7.1.2 Implement HardGate class
- [x] 7.1.3 Implement decide() method
- [x] 7.1.4 Add decision logging
- [x] 7.1.5 Create tests/test_hard_gate.py

## 8. Integration & Testing

### 8.1 Integration Tests
- [x] 8.1.1 Create tests/test_integration.py
- [x] 8.1.2 Implement end-to-end test with mocked LLM
- [x] 8.1.3 Test complete flow: Input → Scoring → Gate
- [x]*8.1.4 Add real LLM integration test (optional, requires API key)

### 8.2 Code Quality
- [x] 8.2.1 Run ruff check and fix all issues
- [x] 8.2.2 Run ruff format on all code
- [x] 8.2.3 Run mypy and fix type errors
- [x] 8.2.4 Ensure all tests pass with pytest

### 8.3 Documentation
- [x] 8.3.1 Create docs/architecture.md (placeholder)
- [x] 8.3.2 Create docs/workflow.md (placeholder)
- [x] 8.3.3 Create docs/decisions.md (placeholder)
- [x] 8.3.4 Update README.md with usage examples

## 9. Milestone Verification

### 9.1 Milestone T1: The First Reject
- [x] 9.1.1 Prepare a bad requirement sample (missing AC)
- [x] 9.1.2 Create test script to run complete flow
- [x] 9.1.3 Verify score < 60
- [x] 9.1.4 Verify blocking_issues contains MISSING_AC
- [x] 9.1.5 Verify Hard Gate returns REJECT
- [x] 9.1.6 Document test results

## Task Dependencies

```
1.1 → 1.2 → 1.3
1.3 → 2.1 → 2.2
2.1 → 3.1 → 3.2 → 3.3
2.1 → 4.1 → 4.2
2.1 → 5.1
4.2 + 5.1 → 6.1
6.1 → 7.1
7.1 → 8.1
8.1 → 8.2 → 8.3 → 9.1
```

## Execution Notes

### Priority Order
1. **Critical Path**: 1.1 → 1.3 → 2.1 → 3.1 → 3.2 → 4.1 → 4.2 → 5.1 → 6.1 → 7.1 → 9.1
2. **Testing**: Can be done in parallel with implementation
3. **Documentation**: Can be done at the end

### Estimated Time per Section
- Section 1: 2 hours
- Section 2: 2 hours
- Section 3: 4 hours
- Section 4: 2 hours
- Section 5: 3 hours
- Section 6: 4 hours
- Section 7: 2 hours
- Section 8: 4 hours
- Section 9: 2 hours

**Total: ~25 hours (3-4 days)**

### Testing Strategy
- Write tests immediately after implementing each component
- Use pytest fixtures for common test data
- Mock LLM calls in unit tests
- Use real LLM calls only in optional integration tests

### Code Review Checklist
Before marking Phase 1 complete:
- [ ] All required tasks completed
- [ ] All tests passing
- [ ] Code quality checks passing (ruff, mypy)
- [ ] Documentation updated
- [ ] Milestone T1 verified
- [ ] No hardcoded secrets or API keys
- [ ] All schemas have docstrings
- [ ] Error handling implemented

## Next Steps After Phase 1

Once Phase 1 is complete and Milestone T1 is verified:
1. Review and document lessons learned
2. Create Phase 2 spec (Structuring & Workflow)
3. Plan Phase 2 implementation
