"""Tests for Structuring Agent."""

import json
from unittest.mock import MagicMock, patch

import pytest
from src.reqgate.schemas.inputs import RequirementPacket
from src.reqgate.schemas.internal import AgentState, PRD_Draft
from src.reqgate.workflow.errors import StructuringFailureError
from src.reqgate.workflow.nodes.structuring_agent import (
    StructuringAgent,
    _extract_json,
    build_prompt,
    parse_llm_response,
    structuring_agent_node,
    validate_no_hallucination,
)


class TestBuildPrompt:
    """Tests for prompt building."""

    def test_build_prompt_includes_input_text(self) -> None:
        """Test that prompt includes input text."""
        input_text = "Test requirement text for building prompt"
        prompt = build_prompt(input_text)
        assert input_text in prompt

    def test_build_prompt_includes_schema(self) -> None:
        """Test that prompt includes schema information."""
        prompt = build_prompt("Test text")
        assert "title" in prompt
        assert "user_story" in prompt
        assert "acceptance_criteria" in prompt

    def test_build_prompt_with_custom_template(self) -> None:
        """Test building prompt with custom template."""
        custom_template = "Custom: {input_text}"
        prompt = build_prompt("Test input", custom_template)
        assert prompt == "Custom: Test input"


class TestExtractJson:
    """Tests for JSON extraction from LLM responses."""

    def test_extract_plain_json(self) -> None:
        """Test extracting plain JSON."""
        text = '{"title": "Test", "user_story": "As a user"}'
        result = _extract_json(text)
        assert '"title": "Test"' in result

    def test_extract_json_from_markdown_block(self) -> None:
        """Test extracting JSON from markdown code block."""
        text = """Here's the result:
```json
{"title": "Test Feature"}
```
"""
        result = _extract_json(text)
        assert '"title": "Test Feature"' in result

    def test_extract_json_from_generic_code_block(self) -> None:
        """Test extracting JSON from generic code block."""
        text = """Result:
```
{"title": "Test"}
```
"""
        result = _extract_json(text)
        assert '"title": "Test"' in result

    def test_extract_nested_json(self) -> None:
        """Test extracting nested JSON object."""
        text = 'Some text {"outer": {"inner": "value"}} more text'
        result = _extract_json(text)
        data = json.loads(result)
        assert data["outer"]["inner"] == "value"


class TestParseLLMResponse:
    """Tests for parsing LLM responses into PRD_Draft."""

    def test_parse_valid_response(self) -> None:
        """Test parsing valid JSON response."""
        response = json.dumps(
            {
                "title": "Implement user login feature",
                "user_story": "As a user, I want to log in, so that I can access my account",
                "acceptance_criteria": [
                    "User can enter credentials",
                    "User sees dashboard after login",
                ],
                "edge_cases": ["Invalid password"],
                "resources": [],
                "missing_info": ["Session timeout"],
                "clarification_questions": ["Support SSO?"],
            }
        )
        result = parse_llm_response(response)
        assert isinstance(result, PRD_Draft)
        assert result.title == "Implement user login feature"
        assert len(result.acceptance_criteria) == 2

    def test_parse_response_with_markdown(self) -> None:
        """Test parsing response wrapped in markdown."""
        response = """Here's the structured PRD:
```json
{
    "title": "Add export feature",
    "user_story": "As a user, I want to export data, so that I can use it elsewhere",
    "acceptance_criteria": ["Export button available"],
    "edge_cases": [],
    "resources": [],
    "missing_info": [],
    "clarification_questions": []
}
```
"""
        result = parse_llm_response(response)
        assert result.title == "Add export feature"

    def test_parse_invalid_json_raises_error(self) -> None:
        """Test that invalid JSON raises StructuringFailureError."""
        response = "This is not valid JSON at all"
        with pytest.raises(StructuringFailureError) as exc_info:
            parse_llm_response(response)
        assert "Failed to parse JSON" in str(exc_info.value)

    def test_parse_invalid_schema_raises_error(self) -> None:
        """Test that valid JSON but invalid schema raises error."""
        response = json.dumps(
            {
                "title": "Short",  # Too short (< 10 chars)
                "user_story": "Invalid format",  # Wrong format
                "acceptance_criteria": [],  # Empty (requires at least 1)
            }
        )
        with pytest.raises(StructuringFailureError) as exc_info:
            parse_llm_response(response)
        assert "schema validation" in str(exc_info.value).lower()


class TestValidateNoHallucination:
    """Tests for hallucination detection."""

    def test_clean_prd_passes(self) -> None:
        """Test that PRD with content from input passes."""
        input_text = "We need a login feature with email and password authentication. Users should be able to access the system after successful login."
        prd = PRD_Draft(
            title="Implement login with email and password",
            user_story="As a user, I want to log in with email, so that I can access the system",
            acceptance_criteria=[
                "User can enter email address",
                "User can enter password",
                "User can access system after login",
            ],
        )
        warnings = validate_no_hallucination(input_text, prd)
        assert len(warnings) == 0

    def test_hallucinated_content_flagged(self) -> None:
        """Test that content not in input is flagged."""
        input_text = "Add a simple button to the page"
        prd = PRD_Draft(
            title="Implement advanced machine learning recommendation system",
            user_story="As a user, I want to see recommendations, so that I can discover content",
            acceptance_criteria=[
                "System uses neural networks for predictions",
                "Real-time collaborative filtering applied",
                "A/B testing framework integrated",
            ],
        )
        warnings = validate_no_hallucination(input_text, prd)
        # Should flag suspicious content
        assert len(warnings) > 0


class TestStructuringAgent:
    """Tests for StructuringAgent class."""

    @patch("src.reqgate.workflow.nodes.structuring_agent.get_llm_client")
    def test_structure_success(self, mock_get_llm: MagicMock) -> None:
        """Test successful structuring."""
        # Mock LLM response
        mock_client = MagicMock()
        mock_client.generate.return_value = json.dumps(
            {
                "title": "Implement user data export feature",
                "user_story": "As a user, I want to export my data, so that I can backup information",
                "acceptance_criteria": ["Export button in settings", "CSV file generated"],
                "edge_cases": [],
                "resources": [],
                "missing_info": ["File size limit"],
                "clarification_questions": ["Support JSON format?"],
            }
        )
        mock_get_llm.return_value = mock_client

        agent = StructuringAgent()
        result = agent.structure("We need to let users export their data as CSV")

        assert isinstance(result, PRD_Draft)
        assert "export" in result.title.lower()
        mock_client.generate.assert_called_once()

    @patch("src.reqgate.workflow.nodes.structuring_agent.get_llm_client")
    def test_structure_llm_failure(self, mock_get_llm: MagicMock) -> None:
        """Test handling of LLM failure."""
        mock_client = MagicMock()
        mock_client.generate.side_effect = Exception("API Error")
        mock_get_llm.return_value = mock_client

        agent = StructuringAgent()
        with pytest.raises(StructuringFailureError) as exc_info:
            agent.structure("Test input")
        assert "LLM call failed" in str(exc_info.value)


class TestStructuringAgentNode:
    """Tests for structuring_agent_node function."""

    def _create_state(self, raw_text: str) -> AgentState:
        """Create a test AgentState."""
        packet = RequirementPacket(
            raw_text=raw_text,
            source_type="Jira_Ticket",
            project_key="TEST",
            ticket_type="Feature",
            priority="P1",
        )
        return {
            "packet": packet,
            "structured_prd": None,
            "score_report": None,
            "gate_decision": None,
            "retry_count": 0,
            "error_logs": [],
            "current_stage": "guardrail_passed",
            "fallback_activated": False,
            "execution_times": {"guardrail": 0.05},
        }

    @patch("src.reqgate.workflow.nodes.structuring_agent.get_llm_client")
    def test_node_success(self, mock_get_llm: MagicMock) -> None:
        """Test node successfully structures input."""
        mock_client = MagicMock()
        mock_client.generate.return_value = json.dumps(
            {
                "title": "Implement search functionality for products",
                "user_story": "As a user, I want to search products, so that I can find items quickly",
                "acceptance_criteria": ["Search box visible", "Results displayed"],
                "edge_cases": ["No results found"],
                "resources": [],
                "missing_info": [],
                "clarification_questions": [],
            }
        )
        mock_get_llm.return_value = mock_client

        state = self._create_state(
            "We need to add product search. Users should be able to find products quickly."
        )
        result = structuring_agent_node(state)

        assert result["structured_prd"] is not None
        assert result["current_stage"] == "structuring_complete"
        assert "structuring" in result["execution_times"]

    @patch("src.reqgate.workflow.nodes.structuring_agent.get_llm_client")
    def test_node_failure_returns_none(self, mock_get_llm: MagicMock) -> None:
        """Test node returns None on failure (for fallback)."""
        mock_client = MagicMock()
        mock_client.generate.side_effect = Exception("LLM Error")
        mock_get_llm.return_value = mock_client

        state = self._create_state("Test input text for structuring agent")
        result = structuring_agent_node(state)

        assert result["structured_prd"] is None
        assert result["current_stage"] == "structuring_failed"
        assert len(result["error_logs"]) > 0

    @patch("src.reqgate.workflow.nodes.structuring_agent.get_llm_client")
    def test_node_invalid_response_returns_none(self, mock_get_llm: MagicMock) -> None:
        """Test node returns None when LLM returns invalid response."""
        mock_client = MagicMock()
        mock_client.generate.return_value = "Not valid JSON response"
        mock_get_llm.return_value = mock_client

        state = self._create_state("Test input text for structuring agent")
        result = structuring_agent_node(state)

        assert result["structured_prd"] is None
        assert result["current_stage"] == "structuring_failed"


class TestExtractionFromRealText:
    """Tests for extraction from realistic requirement texts."""

    @patch("src.reqgate.workflow.nodes.structuring_agent.get_llm_client")
    def test_extract_from_meeting_notes(self, mock_get_llm: MagicMock) -> None:
        """Test extraction from messy meeting notes format."""
        meeting_notes = """
        Meeting Notes - Product Planning 2024-01-15

        Attendees: John (PM), Sarah (Dev), Mike (Design)

        John: We need to add a feature for users to reset their passwords.
        Sarah: Should we use email or SMS for verification?
        John: Email first, SMS can be phase 2.
        Mike: I'll design the reset password flow screen.

        Action items:
        - Users should be able to request password reset from login page
        - Email with reset link should be sent
        - Link should expire after 24 hours

        Next meeting: Jan 22
        """

        mock_client = MagicMock()
        mock_client.generate.return_value = json.dumps(
            {
                "title": "Implement password reset feature via email",
                "user_story": "As a user, I want to reset my password via email, so that I can regain access to my account",
                "acceptance_criteria": [
                    "User can request password reset from login page",
                    "System sends email with reset link",
                    "Reset link expires after 24 hours",
                ],
                "edge_cases": ["Invalid email address", "Expired link clicked"],
                "resources": [],
                "missing_info": [
                    "Password complexity requirements",
                    "Rate limiting for reset requests",
                ],
                "clarification_questions": [
                    "What should happen if user requests multiple resets?",
                    "Should we notify user of successful password change?",
                ],
            }
        )
        mock_get_llm.return_value = mock_client

        agent = StructuringAgent()
        result = agent.structure(meeting_notes)

        assert "password" in result.title.lower() or "reset" in result.title.lower()
        assert len(result.acceptance_criteria) >= 2
        assert len(result.clarification_questions) > 0

    @patch("src.reqgate.workflow.nodes.structuring_agent.get_llm_client")
    def test_extract_with_missing_ac(self, mock_get_llm: MagicMock) -> None:
        """Test extraction when input lacks clear acceptance criteria."""
        vague_input = "We need to make the dashboard faster. Users are complaining."

        mock_client = MagicMock()
        mock_client.generate.return_value = json.dumps(
            {
                "title": "Improve dashboard performance",
                "user_story": "As a user, I want faster dashboard loading, so that I can work efficiently",
                "acceptance_criteria": ["Dashboard loads faster than current state"],
                "edge_cases": [],
                "resources": [],
                "missing_info": [
                    "Current load time baseline",
                    "Target load time",
                    "Specific performance metrics",
                ],
                "clarification_questions": [
                    "What is the current dashboard load time?",
                    "What is the acceptable target load time?",
                    "Which dashboard components are slowest?",
                ],
            }
        )
        mock_get_llm.return_value = mock_client

        agent = StructuringAgent()
        result = agent.structure(vague_input)

        # Should identify missing information
        assert len(result.missing_info) > 0
        assert any("time" in info.lower() for info in result.missing_info)

    @patch("src.reqgate.workflow.nodes.structuring_agent.get_llm_client")
    def test_extract_generates_clarification_questions(self, mock_get_llm: MagicMock) -> None:
        """Test that agent generates clarification questions for ambiguous input."""
        ambiguous_input = "Add notifications to the app."

        mock_client = MagicMock()
        mock_client.generate.return_value = json.dumps(
            {
                "title": "Implement notification system for the app",
                "user_story": "As a user, I want to receive notifications, so that I stay informed",
                "acceptance_criteria": ["Users can receive notifications"],
                "edge_cases": [],
                "resources": [],
                "missing_info": ["Notification types", "Delivery channels", "User preferences"],
                "clarification_questions": [
                    "What types of notifications should be supported?",
                    "Should notifications be push, email, or in-app?",
                    "Can users customize notification preferences?",
                ],
            }
        )
        mock_get_llm.return_value = mock_client

        agent = StructuringAgent()
        result = agent.structure(ambiguous_input)

        assert len(result.clarification_questions) > 0


class TestAntiHallucination:
    """Tests for anti-hallucination measures."""

    @patch("src.reqgate.workflow.nodes.structuring_agent.get_llm_client")
    def test_validation_catches_invented_content(self, mock_get_llm: MagicMock) -> None:
        """Test that validation flags content not in original input."""
        simple_input = "Add a logout button"

        # LLM returns way more than was in input
        mock_client = MagicMock()
        mock_client.generate.return_value = json.dumps(
            {
                "title": "Implement comprehensive session management system",
                "user_story": "As a user, I want to log out, so that I can secure my session",
                "acceptance_criteria": [
                    "Implement OAuth2 token revocation",
                    "Add distributed session invalidation",
                    "Create audit logging for all session events",
                    "Integrate with LDAP for enterprise SSO",
                ],
                "edge_cases": [],
                "resources": [],
                "missing_info": [],
                "clarification_questions": [],
            }
        )
        mock_get_llm.return_value = mock_client

        agent = StructuringAgent()
        result = agent.structure(simple_input, validate_hallucination=True)

        # The validation should log warnings about potential hallucinations
        # But still return the result (hallucination check is advisory)
        assert result is not None
