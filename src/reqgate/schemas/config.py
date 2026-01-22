"""Configuration schemas for rubric and scoring rules."""

from typing import TypedDict


class NegativePattern(TypedDict):
    """Negative pattern definition."""

    pattern: str
    severity: str
    message: str


class RequiredField(TypedDict):
    """Required field definition."""

    field: str
    error_msg: str


class RubricScenarioConfig(TypedDict):
    """
    Configuration for a scoring scenario (FEATURE or BUG).

    This TypedDict provides clear typing for rubric configuration,
    replacing the generic dict[str, Any].
    """

    threshold: int
    weights: dict[str, float]
    required_fields: list[RequiredField]
    negative_patterns: list[NegativePattern]
