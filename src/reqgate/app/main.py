"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from src.reqgate.api.routes import router
from src.reqgate.config.settings import get_settings
from src.reqgate.observability.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    settings = get_settings()
    logger = setup_logging(level=settings.log_level)
    logger.info(f"Starting ReqGate in {settings.reqgate_env} mode")
    logger.info(f"Log level: {settings.log_level}")

    yield

    # Shutdown
    logger.info("Shutting down ReqGate")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI instance
    """
    settings = get_settings()

    app = FastAPI(
        title="ReqGate API",
        description="Requirement Quality Gate - AI-powered PRD quality assessment",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )

    # Include routers
    app.include_router(router)

    return app


# Application instance
app = create_app()
