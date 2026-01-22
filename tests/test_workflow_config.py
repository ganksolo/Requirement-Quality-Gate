"""Tests for WorkflowConfig schema validation."""

import pytest
from pydantic import ValidationError
from src.reqgate.schemas.config import WorkflowConfig


class TestWorkflowConfigDefaults:
    """Tests for WorkflowConfig default values."""

    def test_default_values(self) -> None:
        """Test that WorkflowConfig has correct default values."""
        config = WorkflowConfig()
        assert config.enable_guardrail is True
        assert config.enable_structuring is True
        assert config.enable_fallback is True
        assert config.max_retries == 3
        assert config.llm_timeout == 30.0
        assert config.structuring_timeout == 20.0
        assert config.guardrail_mode == "lenient"

    def test_create_with_all_defaults(self) -> None:
        """Test creating config with no arguments uses all defaults."""
        config = WorkflowConfig()
        # All fields should have their default values
        assert config.model_dump() == {
            "enable_guardrail": True,
            "enable_structuring": True,
            "enable_fallback": True,
            "max_retries": 3,
            "llm_timeout": 30.0,
            "structuring_timeout": 20.0,
            "guardrail_mode": "lenient",
        }


class TestWorkflowConfigCustomValues:
    """Tests for WorkflowConfig with custom values."""

    def test_custom_boolean_flags(self) -> None:
        """Test setting custom boolean flags."""
        config = WorkflowConfig(
            enable_guardrail=False,
            enable_structuring=False,
            enable_fallback=False,
        )
        assert config.enable_guardrail is False
        assert config.enable_structuring is False
        assert config.enable_fallback is False

    def test_custom_max_retries(self) -> None:
        """Test setting custom max_retries."""
        config = WorkflowConfig(max_retries=5)
        assert config.max_retries == 5

    def test_custom_llm_timeout(self) -> None:
        """Test setting custom llm_timeout."""
        config = WorkflowConfig(llm_timeout=60.0)
        assert config.llm_timeout == 60.0

    def test_custom_structuring_timeout(self) -> None:
        """Test setting custom structuring_timeout."""
        config = WorkflowConfig(structuring_timeout=30.0)
        assert config.structuring_timeout == 30.0

    def test_strict_guardrail_mode(self) -> None:
        """Test setting guardrail_mode to strict."""
        config = WorkflowConfig(guardrail_mode="strict")
        assert config.guardrail_mode == "strict"

    def test_full_custom_config(self) -> None:
        """Test creating config with all custom values."""
        config = WorkflowConfig(
            enable_guardrail=False,
            enable_structuring=True,
            enable_fallback=False,
            max_retries=5,
            llm_timeout=60.0,
            structuring_timeout=30.0,
            guardrail_mode="strict",
        )
        assert config.enable_guardrail is False
        assert config.enable_structuring is True
        assert config.enable_fallback is False
        assert config.max_retries == 5
        assert config.llm_timeout == 60.0
        assert config.structuring_timeout == 30.0
        assert config.guardrail_mode == "strict"


class TestWorkflowConfigValidation:
    """Tests for WorkflowConfig validation rules."""

    def test_max_retries_min_boundary(self) -> None:
        """Test that max_retries accepts minimum value (0)."""
        config = WorkflowConfig(max_retries=0)
        assert config.max_retries == 0

    def test_max_retries_max_boundary(self) -> None:
        """Test that max_retries accepts maximum value (10)."""
        config = WorkflowConfig(max_retries=10)
        assert config.max_retries == 10

    def test_max_retries_below_min(self) -> None:
        """Test that max_retries below 0 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowConfig(max_retries=-1)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_max_retries_above_max(self) -> None:
        """Test that max_retries above 10 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowConfig(max_retries=11)
        assert "less than or equal to 10" in str(exc_info.value)

    def test_llm_timeout_min_boundary(self) -> None:
        """Test that llm_timeout accepts minimum value (5.0)."""
        config = WorkflowConfig(llm_timeout=5.0)
        assert config.llm_timeout == 5.0

    def test_llm_timeout_max_boundary(self) -> None:
        """Test that llm_timeout accepts maximum value (120.0)."""
        config = WorkflowConfig(llm_timeout=120.0)
        assert config.llm_timeout == 120.0

    def test_llm_timeout_below_min(self) -> None:
        """Test that llm_timeout below 5.0 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowConfig(llm_timeout=4.9)
        assert "greater than or equal to 5" in str(exc_info.value)

    def test_llm_timeout_above_max(self) -> None:
        """Test that llm_timeout above 120.0 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowConfig(llm_timeout=121.0)
        assert "less than or equal to 120" in str(exc_info.value)

    def test_structuring_timeout_min_boundary(self) -> None:
        """Test that structuring_timeout accepts minimum value (5.0)."""
        config = WorkflowConfig(structuring_timeout=5.0)
        assert config.structuring_timeout == 5.0

    def test_structuring_timeout_max_boundary(self) -> None:
        """Test that structuring_timeout accepts maximum value (60.0)."""
        config = WorkflowConfig(structuring_timeout=60.0)
        assert config.structuring_timeout == 60.0

    def test_structuring_timeout_below_min(self) -> None:
        """Test that structuring_timeout below 5.0 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowConfig(structuring_timeout=4.9)
        assert "greater than or equal to 5" in str(exc_info.value)

    def test_structuring_timeout_above_max(self) -> None:
        """Test that structuring_timeout above 60.0 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowConfig(structuring_timeout=61.0)
        assert "less than or equal to 60" in str(exc_info.value)

    def test_invalid_guardrail_mode(self) -> None:
        """Test that invalid guardrail_mode is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowConfig(guardrail_mode="invalid")  # type: ignore
        assert "Input should be 'strict' or 'lenient'" in str(exc_info.value)


class TestWorkflowConfigSerialization:
    """Tests for WorkflowConfig serialization."""

    def test_json_serialization(self) -> None:
        """Test that WorkflowConfig can be serialized to JSON."""
        config = WorkflowConfig(
            max_retries=5,
            guardrail_mode="strict",
        )
        json_str = config.model_dump_json()
        assert '"max_retries":5' in json_str
        assert '"guardrail_mode":"strict"' in json_str

    def test_dict_serialization(self) -> None:
        """Test that WorkflowConfig can be serialized to dict."""
        config = WorkflowConfig()
        data = config.model_dump()
        assert isinstance(data, dict)
        assert data["enable_guardrail"] is True
        assert data["max_retries"] == 3

    def test_from_dict(self) -> None:
        """Test that WorkflowConfig can be created from dict."""
        data = {
            "enable_guardrail": False,
            "max_retries": 5,
            "guardrail_mode": "strict",
        }
        config = WorkflowConfig.model_validate(data)
        assert config.enable_guardrail is False
        assert config.max_retries == 5
        assert config.guardrail_mode == "strict"
        # Other fields should have defaults
        assert config.enable_structuring is True
        assert config.llm_timeout == 30.0

    def test_schema_example(self) -> None:
        """Test that schema example is valid."""
        schema = WorkflowConfig.model_json_schema()
        example = schema.get("example") or schema.get("examples", [{}])[0]
        # The example should be valid
        config = WorkflowConfig.model_validate(example)
        assert config.enable_guardrail is True
        assert config.max_retries == 3


class TestWorkflowConfigImport:
    """Tests for WorkflowConfig import from schemas module."""

    def test_import_from_schemas(self) -> None:
        """Test that WorkflowConfig can be imported from schemas module."""
        from src.reqgate.schemas import WorkflowConfig as ImportedConfig

        config = ImportedConfig()
        assert config.enable_guardrail is True
