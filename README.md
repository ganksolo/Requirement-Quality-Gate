# ReqGate - Requirement Quality Gate

> 🚀 AI-powered requirement quality assessment for PRD/Tickets

## Overview

ReqGate is a quality gate system that uses AI to automatically evaluate product requirements before they enter technical review. It catches issues early, provides actionable feedback, and improves the overall quality of requirements.

## Current Status

**Phase 1**: Foundation & Scoring Core (In Progress)

- ✅ Project skeleton
- ✅ Core schemas (RequirementPacket, TicketScoreReport)
- ✅ Scoring rubric configuration
- ⏳ Scoring Agent implementation
- ⏳ Hard Gate implementation

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
# Edit .env and add your OPENAI_API_KEY
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
│   ├── agents/        # AI agents
│   ├── gates/         # Quality gate logic
│   ├── adapters/      # External integrations
│   ├── workflow/      # LangGraph workflows
│   └── observability/ # Logging & monitoring
├── tests/             # Test suite
├── config/            # Configuration files
└── docs/              # Documentation
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |

## Configuration

All configuration is via environment variables. See `.env.example` for available options.

## Documentation

- [Architecture](docs/architecture.md)
- [Workflow](docs/workflow.md)
- [Decisions](docs/decisions.md)
- [START_HERE](START_HERE.md) - Project entry point
- [SPEC_GUIDE](SPEC_GUIDE.md) - Spec usage guide

## License

MIT
