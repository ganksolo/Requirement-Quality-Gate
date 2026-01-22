"""Tests for LLM retry logic."""

from unittest.mock import MagicMock, patch

import pytest
from src.reqgate.adapters.llm import (
    LLMClientWithRetry,
    RetryableRateLimitError,
    RetryableTimeoutError,
    call_llm_with_retry,
    create_retry_decorator,
)
from src.reqgate.workflow.errors import LLMRateLimitError, LLMTimeoutError


class TestRetryableErrors:
    """Tests for retryable error classes."""

    def test_retryable_timeout_error(self) -> None:
        """Test RetryableTimeoutError creation."""
        error = RetryableTimeoutError("Connection timeout")
        assert str(error) == "Connection timeout"

    def test_retryable_rate_limit_error(self) -> None:
        """Test RetryableRateLimitError creation."""
        error = RetryableRateLimitError("Rate limit exceeded")
        assert str(error) == "Rate limit exceeded"


class TestCreateRetryDecorator:
    """Tests for retry decorator factory."""

    def test_decorator_with_defaults(self) -> None:
        """Test decorator creation with default values."""
        decorator = create_retry_decorator()
        assert decorator is not None

    def test_decorator_with_custom_values(self) -> None:
        """Test decorator creation with custom values."""
        decorator = create_retry_decorator(
            max_retries=5,
            min_wait=1.0,
            max_wait=30.0,
        )
        assert decorator is not None

    def test_decorator_retries_on_retryable_error(self) -> None:
        """Test that decorator retries on retryable errors."""
        call_count = 0

        @create_retry_decorator(max_retries=2, min_wait=0.01, max_wait=0.02)
        def failing_function() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RetryableTimeoutError("Timeout")
            return "success"

        result = failing_function()
        assert result == "success"
        assert call_count == 3  # 1 initial + 2 retries

    def test_decorator_does_not_retry_regular_exception(self) -> None:
        """Test that decorator does not retry non-retryable errors."""
        call_count = 0

        @create_retry_decorator(max_retries=3, min_wait=0.01, max_wait=0.02)
        def failing_function() -> str:
            nonlocal call_count
            call_count += 1
            raise ValueError("Non-retryable error")

        with pytest.raises(ValueError, match="Non-retryable error"):
            failing_function()
        assert call_count == 1  # No retries


class TestCallLLMWithRetry:
    """Tests for call_llm_with_retry function."""

    def test_successful_call_no_retry(self) -> None:
        """Test successful LLM call without retry."""
        mock_client = MagicMock()
        mock_client.invoke.return_value = '{"result": "success"}'

        result = call_llm_with_retry(
            prompt="Test prompt",
            max_retries=3,
            client=mock_client,
        )

        assert result == '{"result": "success"}'
        assert mock_client.invoke.call_count == 1

    def test_retry_on_timeout(self) -> None:
        """Test retry behavior on timeout errors."""
        mock_client = MagicMock()
        # First call times out, second succeeds
        mock_client.invoke.side_effect = [
            TimeoutError("Connection timeout"),
            '{"result": "success"}',
        ]

        result = call_llm_with_retry(
            prompt="Test prompt",
            max_retries=3,
            client=mock_client,
        )

        assert result == '{"result": "success"}'
        assert mock_client.invoke.call_count == 2

    def test_timeout_exhausts_retries(self) -> None:
        """Test that persistent timeout exhausts retries and raises."""
        mock_client = MagicMock()
        mock_client.invoke.side_effect = TimeoutError("Persistent timeout")

        with pytest.raises(LLMTimeoutError) as exc_info:
            call_llm_with_retry(
                prompt="Test prompt",
                max_retries=2,
                timeout=30.0,
                client=mock_client,
            )

        error = exc_info.value
        assert "timed out" in str(error).lower()
        assert error.retry_count == 3  # 1 initial + 2 retries
        assert error.timeout_seconds == 30.0

    def test_retry_on_rate_limit(self) -> None:
        """Test retry behavior on rate limit errors."""
        mock_client = MagicMock()
        # First call rate limited, second succeeds
        mock_client.invoke.side_effect = [
            RuntimeError("Rate limit exceeded"),
            '{"result": "success"}',
        ]

        result = call_llm_with_retry(
            prompt="Test prompt",
            max_retries=3,
            client=mock_client,
        )

        assert result == '{"result": "success"}'
        assert mock_client.invoke.call_count == 2

    def test_rate_limit_exhausts_retries(self) -> None:
        """Test that persistent rate limit exhausts retries."""
        mock_client = MagicMock()
        mock_client.invoke.side_effect = RuntimeError("API rate limit reached")

        with pytest.raises(LLMRateLimitError) as exc_info:
            call_llm_with_retry(
                prompt="Test prompt",
                max_retries=2,
                client=mock_client,
            )

        error = exc_info.value
        assert "rate" in str(error).lower()
        assert error.retry_count == 3  # 1 initial + 2 retries

    def test_non_retryable_error_raises_immediately(self) -> None:
        """Test that non-retryable errors raise without retry."""
        mock_client = MagicMock()
        mock_client.invoke.side_effect = RuntimeError("Invalid API key")

        with pytest.raises(RuntimeError, match="Invalid API key"):
            call_llm_with_retry(
                prompt="Test prompt",
                max_retries=3,
                client=mock_client,
            )

        # Should not retry for non-rate-limit errors
        assert mock_client.invoke.call_count == 1

    @patch("src.reqgate.adapters.llm.get_llm_client")
    def test_uses_singleton_when_no_client_provided(self, mock_get_llm: MagicMock) -> None:
        """Test that singleton client is used when none provided."""
        mock_client = MagicMock()
        mock_client.invoke.return_value = '{"result": "ok"}'
        mock_get_llm.return_value = mock_client

        result = call_llm_with_retry(prompt="Test")

        assert result == '{"result": "ok"}'
        mock_get_llm.assert_called_once()

    def test_multiple_timeouts_then_success(self) -> None:
        """Test recovery after multiple timeouts."""
        mock_client = MagicMock()
        mock_client.invoke.side_effect = [
            TimeoutError("Timeout 1"),
            TimeoutError("Timeout 2"),
            '{"status": "recovered"}',
        ]

        result = call_llm_with_retry(
            prompt="Test prompt",
            max_retries=3,
            client=mock_client,
        )

        assert result == '{"status": "recovered"}'
        assert mock_client.invoke.call_count == 3


class TestLLMClientWithRetry:
    """Tests for LLMClientWithRetry wrapper class."""

    def test_init_with_defaults(self) -> None:
        """Test initialization with default values."""
        mock_client = MagicMock()
        wrapper = LLMClientWithRetry(client=mock_client)

        assert wrapper.client is mock_client
        assert wrapper.max_retries == 3
        assert wrapper.timeout == 30.0

    def test_init_with_custom_values(self) -> None:
        """Test initialization with custom values."""
        mock_client = MagicMock()
        wrapper = LLMClientWithRetry(
            client=mock_client,
            max_retries=5,
            timeout=60.0,
        )

        assert wrapper.max_retries == 5
        assert wrapper.timeout == 60.0

    @patch("src.reqgate.adapters.llm.get_llm_client")
    def test_init_uses_singleton_when_no_client(self, mock_get_llm: MagicMock) -> None:
        """Test that singleton is used when no client provided."""
        mock_client = MagicMock()
        mock_get_llm.return_value = mock_client

        wrapper = LLMClientWithRetry()

        assert wrapper.client is mock_client
        mock_get_llm.assert_called_once()

    def test_generate_success(self) -> None:
        """Test successful generation."""
        mock_client = MagicMock()
        mock_client.invoke.return_value = '{"output": "test"}'
        wrapper = LLMClientWithRetry(client=mock_client)

        result = wrapper.generate("Test prompt")

        assert result == '{"output": "test"}'

    def test_generate_with_retry(self) -> None:
        """Test generation with retry on transient failure."""
        mock_client = MagicMock()
        mock_client.invoke.side_effect = [
            TimeoutError("Timeout"),
            '{"output": "success"}',
        ]
        wrapper = LLMClientWithRetry(client=mock_client, max_retries=2)

        result = wrapper.generate("Test prompt")

        assert result == '{"output": "success"}'
        assert mock_client.invoke.call_count == 2

    def test_generate_raises_timeout_error(self) -> None:
        """Test that generate raises LLMTimeoutError on exhausted retries."""
        mock_client = MagicMock()
        mock_client.invoke.side_effect = TimeoutError("Persistent timeout")
        wrapper = LLMClientWithRetry(client=mock_client, max_retries=1)

        with pytest.raises(LLMTimeoutError):
            wrapper.generate("Test prompt")

    def test_generate_raises_rate_limit_error(self) -> None:
        """Test that generate raises LLMRateLimitError on rate limiting."""
        mock_client = MagicMock()
        mock_client.invoke.side_effect = RuntimeError("Rate limit exceeded")
        wrapper = LLMClientWithRetry(client=mock_client, max_retries=1)

        with pytest.raises(LLMRateLimitError):
            wrapper.generate("Test prompt")


class TestExponentialBackoff:
    """Tests for exponential backoff behavior."""

    def test_wait_times_increase_exponentially(self) -> None:
        """Test that wait times follow exponential pattern (conceptual test)."""
        # This test verifies the retry decorator is configured correctly
        # by checking that it accepts the expected parameters
        decorator = create_retry_decorator(
            max_retries=4,
            min_wait=1.0,
            max_wait=16.0,
        )

        # The decorator should be callable and apply to functions
        @decorator
        def sample_func() -> str:
            return "ok"

        assert sample_func() == "ok"


class TestIntegrationScenarios:
    """Integration tests for retry scenarios."""

    def test_mixed_errors_then_success(self) -> None:
        """Test handling of mixed error types before success."""
        mock_client = MagicMock()
        mock_client.invoke.side_effect = [
            TimeoutError("First timeout"),
            RuntimeError("Rate limit hit"),
            '{"final": "result"}',
        ]

        result = call_llm_with_retry(
            prompt="Complex scenario",
            max_retries=3,
            client=mock_client,
        )

        assert result == '{"final": "result"}'
        assert mock_client.invoke.call_count == 3

    def test_timeout_followed_by_different_error(self) -> None:
        """Test timeout followed by non-retryable error."""
        mock_client = MagicMock()
        mock_client.invoke.side_effect = [
            TimeoutError("Initial timeout"),
            RuntimeError("Invalid API key - authentication failed"),
        ]

        # Non-rate-limit RuntimeError should not retry
        with pytest.raises(RuntimeError, match="Invalid API key"):
            call_llm_with_retry(
                prompt="Test",
                max_retries=3,
                client=mock_client,
            )

        assert mock_client.invoke.call_count == 2

    def test_all_retries_timeout(self) -> None:
        """Test scenario where all attempts timeout."""
        mock_client = MagicMock()
        mock_client.invoke.side_effect = TimeoutError("Network unreachable")

        with pytest.raises(LLMTimeoutError) as exc_info:
            call_llm_with_retry(
                prompt="Unreachable service",
                max_retries=3,
                timeout=15.0,
                client=mock_client,
            )

        error = exc_info.value
        assert error.retry_count == 4  # 1 initial + 3 retries
        assert error.timeout_seconds == 15.0
        assert mock_client.invoke.call_count == 4
