"""Application settings module."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application settings
    reqgate_env: Literal["development", "staging", "production"] = "development"
    reqgate_port: int = 8000
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # OpenRouter settings (unified LLM gateway)
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # LLM Model settings
    llm_model: str = "openai/gpt-4o"
    llm_timeout: int = 60
    llm_fallback_models: str = "deepseek/deepseek-chat,google/gemini-2.0-flash-001"

    # Scoring settings
    rubric_file_path: str = "config/scoring_rubric.yaml"
    default_threshold: int = 60

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.reqgate_env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.reqgate_env == "production"

    @property
    def fallback_models_list(self) -> list[str]:
        """Get fallback models as a list."""
        if not self.llm_fallback_models:
            return []
        return [m.strip() for m in self.llm_fallback_models.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

