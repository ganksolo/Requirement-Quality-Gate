"""Input Guardrail - Validates and sanitizes input before processing."""

import logging
import re
import time
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field
from src.reqgate.schemas.internal import AgentState
from src.reqgate.workflow.errors import GuardrailRejectionError

logger = logging.getLogger(__name__)


class PIIDetectionConfig(BaseModel):
    """Configuration for PII detection."""

    enabled: bool = True
    mode: Literal["strict", "lenient"] = "lenient"
    patterns: dict[str, bool] = Field(
        default_factory=lambda: {
            "email": True,
            "phone": True,
            "credit_card": False,
            "ssn": False,
        }
    )


class PromptInjectionConfig(BaseModel):
    """Configuration for prompt injection detection."""

    enabled: bool = True
    action: Literal["reject", "sanitize", "warn"] = "reject"
    patterns: list[str] = Field(
        default_factory=lambda: [
            "ignore previous instructions",
            "ignore all previous",
            "disregard all previous",
            "forget everything",
            "you are now",
            "act as",
            "pretend to be",
            "system prompt",
            "reveal your instructions",
        ]
    )


class GuardrailConfig(BaseModel):
    """
    Configuration for input guardrail.

    Loaded from config/guardrail_config.yaml or created with defaults.
    """

    min_length: int = Field(default=50, ge=1, description="Minimum input text length")
    max_length: int = Field(default=10000, le=100000, description="Maximum input text length")
    pii_detection: PIIDetectionConfig = Field(default_factory=PIIDetectionConfig)
    prompt_injection: PromptInjectionConfig = Field(default_factory=PromptInjectionConfig)
    default_mode: Literal["strict", "lenient"] = "lenient"


class GuardrailResult(BaseModel):
    """Result of guardrail validation."""

    passed: bool
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    sanitized_text: str | None = None
    pii_detected: list[str] = Field(default_factory=list)
    injection_detected: list[str] = Field(default_factory=list)


# Regex patterns for PII detection
PII_PATTERNS = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone": r"\b(?:\+?1[-.\s]?)?(?:\(?[0-9]{3}\)?[-.\s]?)?[0-9]{3}[-.\s]?[0-9]{4}\b",
    "credit_card": r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b",
    "ssn": r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b",
}


class InputGuardrail:
    """
    Input validation and sanitization guardrail.

    Validates input text for:
    - Length constraints
    - PII (Personally Identifiable Information)
    - Prompt injection attacks
    """

    def __init__(self, config: GuardrailConfig | None = None) -> None:
        """
        Initialize the guardrail.

        Args:
            config: Guardrail configuration. If None, loads from default config file.
        """
        self.config = config or self._load_default_config()

    def _load_default_config(self) -> GuardrailConfig:
        """Load configuration from default YAML file."""
        config_path = Path("config/guardrail_config.yaml")
        if config_path.exists():
            return load_guardrail_config(config_path)
        logger.warning("Guardrail config not found, using defaults")
        return GuardrailConfig()

    def validate(
        self, text: str, mode: Literal["strict", "lenient"] | None = None
    ) -> GuardrailResult:
        """
        Validate input text against guardrail rules.

        Args:
            text: Input text to validate
            mode: Validation mode override (uses config default if None)

        Returns:
            GuardrailResult with validation results
        """
        effective_mode = mode or self.config.default_mode
        result = GuardrailResult(passed=True, sanitized_text=text)

        # 1. Length validation
        self._validate_length(text, result)

        # 2. PII detection
        if self.config.pii_detection.enabled:
            self._detect_pii(text, result, effective_mode)

        # 3. Prompt injection detection
        if self.config.prompt_injection.enabled:
            self._detect_injection(text, result)

        return result

    def _validate_length(self, text: str, result: GuardrailResult) -> None:
        """Validate text length constraints."""
        text_length = len(text.strip())

        if text_length < self.config.min_length:
            result.passed = False
            result.errors.append(
                f"Input too short: {text_length} characters (minimum: {self.config.min_length})"
            )

        if text_length > self.config.max_length:
            result.passed = False
            result.errors.append(
                f"Input too long: {text_length} characters (maximum: {self.config.max_length})"
            )

    def _detect_pii(
        self, text: str, result: GuardrailResult, mode: Literal["strict", "lenient"]
    ) -> None:
        """Detect PII in text."""
        pii_config = self.config.pii_detection

        for pii_type, enabled in pii_config.patterns.items():
            if not enabled:
                continue

            pattern = PII_PATTERNS.get(pii_type)
            if not pattern:
                continue

            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Mask the actual values for logging
                masked = [self._mask_pii(m) for m in matches]
                result.pii_detected.append(f"{pii_type}: {len(matches)} found")

                if mode == "strict" or pii_config.mode == "strict":
                    result.passed = False
                    result.errors.append(f"PII detected ({pii_type}): {masked}")
                else:
                    result.warnings.append(f"PII detected ({pii_type}): {masked}")

    def _mask_pii(self, value: str) -> str:
        """Mask PII value for safe logging."""
        if len(value) <= 4:
            return "****"
        return value[:2] + "*" * (len(value) - 4) + value[-2:]

    def _detect_injection(self, text: str, result: GuardrailResult) -> None:
        """Detect prompt injection patterns."""
        injection_config = self.config.prompt_injection
        text_lower = text.lower()

        detected_patterns = []
        for pattern in injection_config.patterns:
            if pattern.lower() in text_lower:
                detected_patterns.append(pattern)

        if detected_patterns:
            result.injection_detected = detected_patterns

            if injection_config.action == "reject":
                result.passed = False
                result.errors.append(f"Prompt injection detected: {detected_patterns}")
            elif injection_config.action == "warn":
                result.warnings.append(f"Potential prompt injection: {detected_patterns}")
            elif injection_config.action == "sanitize":
                # Remove injection patterns from text
                sanitized = text
                for pattern in detected_patterns:
                    sanitized = re.sub(
                        re.escape(pattern), "[REMOVED]", sanitized, flags=re.IGNORECASE
                    )
                result.sanitized_text = sanitized
                result.warnings.append(f"Sanitized prompt injection patterns: {detected_patterns}")


def load_guardrail_config(config_path: Path | str) -> GuardrailConfig:
    """
    Load guardrail configuration from YAML file.

    Args:
        config_path: Path to the configuration file

    Returns:
        GuardrailConfig instance
    """
    path = Path(config_path)
    if not path.exists():
        logger.warning(f"Config file not found: {path}, using defaults")
        return GuardrailConfig()

    with open(path) as f:
        data = yaml.safe_load(f)

    guardrail_data = data.get("input_guardrail", {})

    # Parse nested configs
    pii_data = guardrail_data.get("pii_detection", {})
    injection_data = guardrail_data.get("prompt_injection", {})

    return GuardrailConfig(
        min_length=guardrail_data.get("min_length", 50),
        max_length=guardrail_data.get("max_length", 10000),
        pii_detection=PIIDetectionConfig(**pii_data) if pii_data else PIIDetectionConfig(),
        prompt_injection=PromptInjectionConfig(**injection_data)
        if injection_data
        else PromptInjectionConfig(),
        default_mode=guardrail_data.get("default_mode", "lenient"),
    )


@lru_cache(maxsize=1)
def get_guardrail() -> InputGuardrail:
    """
    Get singleton InputGuardrail instance.

    Returns:
        Cached InputGuardrail instance
    """
    return InputGuardrail()


def input_guardrail_node(state: AgentState) -> AgentState:
    """
    LangGraph node for input guardrail.

    Validates and sanitizes input before processing.

    Args:
        state: Current workflow state

    Returns:
        Updated state with validation results

    Raises:
        GuardrailRejectionError: If input fails validation
    """
    start_time = time.time()
    guardrail = get_guardrail()

    # Get input text from packet
    raw_text = state["packet"].raw_text

    # Validate input
    result = guardrail.validate(raw_text)

    # Log warnings
    for warning in result.warnings:
        logger.warning(f"Guardrail warning: {warning}")

    # Update execution times
    execution_times = dict(state.get("execution_times", {}))
    execution_times["guardrail"] = time.time() - start_time

    # Handle validation failure
    if not result.passed:
        error_msg = "; ".join(result.errors)
        logger.error(f"Guardrail rejected input: {error_msg}")

        # Determine rejection reason
        if any("too short" in e for e in result.errors):
            reason = "too_short"
        elif any("too long" in e for e in result.errors):
            reason = "too_long"
        elif result.pii_detected:
            reason = "pii_detected"
        elif result.injection_detected:
            reason = "prompt_injection"
        else:
            reason = "validation_failed"

        # Log error to state
        error_logs = list(state.get("error_logs", []))
        error_logs.append(f"Guardrail: {error_msg}")

        raise GuardrailRejectionError(
            message=f"Input validation failed: {error_msg}",
            rejection_reason=reason,
            details=error_msg,
        )

    # Update state
    return {
        **state,
        "current_stage": "guardrail_passed",
        "execution_times": execution_times,
    }
