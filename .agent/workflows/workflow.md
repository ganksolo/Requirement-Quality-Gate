---
description: ReqGate Spec-Driven Development Workflow - 标准任务执行流程
---

# ReqGate Development Workflow

## 🎯 Workflow Overview

This workflow defines the standard process for executing tasks in the ReqGate project using Spec-Driven Development methodology.

## 📋 Prerequisites

Before starting any task:
1. Read `START_HERE.md` (project entry point)
2. Read `.kiro/PROJECT_OVERVIEW.md` (project overview)
3. Read `.kiro/steering/ai-assistant-guide.md` (detailed guide)

## 🔄 Standard Workflow

### Phase 1: Understand

```
Step 1: Read Requirements
├─ File: .kiro/specs/phase-1-foundation-scoring/requirements.md
├─ Goal: Understand user stories and acceptance criteria
└─ Output: Clear understanding of what needs to be built

Step 2: Read Design
├─ File: .kiro/specs/phase-1-foundation-scoring/design.md
├─ Goal: Understand architecture and implementation approach
└─ Output: Clear understanding of how to build it

Step 3: Identify Task
├─ File: .kiro/specs/phase-1-foundation-scoring/tasks.md
├─ Goal: Find the next uncompleted task [ ]
└─ Output: Specific task to implement
```

### Phase 2: Implement

```
Step 4: Write Code
├─ Follow: Schema-Driven principles (Pydantic only, no dict)
├─ Follow: Type Safety (all functions must have type annotations)
├─ Follow: Design document specifications
└─ Output: Implementation code

Step 5: Write Tests
├─ Create: Unit tests for the implemented functionality
├─ Follow: Test naming convention (test_*.py)
├─ Ensure: Test coverage for core logic
└─ Output: Test code
```

### Phase 3: Verify

```
Step 6: Run Tests
├─ Command: pytest tests/ -v
├─ Command: ruff check src/ tests/
├─ Command: mypy src/
└─ Output: All tests pass, no lint/type errors

Step 7: Update Status
├─ Action: Mark task as complete [x] in tasks.md
├─ Action: Commit changes with proper message
└─ Output: Updated task status
```

### Phase 4: Report

```
Step 8: Report Progress
├─ Report: What was implemented
├─ Report: Test results
├─ Report: Next suggested task
└─ Output: Progress summary for user
```

## 🎮 Execution Modes

### Mode 1: Single Task (Recommended)

```yaml
process:
  - find_next_task: "[ ]"
  - implement_task: true
  - run_tests: true
  - mark_complete: "[x]"
  - stop_and_wait: true  # Wait for user review
```

**Use when**: Working on complex tasks or need careful review

### Mode 2: Batch Execution

```yaml
process:
  - mark_all_queued: "[~]"
  - for_each_task:
      - implement: true
      - test: true
      - mark_complete: "[x]"
      - continue_if: "no_errors"
  - stop_on_error: true
  - report_progress: true
```

**Use when**: Executing multiple simple tasks in sequence

## 🚨 Decision Points

### When to Stop and Ask User

```yaml
stop_conditions:
  - spec_unclear: "Requirements or design is ambiguous"
  - test_failure: "Test fails 3 consecutive times"
  - architecture_change: "Need to modify core architecture"
  - missing_credentials: "Need API keys or sensitive data"
```

### Error Handling

```yaml
on_error:
  - log_error: true
  - attempt_fix: max_3_times
  - if_still_fails:
      - report_to_user: true
      - provide_context: "error message, attempts made"
      - ask_for_guidance: true
```

## 📏 Quality Gates

### Code Quality Checks

```yaml
quality_checks:
  - ruff_check: "ruff check src/ tests/"
  - ruff_format: "ruff format src/ tests/"
  - type_check: "mypy src/"
  - test_run: "pytest tests/ -v"
  - coverage: "pytest tests/ --cov=src/reqgate"
```

### Acceptance Criteria

```yaml
task_complete_when:
  - code_matches_design: true
  - all_tests_pass: true
  - quality_checks_pass: true
  - task_status_updated: true
  - documentation_updated: true
```

## 🎯 Current Phase Context

### Phase 1: Foundation & Scoring Core

```yaml
phase: 1
status: "In Progress"
spec_location: ".kiro/specs/phase-1-foundation-scoring/"
total_tasks: 35
required_tasks: 32
optional_tasks: 3

key_components:
  - RequirementPacket: "Input Schema"
  - TicketScoreReport: "Output Schema"
  - ScoringAgent: "LLM-based scoring"
  - HardGate: "Decision logic"
  - RubricLoader: "YAML configuration"

not_included:
  - StructuringAgent: "Phase 2"
  - LangGraphWorkflow: "Phase 2"
  - FastAPIRoutes: "Phase 3 (except /health)"
  - JiraIntegration: "Phase 3"
```

## 📝 Code Templates

### Schema Definition Template

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional

class MySchema(BaseModel):
    """Schema description"""
    required_field: str = Field(..., description="Field description")
    optional_field: Optional[str] = None
    
    class Config:
        json_schema_extra = {"example": {"required_field": "value"}}
```

### Function Definition Template

```python
def my_function(input: InputSchema) -> OutputSchema:
    """
    Function description
    
    Args:
        input: Input description
    
    Returns:
        Output description
    """
    return OutputSchema(...)
```

### Test Definition Template

```python
def test_my_function_valid():
    """Test valid input"""
    result = my_function(InputSchema(...))
    assert result.field == expected_value

def test_my_function_invalid():
    """Test invalid input"""
    with pytest.raises(ValidationError):
        my_function(InputSchema(invalid_data))
```

## 🔧 Quick Commands

```bash
# Development
uvicorn src.reqgate.app.main:app --reload --port 8000

# Testing
pytest tests/ -v
pytest tests/test_schemas.py -v
pytest tests/ --cov=src/reqgate

# Code Quality
ruff check src/ tests/
ruff format src/ tests/
mypy src/
```

## 📊 Progress Reporting Template

### On Success

```markdown
✅ Task X.X Completed

**Implementation**:
- [What was implemented]

**Tests**:
- [Test results]

**Next**:
- [Suggested next task]
```

### On Error

```markdown
❌ Task X.X Failed

**Error**:
[Error message]

**Attempts**:
1. [Attempt 1]
2. [Attempt 2]

**Need Help**:
[What help is needed]
```

## 🎓 Core Principles

```yaml
principles:
  - spec_first: "Always read spec before coding"
  - schema_driven: "Use Pydantic, never dict"
  - type_safety: "All functions must have type annotations"
  - test_everything: "Core logic must have tests"
  - quality_over_speed: "Correct code is more important than fast code"
```

## 🔗 Related Documents

```yaml
documentation:
  entry_point: "START_HERE.md"
  project_overview: ".kiro/PROJECT_OVERVIEW.md"
  spec_guide: "SPEC_GUIDE.md"
  detailed_guide: ".kiro/steering/ai-assistant-guide.md"
  
workflow_rules:
  development: ".kiro/steering/development-workflow.md"
  schema_rules: ".kiro/steering/schema-driven-rules.md"
  phase_guide: ".kiro/steering/phase-execution-guide.md"

current_spec:
  requirements: ".kiro/specs/phase-1-foundation-scoring/requirements.md"
  design: ".kiro/specs/phase-1-foundation-scoring/design.md"
  tasks: ".kiro/specs/phase-1-foundation-scoring/tasks.md"
```

---

**Version**: 1.0  
**Last Updated**: 2025-01-21  
**Current Phase**: Phase 1 (Foundation & Scoring Core)  
**Status**: Active
