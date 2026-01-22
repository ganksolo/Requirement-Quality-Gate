# ReqGate - Requirement Quality Gate

> 🚀 AI-powered requirement quality assessment for PRD/Tickets

## Overview

ReqGate is a quality gate system that uses AI to automatically evaluate product requirements before they enter technical review. It catches issues early, provides actionable feedback, and improves the overall quality of requirements.

### Key Features

- **Automatic Structuring**: Convert messy requirement text into standardized PRD format
- **Quality Scoring**: LLM-based evaluation against configurable rubric
- **Hard Gate**: Deterministic pass/reject decisions with blocking issue detection
- **Fallback Mechanism**: Graceful degradation when structuring fails
- **Input Guardrail**: Protection against PII leakage and prompt injection

## Current Status

**Phase 1**: Foundation & Scoring Core ✅ Complete  
**Phase 2**: Structuring & Workflow ✅ Complete

### Phase 2 Features

- ✅ PRD_Draft schema for structured requirements
- ✅ Structuring Agent with anti-hallucination measures
- ✅ Input Guardrail for input validation and security
- ✅ LangGraph workflow orchestration
- ✅ Fallback mechanism for graceful degradation
- ✅ Retry logic with exponential backoff

## Quick Start

### Prerequisites

- Python 3.14+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd Requirement-Quality-Gate

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
uv pip install -e ".[dev]"

# Copy environment file
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

### Running the Server

```bash
# Development mode with auto-reload
uvicorn src.reqgate.app.main:app --reload --port 8000

# Access the API docs at http://localhost:8000/docs
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/reqgate --cov-report=html

# Run specific test file
pytest tests/test_workflow_integration.py -v
```

### Code Quality

```bash
# Lint check
ruff check src/ tests/

# Format code
ruff format src/ tests/

# Type check
mypy src/
```

## Project Structure

```
reqgate/
├── src/reqgate/
│   ├── app/           # FastAPI application
│   ├── api/           # API routes
│   ├── config/        # Configuration management
│   ├── schemas/       # Pydantic models
│   │   ├── inputs.py      # RequirementPacket
│   │   ├── outputs.py     # TicketScoreReport
│   │   ├── internal.py    # PRD_Draft, AgentState
│   │   └── config.py      # WorkflowConfig
│   ├── agents/        # AI agents
│   │   ├── scoring.py     # Scoring Agent
│   │   └── structuring.py # (deprecated, see workflow/)
│   ├── gates/         # Quality gate logic
│   │   ├── rules.py       # Rubric Loader
│   │   └── decision.py    # Hard Gate
│   ├── adapters/      # External integrations
│   │   └── llm.py         # LLM Client with retry
│   ├── workflow/      # LangGraph workflows (Phase 2)
│   │   ├── graph.py       # Workflow definition
│   │   ├── errors.py      # Workflow exceptions
│   │   └── nodes/         # Workflow nodes
│   └── observability/ # Logging & monitoring
├── tests/             # Test suite (276+ tests)
├── config/            # Configuration files
│   ├── scoring_rubric.yaml
│   └── guardrail_config.yaml
├── prompts/           # LLM prompt templates
│   └── structuring_agent_v1.txt
└── docs/              # Documentation
```

## Workflow

ReqGate processes requirements through a multi-stage pipeline:

```
Input Text
    ↓
[Input Guardrail] → Validate length, detect PII, block injection
    ↓
[Structuring Agent] → Convert to structured PRD_Draft
    ↓ (fallback if fails)
[Scoring Agent] → Evaluate quality against rubric
    ↓
[Hard Gate] → Make pass/reject decision
    ↓
Output
```

### Fallback Mode

If the Structuring Agent fails to process input:
1. Error is logged
2. Scoring Agent uses raw text directly
3. Score penalty (-5 points) is applied
4. Workflow continues without interruption

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |

> Note: Full API endpoints will be added in Phase 3.

## Configuration

All configuration is via environment variables. See `.env.example` for available options.

### Key Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | - | Required for LLM calls |
| `LLM_MODEL` | `openai/gpt-4o` | Primary LLM model |
| `ENABLE_STRUCTURING` | `true` | Toggle structuring agent |
| `ENABLE_GUARDRAIL` | `true` | Toggle input guardrail |
| `GUARDRAIL_MODE` | `lenient` | `strict` or `lenient` |
| `MAX_LLM_RETRIES` | `3` | LLM retry attempts |
| `STRUCTURING_TIMEOUT` | `20` | Structuring timeout (seconds) |
| `DEFAULT_THRESHOLD` | `60` | Pass/reject score threshold |

## Documentation

- [Architecture](docs/architecture.md) - System architecture and components
- [Workflow](docs/workflow.md) - LangGraph workflow details
- [Prompts](docs/prompts.md) - Prompt template documentation
- [START_HERE](START_HERE.md) - Project entry point
- [SPEC_GUIDE](SPEC_GUIDE.md) - Spec usage guide

## Development

### Spec-Driven Development

This project follows Spec-Driven Development methodology:

1. Create Spec (`requirements.md`, `design.md`, `tasks.md`)
2. Review and approve Spec
3. Execute tasks from Spec
4. Verify milestone completion

See `.kiro/specs/` for current and completed Specs.

### Core Principles

- **Schema-Driven**: All data flows through Pydantic schemas
- **Type Safety**: All functions have type annotations
- **Test Coverage**: Core modules > 80% coverage
- **Quality Checks**: ruff + mypy must pass

## License

MIT
