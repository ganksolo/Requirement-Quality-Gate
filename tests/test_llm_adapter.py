"""Tests for LLM Adapter."""

from unittest.mock import MagicMock, patch

import pytest
from src.reqgate.adapters.llm import LLMClient, OpenRouterClient, get_llm_client


class TestLLMClient:
    """Test suite for LLMClient abstract class."""

    def test_is_abstract(self):
        """Test that LLMClient cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LLMClient()


class TestOpenRouterClient:
    """Test suite for OpenRouterClient."""

    @patch("src.reqgate.adapters.llm.get_settings")
    def test_initialization(self, mock_get_settings):
        """Test client initialization."""
        mock_settings = MagicMock()
        mock_settings.openrouter_api_key = "test-key"
        mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
        mock_settings.llm_model = "openai/gpt-4o"
        mock_settings.llm_timeout = 60
        mock_settings.fallback_models_list = ["deepseek/deepseek-chat"]
        mock_get_settings.return_value = mock_settings

        client = OpenRouterClient()

        assert client.api_key == "test-key"
        assert client.model == "openai/gpt-4o"
        assert client.timeout == 60
        assert client.fallback_models == ["deepseek/deepseek-chat"]
        assert client._client is None  # Lazy loading

    @patch("src.reqgate.adapters.llm.get_settings")
    def test_lazy_client_loading(self, mock_get_settings):
        """Test that OpenAI client is lazily loaded."""
        mock_settings = MagicMock()
        mock_settings.openrouter_api_key = "test-key"
        mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
        mock_settings.llm_model = "openai/gpt-4o"
        mock_settings.llm_timeout = 60
        mock_settings.fallback_models_list = []
        mock_get_settings.return_value = mock_settings

        client = OpenRouterClient()

        # Client should not be initialized yet
        assert client._client is None

    @patch("src.reqgate.adapters.llm.get_settings")
    def test_get_client_creates_openai_client(self, mock_get_settings):
        """Test that _get_client creates OpenAI client on first call."""
        mock_settings = MagicMock()
        mock_settings.openrouter_api_key = "test-key"
        mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
        mock_settings.llm_model = "openai/gpt-4o"
        mock_settings.llm_timeout = 60
        mock_settings.fallback_models_list = []
        mock_get_settings.return_value = mock_settings

        client = OpenRouterClient()
        openai_client = client._get_client()

        assert openai_client is not None
        assert client._client is openai_client


class TestGetLLMClient:
    """Test suite for get_llm_client function."""

    @patch("src.reqgate.adapters.llm.get_settings")
    def test_returns_llm_client(self, mock_get_settings):
        """Test that function returns an LLMClient instance."""
        mock_settings = MagicMock()
        mock_settings.openrouter_api_key = "test-key"
        mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
        mock_settings.llm_model = "openai/gpt-4o"
        mock_settings.llm_timeout = 60
        mock_settings.fallback_models_list = []
        mock_get_settings.return_value = mock_settings

        # Reset global state
        import src.reqgate.adapters.llm as llm_module

        llm_module._llm_client = None

        client = get_llm_client()
        assert isinstance(client, LLMClient)
        assert isinstance(client, OpenRouterClient)

    @patch("src.reqgate.adapters.llm.get_settings")
    def test_singleton_behavior(self, mock_get_settings):
        """Test singleton pattern."""
        mock_settings = MagicMock()
        mock_settings.openrouter_api_key = "test-key"
        mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
        mock_settings.llm_model = "openai/gpt-4o"
        mock_settings.llm_timeout = 60
        mock_settings.fallback_models_list = []
        mock_get_settings.return_value = mock_settings

        import src.reqgate.adapters.llm as llm_module

        llm_module._llm_client = None

        client1 = get_llm_client()
        client2 = get_llm_client()

        assert client1 is client2
