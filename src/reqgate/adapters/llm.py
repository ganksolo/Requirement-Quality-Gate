"""
LLM adapter for calling language models via OpenRouter.

Provides abstraction over different LLM providers through OpenRouter's unified API.
"""

import logging
from abc import ABC, abstractmethod

from openai import OpenAI
from pydantic import BaseModel

from src.reqgate.config.settings import get_settings

logger = logging.getLogger("reqgate.llm")


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
