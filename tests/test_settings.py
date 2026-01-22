"""Tests for configuration settings."""

import os
from unittest.mock import patch

import pytest
from src.reqgate.config.settings import Settings, get_settings


class TestSettings:
    """Test suite for Settings class."""

    def test_default_values(self):
        """Test that default values are applied correctly."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()

            assert settings.reqgate_env == "development"
            assert settings.reqgate_port == 8000
            assert settings.log_level == "INFO"
            assert settings.openai_model == "gpt-4o"
            assert settings.openai_timeout == 30
            assert settings.default_threshold == 60

    def test_environment_override(self):
        """Test that environment variables override defaults."""
        env_vars = {
            "REQGATE_ENV": "production",
            "REQGATE_PORT": "9000",
            "LOG_LEVEL": "DEBUG",
            "OPENAI_API_KEY": "sk-test-key",
            "OPENAI_MODEL": "gpt-4",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()

            assert settings.reqgate_env == "production"
            assert settings.reqgate_port == 9000
            assert settings.log_level == "DEBUG"
            assert settings.openai_api_key == "sk-test-key"
            assert settings.openai_model == "gpt-4"

    def test_is_development_property(self):
        """Test is_development property."""
        with patch.dict(os.environ, {"REQGATE_ENV": "development"}, clear=True):
            settings = Settings()
            assert settings.is_development is True
            assert settings.is_production is False

    def test_is_production_property(self):
        """Test is_production property."""
        with patch.dict(os.environ, {"REQGATE_ENV": "production"}, clear=True):
            settings = Settings()
            assert settings.is_production is True
            assert settings.is_development is False

    def test_invalid_env_value(self):
        """Test that invalid env values are rejected."""
        with patch.dict(os.environ, {"REQGATE_ENV": "invalid"}, clear=True):
            with pytest.raises(ValueError):
                Settings()

    def test_invalid_log_level(self):
        """Test that invalid log levels are rejected."""
        with patch.dict(os.environ, {"LOG_LEVEL": "INVALID"}, clear=True):
            with pytest.raises(ValueError):
                Settings()


class TestGetSettings:
    """Test suite for get_settings singleton."""

    def test_returns_settings_instance(self):
        """Test that get_settings returns a Settings instance."""
        # Clear the cache first
        get_settings.cache_clear()

        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_singleton_behavior(self):
        """Test that get_settings returns the same instance."""
        get_settings.cache_clear()

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2
