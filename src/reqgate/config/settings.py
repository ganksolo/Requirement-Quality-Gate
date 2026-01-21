"""Application settings loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration.

    All settings are loaded from environment variables.
    Use .env file for local development.
    """

    # Application
    reqgate_env: Literal["development", "staging", "production"] = "development"
    reqgate_port: int = 8000
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # OpenAI LLM
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_timeout: int = 30

    # Gemini LLM (optional)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-pro"

    # Scoring
    rubric_file_path: str = "config/scoring_rubric.yaml"
    default_threshold: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.reqgate_env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.reqgate_env == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Get application settings singleton.

    Uses lru_cache for singleton behavior.
    """
    return Settings()
