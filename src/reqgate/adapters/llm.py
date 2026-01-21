"""
LLM adapter for calling language models.

Provides abstraction over different LLM providers.
Phase 1: Placeholder - Full implementation in later tasks.
"""

from abc import ABC, abstractmethod

from pydantic import BaseModel
from src.reqgate.config.settings import get_settings


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


class OpenAIClient(LLMClient):
    """OpenAI client implementation."""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model
        self.timeout = settings.openai_timeout
        self._client = None

    def _get_client(self):
        """Lazy load the OpenAI client."""
        if self._client is None:
            import openai
            self._client = openai.OpenAI(api_key=self.api_key)
        return self._client

    def invoke(self, prompt: str, _response_schema: type[BaseModel]) -> str:
        """
        Call OpenAI API.

        Args:
            prompt: The prompt to send
            response_schema: Expected response schema for structured output

        Returns:
            JSON string response

        Raises:
            TimeoutError: On API timeout
            RuntimeError: On API error
        """
        import openai

        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a technical requirement reviewer."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                timeout=self.timeout,
            )

            return response.choices[0].message.content or "{}"

        except openai.APITimeoutError as e:
            raise TimeoutError(f"LLM request timeout: {e}") from e
        except openai.APIError as e:
            raise RuntimeError(f"LLM API error: {e}") from e


_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Get LLM client singleton."""
    global _llm_client
    if _llm_client is None:
        _llm_client = OpenAIClient()
    return _llm_client
