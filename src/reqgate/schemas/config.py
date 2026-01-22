"""Configuration schemas for rubric and scoring rules."""

from typing import Literal, TypedDict

from pydantic import BaseModel, Field


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


class WorkflowConfig(BaseModel):
    """
    Configuration for workflow execution.

    This schema defines runtime configuration options for the LangGraph workflow,
    including feature toggles, retry settings, and timeout values.

    Attributes:
        enable_guardrail: Whether to run input guardrail node
        enable_structuring: Whether to run structuring agent node
        enable_fallback: Whether to enable fallback mode on structuring failure
        max_retries: Maximum number of LLM call retries
        llm_timeout: Timeout for LLM calls in seconds
        structuring_timeout: Timeout for structuring agent in seconds
        guardrail_mode: Guardrail strictness level ('strict' or 'lenient')
    """

    enable_guardrail: bool = Field(
        default=True,
        description="Whether to run input guardrail node",
    )

    enable_structuring: bool = Field(
        default=True,
        description="Whether to run structuring agent node",
    )

    enable_fallback: bool = Field(
        default=True,
        description="Whether to enable fallback mode on structuring failure",
    )

    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum number of LLM call retries (0-10)",
    )

    llm_timeout: float = Field(
        default=30.0,
        ge=5.0,
        le=120.0,
        description="Timeout for LLM calls in seconds (5-120)",
    )

    structuring_timeout: float = Field(
        default=20.0,
        ge=5.0,
        le=60.0,
        description="Timeout for structuring agent in seconds (5-60)",
    )

    guardrail_mode: Literal["strict", "lenient"] = Field(
        default="lenient",
        description="Guardrail strictness level: 'strict' rejects on any issue, 'lenient' only rejects blockers",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "enable_guardrail": True,
                "enable_structuring": True,
                "enable_fallback": True,
                "max_retries": 3,
                "llm_timeout": 30.0,
                "structuring_timeout": 20.0,
                "guardrail_mode": "lenient",
            }
        }
    }
