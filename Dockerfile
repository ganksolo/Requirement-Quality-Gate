# ReqGate Dockerfile
# Multi-stage build for production deployment

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.14-slim AS builder

WORKDIR /app

# Install uv for fast package installation
RUN pip install uv

# Copy dependency files
COPY pyproject.toml .
COPY README.md .

# Create virtual environment and install dependencies
RUN uv venv /app/.venv
RUN . /app/.venv/bin/activate && uv pip install .

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.14-slim AS runtime

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY src/ /app/src/
COPY config/ /app/config/

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV REQGATE_ENV=production

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with uvicorn
CMD ["uvicorn", "src.reqgate.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
