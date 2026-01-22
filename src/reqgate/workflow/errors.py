"""Workflow-specific exceptions and error types."""

from typing import Literal


class WorkflowExecutionError(Exception):
    """Base exception for workflow failures."""

    def __init__(self, message: str, stage: str = "unknown") -> None:
        """
        Initialize workflow execution error.

        Args:
            message: Error message
            stage: Workflow stage where error occurred
        """
        self.stage = stage
        super().__init__(message)


class GuardrailRejectionError(WorkflowExecutionError):
    """
    Input rejected by guardrail.

    Raised when input fails validation checks and cannot proceed.
    """

    def __init__(
        self,
        message: str,
        rejection_reason: Literal[
            "too_short", "too_long", "pii_detected", "prompt_injection", "validation_failed"
        ],
        details: str | None = None,
    ) -> None:
        """
        Initialize guardrail rejection error.

        Args:
            message: Human-readable error message
            rejection_reason: Categorized reason for rejection
            details: Additional details about the rejection
        """
        self.rejection_reason = rejection_reason
        self.details = details
        super().__init__(message, stage="guardrail")


class StructuringFailureError(WorkflowExecutionError):
    """
    Structuring agent failed to produce valid output.

    Raised when the structuring agent cannot extract structured PRD from input.
    """

    def __init__(self, message: str, details: str | None = None) -> None:
        """
        Initialize structuring failure error.

        Args:
            message: Human-readable error message
            details: Additional details about the failure
        """
        self.details = details
        super().__init__(message, stage="structuring")


class LLMTimeoutError(WorkflowExecutionError):
    """
    LLM call timed out after retries.

    Raised when LLM API calls fail due to timeout after exhausting retries.
    """

    def __init__(
        self,
        message: str,
        retry_count: int,
        timeout_seconds: float,
    ) -> None:
        """
        Initialize LLM timeout error.

        Args:
            message: Human-readable error message
            retry_count: Number of retries attempted
            timeout_seconds: Timeout duration per attempt
        """
        self.retry_count = retry_count
        self.timeout_seconds = timeout_seconds
        super().__init__(message, stage="llm_call")


class LLMRateLimitError(WorkflowExecutionError):
    """
    LLM call failed due to rate limiting.

    Raised when LLM API returns rate limit errors after retries.
    """

    def __init__(
        self,
        message: str,
        retry_count: int,
    ) -> None:
        """
        Initialize LLM rate limit error.

        Args:
            message: Human-readable error message
            retry_count: Number of retries attempted
        """
        self.retry_count = retry_count
        super().__init__(message, stage="llm_call")
