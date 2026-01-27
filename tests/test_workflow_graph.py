"""Tests for LangGraph workflow."""

from unittest.mock import MagicMock, patch

import pytest
from src.reqgate.schemas.config import WorkflowConfig
from src.reqgate.schemas.inputs import RequirementPacket
from src.reqgate.schemas.internal import AgentState, PRD_Draft
from src.reqgate.schemas.outputs import TicketScoreReport
from src.reqgate.workflow.errors import GuardrailRejectionError, WorkflowExecutionError
from src.reqgate.workflow.graph import (
    activate_fallback,
    create_initial_state,
    create_workflow,
    format_prd_for_scoring,
    hard_gate_node,
    run_workflow,
    scoring_node,
    should_fallback,
)


# Test fixtures
def make_packet(
    raw_text: str = "This is a test requirement with enough characters",
) -> RequirementPacket:
    """Create a valid RequirementPacket for testing."""
    return RequirementPacket(
        raw_text=raw_text,
        source_type="Jira_Ticket",
        project_key="TEST",
        priority="P1",
        ticket_type="Feature",
    )


def make_prd() -> PRD_Draft:
    """Create a valid PRD_Draft for testing."""
    return PRD_Draft(
        title="Implement user login feature",
        user_story="As a user, I want to log in, so that I can access my account",
        acceptance_criteria=["User can enter credentials", "User sees dashboard"],
    )


class TestFormatPRDForScoring:
    """Tests for format_prd_for_scoring function."""

    def test_basic_formatting(self) -> None:
        """Test basic PRD formatting."""
        prd = make_prd()

        result = format_prd_for_scoring(prd)

        assert "# Implement user login feature" in result
        assert "## User Story" in result
        assert "As a user, I want to log in" in result
        assert "## Acceptance Criteria" in result
        assert "1. User can enter credentials" in result
        assert "2. User sees dashboard" in result

    def test_formatting_with_edge_cases(self) -> None:
        """Test PRD formatting with edge cases."""
        prd = PRD_Draft(
            title="Implement password reset feature",
            user_story="As a user, I want to reset password, so that I can regain access",
            acceptance_criteria=["Reset link sent via email"],
            edge_cases=["Invalid email", "Expired link"],
        )

        result = format_prd_for_scoring(prd)

        assert "## Edge Cases" in result
        assert "- Invalid email" in result
        assert "- Expired link" in result

    def test_formatting_with_resources(self) -> None:
        """Test PRD formatting with resources."""
        prd = PRD_Draft(
            title="Implement OAuth integration feature",
            user_story="As a user, I want OAuth login, so that I can sign in quickly",
            acceptance_criteria=["OAuth flow works"],
            resources=["OAuth RFC", "Google docs"],
        )

        result = format_prd_for_scoring(prd)

        assert "## Resources" in result
        assert "- OAuth RFC" in result
        assert "- Google docs" in result

    def test_formatting_with_missing_info(self) -> None:
        """Test PRD formatting with missing info."""
        prd = PRD_Draft(
            title="Implement notification system feature",
            user_story="As a user, I want notifications, so that I stay informed",
            acceptance_criteria=["User receives notifications"],
            missing_info=["Notification types", "Delivery channels"],
        )

        result = format_prd_for_scoring(prd)

        assert "## Identified Gaps" in result
        assert "- Notification types" in result
        assert "- Delivery channels" in result


class TestCreateInitialState:
    """Tests for create_initial_state function."""

    def test_creates_valid_state(self) -> None:
        """Test initial state creation."""
        packet = make_packet()

        state = create_initial_state(packet)

        assert state["packet"] is packet
        assert state["structured_prd"] is None
        assert state["score_report"] is None
        assert state["gate_decision"] is None
        assert state["retry_count"] == 0
        assert state["error_logs"] == []
        assert state["current_stage"] == "init"
        assert state["fallback_activated"] is False
        assert state["execution_times"] == {}


class TestShouldFallback:
    """Tests for should_fallback routing function."""

    def test_returns_scoring_when_prd_available(self) -> None:
        """Test routing when structured PRD is available."""
        prd = make_prd()
        state: AgentState = {
            "packet": make_packet(),
            "structured_prd": prd,
            "score_report": None,
            "gate_decision": None,
            "retry_count": 0,
            "error_logs": [],
            "current_stage": "structuring",
            "fallback_activated": False,
            "execution_times": {},
        }

        result = should_fallback(state)

        assert result == "structure_check"

    def test_returns_fallback_when_no_prd(self) -> None:
        """Test routing when no structured PRD."""
        state: AgentState = {
            "packet": make_packet(),
            "structured_prd": None,
            "score_report": None,
            "gate_decision": None,
            "retry_count": 0,
            "error_logs": [],
            "current_stage": "structuring",
            "fallback_activated": False,
            "execution_times": {},
        }

        result = should_fallback(state)

        assert result == "fallback_scoring"


class TestActivateFallback:
    """Tests for activate_fallback function."""

    def test_sets_fallback_flag(self) -> None:
        """Test that fallback flag is set."""
        state: AgentState = {
            "packet": make_packet(),
            "structured_prd": None,
            "score_report": None,
            "gate_decision": None,
            "retry_count": 0,
            "error_logs": [],
            "current_stage": "structuring",
            "fallback_activated": False,
            "execution_times": {},
        }

        result = activate_fallback(state)

        assert result["fallback_activated"] is True
        assert "Fallback activated" in result["error_logs"][0]


class TestScoringNode:
    """Tests for scoring_node function."""

    @patch("src.reqgate.workflow.graph.ScoringAgent")
    def test_scores_with_structured_prd(self, mock_agent_class: MagicMock) -> None:
        """Test scoring with structured PRD."""
        prd = make_prd()

        mock_report = MagicMock(spec=TicketScoreReport)
        mock_report.total_score = 85
        mock_agent = MagicMock()
        mock_agent.score.return_value = mock_report
        mock_agent_class.return_value = mock_agent

        state: AgentState = {
            "packet": make_packet("Original requirement text for testing"),
            "structured_prd": prd,
            "score_report": None,
            "gate_decision": None,
            "retry_count": 0,
            "error_logs": [],
            "current_stage": "init",
            "fallback_activated": False,
            "execution_times": {},
        }

        result = scoring_node(state)

        assert result["score_report"] is mock_report
        assert result["current_stage"] == "scoring"
        assert "scoring" in result["execution_times"]

    @patch("src.reqgate.workflow.graph.ScoringAgent")
    def test_applies_fallback_penalty(self, mock_agent_class: MagicMock) -> None:
        """Test that fallback penalty is applied."""
        mock_report = MagicMock(spec=TicketScoreReport)
        mock_report.total_score = 80
        mock_agent = MagicMock()
        mock_agent.score.return_value = mock_report
        mock_agent_class.return_value = mock_agent

        state: AgentState = {
            "packet": make_packet("Test requirement with fallback mode enabled"),
            "structured_prd": None,
            "score_report": None,
            "gate_decision": None,
            "retry_count": 0,
            "error_logs": [],
            "current_stage": "init",
            "fallback_activated": True,  # Fallback mode
            "execution_times": {},
        }

        scoring_node(state)

        # Score should be reduced by 5
        assert mock_report.total_score == 75

    @patch("src.reqgate.workflow.graph.ScoringAgent")
    def test_handles_scoring_error(self, mock_agent_class: MagicMock) -> None:
        """Test error handling in scoring node."""
        mock_agent = MagicMock()
        mock_agent.score.side_effect = RuntimeError("LLM error")
        mock_agent_class.return_value = mock_agent

        state: AgentState = {
            "packet": make_packet("Test requirement for error handling"),
            "structured_prd": None,
            "score_report": None,
            "gate_decision": None,
            "retry_count": 0,
            "error_logs": [],
            "current_stage": "init",
            "fallback_activated": False,
            "execution_times": {},
        }

        result = scoring_node(state)

        # Should not raise, but log error
        assert result["score_report"] is None
        assert len(result["error_logs"]) > 0
        assert "Scoring failed" in result["error_logs"][0]


class TestHardGateNode:
    """Tests for hard_gate_node function."""

    @patch("src.reqgate.workflow.graph.HardGate")
    def test_passes_good_score(self, mock_gate_class: MagicMock) -> None:
        """Test gate passes for good score."""
        mock_gate = MagicMock()
        mock_gate.decide.return_value = "PASS"
        mock_gate_class.return_value = mock_gate

        mock_report = MagicMock(spec=TicketScoreReport)

        state: AgentState = {
            "packet": make_packet("Test requirement for gate pass scenario"),
            "structured_prd": None,
            "score_report": mock_report,
            "gate_decision": None,
            "retry_count": 0,
            "error_logs": [],
            "current_stage": "scoring",
            "fallback_activated": False,
            "execution_times": {},
        }

        result = hard_gate_node(state)

        assert result["gate_decision"] is True
        assert "gate" in result["execution_times"]

    @patch("src.reqgate.workflow.graph.HardGate")
    def test_rejects_bad_score(self, mock_gate_class: MagicMock) -> None:
        """Test gate rejects for bad score."""
        mock_gate = MagicMock()
        mock_gate.decide.return_value = "REJECT"
        mock_gate_class.return_value = mock_gate

        mock_report = MagicMock(spec=TicketScoreReport)

        state: AgentState = {
            "packet": make_packet("Test requirement for gate reject scenario"),
            "structured_prd": None,
            "score_report": mock_report,
            "gate_decision": None,
            "retry_count": 0,
            "error_logs": [],
            "current_stage": "scoring",
            "fallback_activated": False,
            "execution_times": {},
        }

        result = hard_gate_node(state)

        assert result["gate_decision"] is False

    def test_rejects_when_no_score_report(self) -> None:
        """Test gate rejects when no score report."""
        state: AgentState = {
            "packet": make_packet("Test requirement without score report"),
            "structured_prd": None,
            "score_report": None,
            "gate_decision": None,
            "retry_count": 0,
            "error_logs": [],
            "current_stage": "scoring",
            "fallback_activated": False,
            "execution_times": {},
        }

        result = hard_gate_node(state)

        assert result["gate_decision"] is False
        assert "no score report" in result["error_logs"][0].lower()


class TestCreateWorkflow:
    """Tests for create_workflow function."""

    def test_creates_with_defaults(self) -> None:
        """Test workflow creation with default config."""
        workflow = create_workflow()

        # Should compile without error
        assert workflow is not None

    def test_creates_minimal_workflow(self) -> None:
        """Test minimal workflow without guardrail or structuring."""
        config = WorkflowConfig(
            enable_guardrail=False,
            enable_structuring=False,
            enable_fallback=False,
        )

        workflow = create_workflow(config)

        assert workflow is not None

    def test_creates_guardrail_only_workflow(self) -> None:
        """Test workflow with guardrail but no structuring."""
        config = WorkflowConfig(
            enable_guardrail=True,
            enable_structuring=False,
            enable_fallback=False,
        )

        workflow = create_workflow(config)

        assert workflow is not None

    def test_creates_full_workflow(self) -> None:
        """Test full workflow with all features."""
        config = WorkflowConfig(
            enable_guardrail=True,
            enable_structuring=True,
            enable_fallback=True,
        )

        workflow = create_workflow(config)

        assert workflow is not None


class TestRunWorkflow:
    """Tests for run_workflow function."""

    @patch("src.reqgate.workflow.graph.create_workflow")
    def test_runs_successfully(self, mock_create: MagicMock) -> None:
        """Test successful workflow execution."""
        mock_workflow = MagicMock()
        mock_workflow.invoke.return_value = {
            "packet": MagicMock(),
            "structured_prd": None,
            "score_report": MagicMock(),
            "gate_decision": True,
            "retry_count": 0,
            "error_logs": [],
            "current_stage": "gate",
            "fallback_activated": False,
            "execution_times": {},
        }
        mock_create.return_value = mock_workflow

        packet = make_packet("Test requirement for workflow execution")

        result = run_workflow(packet)

        assert result["gate_decision"] is True
        mock_workflow.invoke.assert_called_once()

    @patch("src.reqgate.workflow.graph.create_workflow")
    def test_passes_config(self, mock_create: MagicMock) -> None:
        """Test that config is passed to workflow."""
        mock_workflow = MagicMock()
        mock_workflow.invoke.return_value = {
            "packet": MagicMock(),
            "structured_prd": None,
            "score_report": MagicMock(),
            "gate_decision": False,
            "retry_count": 0,
            "error_logs": [],
            "current_stage": "gate",
            "fallback_activated": False,
            "execution_times": {},
        }
        mock_create.return_value = mock_workflow

        config = WorkflowConfig(enable_guardrail=False)
        packet = make_packet("Test requirement for config passing")

        run_workflow(packet, config)

        mock_create.assert_called_once_with(config)

    @patch("src.reqgate.workflow.graph.create_workflow")
    def test_reraises_guardrail_rejection(self, mock_create: MagicMock) -> None:
        """Test that GuardrailRejectionError is re-raised."""
        mock_workflow = MagicMock()
        mock_workflow.invoke.side_effect = GuardrailRejectionError(
            message="Input too short",
            rejection_reason="too_short",
        )
        mock_create.return_value = mock_workflow

        packet = make_packet("Short but valid packet text for rejection test")

        with pytest.raises(GuardrailRejectionError):
            run_workflow(packet)

    @patch("src.reqgate.workflow.graph.create_workflow")
    def test_wraps_other_errors(self, mock_create: MagicMock) -> None:
        """Test that other errors are wrapped in WorkflowExecutionError."""
        mock_workflow = MagicMock()
        mock_workflow.invoke.side_effect = RuntimeError("Unexpected error")
        mock_create.return_value = mock_workflow

        packet = make_packet("Test requirement for error wrapping")

        with pytest.raises(WorkflowExecutionError) as exc_info:
            run_workflow(packet)

        assert "Unexpected error" in str(exc_info.value)


class TestWorkflowIntegration:
    """Integration tests for the workflow."""

    @patch("src.reqgate.workflow.graph.ScoringAgent")
    @patch("src.reqgate.workflow.graph.HardGate")
    def test_minimal_workflow_integration(
        self,
        mock_gate_class: MagicMock,
        mock_agent_class: MagicMock,
    ) -> None:
        """Test minimal workflow (scoring + gate only)."""
        # Setup mocks
        mock_report = MagicMock(spec=TicketScoreReport)
        mock_report.total_score = 85
        mock_agent = MagicMock()
        mock_agent.score.return_value = mock_report
        mock_agent_class.return_value = mock_agent

        mock_gate = MagicMock()
        mock_gate.decide.return_value = "PASS"
        mock_gate_class.return_value = mock_gate

        # Run workflow
        config = WorkflowConfig(
            enable_guardrail=False,
            enable_structuring=False,
            enable_fallback=False,
        )
        packet = make_packet("Test requirement text for integration testing")

        result = run_workflow(packet, config)

        assert result["gate_decision"] is True
        assert result["score_report"] is mock_report
        mock_agent.score.assert_called_once()
        mock_gate.decide.assert_called_once()
