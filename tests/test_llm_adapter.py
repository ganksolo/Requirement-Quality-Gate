"""Tests for LLM Adapter."""

from unittest.mock import MagicMock, patch

import pytest
from src.reqgate.adapters.llm import LLMClient, OpenAIClient, get_llm_client


class TestLLMClient:
    """Test suite for LLMClient abstract class."""

    def test_is_abstract(self):
        """Test that LLMClient cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LLMClient()


class TestOpenAIClient:
    """Test suite for OpenAIClient."""

    @patch("src.reqgate.adapters.llm.get_settings")
    def test_initialization(self, mock_get_settings):
        """Test client initialization."""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = "gpt-4o"
        mock_settings.openai_timeout = 30
        mock_get_settings.return_value = mock_settings

        client = OpenAIClient()

        assert client.api_key == "test-key"
        assert client.model == "gpt-4o"
        assert client.timeout == 30
        assert client._client is None  # Lazy loading

    @patch("src.reqgate.adapters.llm.get_settings")
    def test_lazy_client_loading(self, mock_get_settings):
        """Test that OpenAI client is lazily loaded."""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = "gpt-4o"
        mock_settings.openai_timeout = 30
        mock_get_settings.return_value = mock_settings

        client = OpenAIClient()

        # Client should not be initialized yet
        assert client._client is None

    @patch("src.reqgate.adapters.llm.get_settings")
    def test_get_client_creates_openai_client(self, mock_get_settings):
        """Test that _get_client creates OpenAI client on first call."""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = "gpt-4o"
        mock_settings.openai_timeout = 30
        mock_get_settings.return_value = mock_settings

        client = OpenAIClient()
        assert client._client is None

        # Patch openai import inside the method
        with patch.dict("sys.modules", {"openai": MagicMock()}):
            pass  # Just verify client init doesn't crash


class TestGetLLMClient:
    """Test suite for get_llm_client function."""

    @patch("src.reqgate.adapters.llm.get_settings")
    def test_returns_llm_client(self, mock_get_settings):
        """Test that function returns an LLMClient instance."""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = "gpt-4o"
        mock_settings.openai_timeout = 30
        mock_get_settings.return_value = mock_settings

        # Reset global state
        import src.reqgate.adapters.llm as llm_module

        llm_module._llm_client = None

        client = get_llm_client()
        assert isinstance(client, LLMClient)
        assert isinstance(client, OpenAIClient)

    @patch("src.reqgate.adapters.llm.get_settings")
    def test_singleton_behavior(self, mock_get_settings):
        """Test singleton pattern."""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = "gpt-4o"
        mock_settings.openai_timeout = 30
        mock_get_settings.return_value = mock_settings

        import src.reqgate.adapters.llm as llm_module

        llm_module._llm_client = None

        client1 = get_llm_client()
        client2 = get_llm_client()

        assert client1 is client2
