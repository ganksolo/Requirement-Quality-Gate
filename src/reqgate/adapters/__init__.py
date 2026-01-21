"""Adapters module - External service integrations."""

from src.reqgate.adapters.llm import LLMClient, OpenAIClient, get_llm_client

__all__ = [
    "LLMClient",
    "OpenAIClient",
    "get_llm_client",
]
