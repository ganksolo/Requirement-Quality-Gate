# Architecture Overview

> **Phase 1 Placeholder** - Detailed architecture documentation will be added as the system evolves.

## System Architecture

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
│         Business Logic Layer            │
│  (Scoring Agent + Hard Gate)            │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Infrastructure Layer            │
│  (LLM Adapter + Config Loader)          │
└─────────────────────────────────────────┘
```

## Key Components

- **FastAPI App**: HTTP interface with health check
- **Settings**: Environment-based configuration
- **Schemas**: Pydantic models for data contracts
- **Scoring Agent**: LLM-based requirement evaluation
- **Hard Gate**: Deterministic pass/reject logic
- **LLM Adapter**: OpenAI/Gemini integration
