"""
Scoring rubric loader.

Loads and caches scoring rules from YAML configuration.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from src.reqgate.config.settings import get_settings
from src.reqgate.schemas.config import RubricScenarioConfig


class RubricLoader:
    """Scoring rubric loader and cache."""

    def __init__(self) -> None:
        self._cache: dict[str, Any] | None = None

    def load(self) -> dict[str, Any]:
        """
        Load scoring rubric from YAML file.

        Returns:
            Parsed rubric configuration

        Raises:
            FileNotFoundError: If rubric file doesn't exist
        """
        if self._cache is not None:
            return self._cache

        settings = get_settings()
        rubric_path = Path(settings.rubric_file_path)

        if not rubric_path.exists():
            raise FileNotFoundError(f"Rubric file not found: {rubric_path}")

        with open(rubric_path, encoding="utf-8") as f:
            self._cache = yaml.safe_load(f)

        return self._cache  # type: ignore

    def get_scenario_config(self, ticket_type: str) -> RubricScenarioConfig:
        """
        Get configuration for a specific scenario.

        Args:
            ticket_type: 'Feature' or 'Bug'

        Returns:
            Scenario-specific configuration with typed fields
        """
        rubric = self.load()
        scenario = "BUG" if ticket_type == "Bug" else "FEATURE"

        if scenario not in rubric:
            raise ValueError(f"Unknown scenario: {scenario}")

        return rubric[scenario]


@lru_cache
def get_rubric_loader() -> RubricLoader:
    """Get rubric loader singleton."""
    return RubricLoader()
