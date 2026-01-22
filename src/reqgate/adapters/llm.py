"""
LLM adapter for calling language models via OpenRouter.

Provides abstraction over different LLM providers through OpenRouter's unified API.
Includes retry logic with exponential backoff for handling transient failures.
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TypeVar

from openai import OpenAI
from pydantic import BaseModel
from src.reqgate.config.settings import get_settings
from src.reqgate.workflow.errors import LLMRateLimitError, LLMTimeoutError
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger("reqgate.llm")

T = TypeVar("T")


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def invoke(self, prompt: str, response_schema: type[BaseModel]) -> str:
        """
        Invoke LLM and return JSON string.

        Args:
            prompt: The prompt to send
            response_schema: Expected response schema

        Returns:
            JSON string response
        """
        pass


class OpenRouterClient(LLMClient):
    """OpenRouter client implementation supporting multiple LLM providers."""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.openrouter_api_key
        self.base_url = settings.openrouter_base_url
        self.model = settings.llm_model
        self.timeout = settings.llm_timeout
        self.fallback_models = settings.fallback_models_list
        self._client: OpenAI | None = None

    def _get_client(self) -> OpenAI:
        """Lazy load the OpenAI-compatible client for OpenRouter."""
        if self._client is None:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        return self._client

    def invoke(self, prompt: str, _response_schema: type[BaseModel]) -> str:
        """
        Call OpenRouter API with fallback support.

        Args:
            prompt: The prompt to send
            _response_schema: Expected response schema for structured output

        Returns:
            JSON string response

        Raises:
            TimeoutError: On API timeout
            RuntimeError: On API error after all fallbacks exhausted
        """
        models_to_try = [self.model] + self.fallback_models
        last_error: Exception | None = None

        for model in models_to_try:
            try:
                logger.info(f"Calling LLM model: {model}")
                return self._call_model(model, prompt)
            except TimeoutError:
                logger.warning(f"Timeout with model {model}, trying fallback...")
                last_error = TimeoutError(f"LLM request timeout: {model}")
            except RuntimeError as e:
                logger.warning(f"Error with model {model}: {e}, trying fallback...")
                last_error = e

        raise last_error or RuntimeError("All LLM models failed")

    def _call_model(self, model: str, prompt: str) -> str:
        """Call a specific model."""
        import openai

        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a technical requirement reviewer. Always respond in valid JSON format.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                timeout=self.timeout,
                extra_headers={
                    "HTTP-Referer": "https://reqgate.dev",
                    "X-Title": "ReqGate",
                },
            )

            return response.choices[0].message.content or "{}"

        except openai.APITimeoutError as e:
            raise TimeoutError(f"LLM request timeout: {e}") from e
        except openai.APIError as e:
            raise RuntimeError(f"LLM API error: {e}") from e


# Backwards compatibility alias
OpenAIClient = OpenRouterClient

_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Get LLM client singleton."""
    global _llm_client
    if _llm_client is None:
        _llm_client = OpenRouterClient()
    return _llm_client


# ============================================
# Retry Logic (Phase 2)
# ============================================


class RetryableError(Exception):
    """Base exception for errors that should trigger retry."""

    pass


class RetryableTimeoutError(RetryableError):
    """Timeout error that should trigger retry."""

    pass


class RetryableRateLimitError(RetryableError):
    """Rate limit error that should trigger retry."""

    pass


def create_retry_decorator(
    max_retries: int = 3,
    min_wait: float = 2.0,
    max_wait: float = 10.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Create a retry decorator with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        min_wait: Minimum wait time between retries (seconds)
        max_wait: Maximum wait time between retries (seconds)

    Returns:
        Configured retry decorator
    """
    return retry(
        stop=stop_after_attempt(max_retries + 1),  # +1 because first attempt counts
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(RetryableError),
        reraise=True,
    )


def call_llm_with_retry(
    prompt: str,
    max_retries: int = 3,
    timeout: float = 30.0,
    client: LLMClient | None = None,
) -> str:
    """
    Call LLM with exponential backoff retry.

    This function wraps LLM calls with automatic retry logic for handling
    transient failures like timeouts and rate limits.

    Args:
        prompt: Input prompt to send to LLM
        max_retries: Maximum number of retry attempts (default: 3)
        timeout: Timeout per attempt in seconds (default: 30.0)
        client: Optional LLM client (uses singleton if None)

    Returns:
        LLM response text

    Raises:
        LLMTimeoutError: If all retries exhausted due to timeout
        LLMRateLimitError: If rate limited after retries
        RuntimeError: For other unrecoverable errors
    """
    llm_client = client or get_llm_client()
    retry_count = 0

    @create_retry_decorator(max_retries=max_retries)
    def _call_with_retry() -> str:
        nonlocal retry_count
        try:
            # Use a dummy schema since generate doesn't use it
            from src.reqgate.schemas.outputs import TicketScoreReport

            return llm_client.invoke(prompt, TicketScoreReport)
        except TimeoutError as e:
            retry_count += 1
            logger.warning(f"LLM timeout (attempt {retry_count}/{max_retries + 1}): {e}")
            raise RetryableTimeoutError(str(e)) from e
        except RuntimeError as e:
            error_msg = str(e).lower()
            if "rate" in error_msg and "limit" in error_msg:
                retry_count += 1
                logger.warning(f"LLM rate limit (attempt {retry_count}/{max_retries + 1}): {e}")
                raise RetryableRateLimitError(str(e)) from e
            # Non-retryable error
            raise

    try:
        return _call_with_retry()
    except RetryError as e:
        # All retries exhausted
        original_error = e.last_attempt.exception()
        if isinstance(original_error, RetryableTimeoutError):
            raise LLMTimeoutError(
                message=f"LLM call timed out after {retry_count} retries",
                retry_count=retry_count,
                timeout_seconds=timeout,
            ) from original_error
        elif isinstance(original_error, RetryableRateLimitError):
            raise LLMRateLimitError(
                message=f"LLM rate limited after {retry_count} retries",
                retry_count=retry_count,
            ) from original_error
        raise
    except RetryableTimeoutError as e:
        # Single attempt timeout (shouldn't happen with retry decorator)
        raise LLMTimeoutError(
            message=f"LLM call timed out: {e}",
            retry_count=retry_count,
            timeout_seconds=timeout,
        ) from e
    except RetryableRateLimitError as e:
        raise LLMRateLimitError(
            message=f"LLM rate limited: {e}",
            retry_count=retry_count,
        ) from e


class LLMClientWithRetry:
    """
    LLM client wrapper with built-in retry logic.

    Wraps an existing LLM client and adds automatic retry with
    exponential backoff for transient failures.
    """

    def __init__(
        self,
        client: LLMClient | None = None,
        max_retries: int = 3,
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize the retry-enabled client.

        Args:
            client: Underlying LLM client (uses singleton if None)
            max_retries: Maximum retry attempts
            timeout: Timeout per attempt in seconds
        """
        self.client = client or get_llm_client()
        self.max_retries = max_retries
        self.timeout = timeout

    def generate(self, prompt: str) -> str:
        """
        Generate response with retry logic.

        Args:
            prompt: Input prompt

        Returns:
            LLM response text

        Raises:
            LLMTimeoutError: If all retries exhausted due to timeout
            LLMRateLimitError: If rate limited after retries
        """
        return call_llm_with_retry(
            prompt=prompt,
            max_retries=self.max_retries,
            timeout=self.timeout,
            client=self.client,
        )
