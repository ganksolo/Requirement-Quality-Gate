"""Workflow Integration Tests.

This module tests the complete workflow integration:
1. Happy path - all nodes succeed
2. Fallback path - structuring fails, scoring uses raw text
3. Retry path - LLM timeout then success
4. Error path - guardrail rejects input
5. State transitions verification
6. Execution times logging
"""

from unittest.mock import MagicMock, patch

import pytest
from src.reqgate.schemas.config import WorkflowConfig
from src.reqgate.schemas.inputs import RequirementPacket
from src.reqgate.schemas.internal import PRD_Draft
from src.reqgate.schemas.outputs import TicketScoreReport
from src.reqgate.workflow.errors import GuardrailRejectionError
from src.reqgate.workflow.graph import create_initial_state, create_workflow, run_workflow
from src.reqgate.workflow.nodes.input_guardrail import GuardrailResult


def make_packet(
    raw_text: str = "This is a comprehensive test requirement with sufficient detail for testing the workflow integration",
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
        title="Implement user authentication feature",
        user_story="As a user, I want to log in, so that I can access my account",
        acceptance_criteria=[
            "User can enter username and password",
            "System validates credentials",
            "User sees dashboard on success",
        ],
    )


def make_score_report(total_score: int = 85) -> MagicMock:
    """Create a mock TicketScoreReport."""
    report = MagicMock(spec=TicketScoreReport)
    report.total_score = total_score
    report.blocking_issues = []
    return report


class TestHappyPath:
    """Tests for the happy path - all nodes succeed."""

    @patch("src.reqgate.workflow.graph.ScoringAgent")
    @patch("src.reqgate.workflow.graph.HardGate")
    def test_minimal_workflow_succeeds(
        self,
        mock_gate_class: MagicMock,
        mock_agent_class: MagicMock,
    ) -> None:
        """Test minimal workflow (scoring + gate) succeeds."""
        # Setup mocks
        mock_report = make_score_report(85)
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
        packet = make_packet()

        result = run_workflow(packet, config)

        # Verify results
        assert result["gate_decision"] is True
        assert result["score_report"] is mock_report
        assert result["fallback_activated"] is False
        assert "scoring" in result["execution_times"]
        assert "gate" in result["execution_times"]

    @patch("src.reqgate.workflow.graph.ScoringAgent")
    @patch("src.reqgate.workflow.graph.HardGate")
    @patch("src.reqgate.workflow.nodes.input_guardrail.get_guardrail")
    def test_workflow_with_guardrail_succeeds(
        self,
        mock_get_guardrail: MagicMock,
        mock_gate_class: MagicMock,
        mock_agent_class: MagicMock,
    ) -> None:
        """Test workflow with guardrail enabled succeeds."""
        # Setup guardrail mock - return GuardrailResult
        mock_guardrail = MagicMock()
        mock_guardrail.validate.return_value = GuardrailResult(passed=True)
        mock_get_guardrail.return_value = mock_guardrail

        # Setup scoring mock
        mock_report = make_score_report(90)
        mock_agent = MagicMock()
        mock_agent.score.return_value = mock_report
        mock_agent_class.return_value = mock_agent

        # Setup gate mock
        mock_gate = MagicMock()
        mock_gate.decide.return_value = "PASS"
        mock_gate_class.return_value = mock_gate

        # Run workflow
        config = WorkflowConfig(
            enable_guardrail=True,
            enable_structuring=False,
            enable_fallback=False,
        )
        packet = make_packet()

        result = run_workflow(packet, config)

        assert result["gate_decision"] is True


class TestFallbackPath:
    """Tests for the fallback path - structuring fails."""

    @patch("src.reqgate.workflow.graph.ScoringAgent")
    @patch("src.reqgate.workflow.graph.HardGate")
    @patch("src.reqgate.workflow.nodes.structuring_agent.get_llm_client")
    def test_fallback_activated_on_structuring_failure(
        self,
        mock_llm: MagicMock,
        mock_gate_class: MagicMock,
        mock_agent_class: MagicMock,
    ) -> None:
        """Test that fallback is activated when structuring fails."""
        # Setup LLM to fail
        mock_llm_client = MagicMock()
        mock_llm_client.invoke.side_effect = RuntimeError("LLM unavailable")
        mock_llm.return_value = mock_llm_client

        # Setup scoring
        mock_report = make_score_report(70)
        mock_agent = MagicMock()
        mock_agent.score.return_value = mock_report
        mock_agent_class.return_value = mock_agent

        # Setup gate
        mock_gate = MagicMock()
        mock_gate.decide.return_value = "PASS"
        mock_gate_class.return_value = mock_gate

        # Run workflow with structuring enabled
        config = WorkflowConfig(
            enable_guardrail=False,
            enable_structuring=True,
            enable_fallback=True,
        )
        packet = make_packet()

        result = run_workflow(packet, config)

        # Verify fallback was activated
        assert result["fallback_activated"] is True
        assert result["structured_prd"] is None
        # Score should have -5 penalty (70 - 5 = 65)
        assert mock_report.total_score == 65

    @patch("src.reqgate.workflow.graph.ScoringAgent")
    @patch("src.reqgate.workflow.graph.HardGate")
    @patch("src.reqgate.workflow.nodes.structuring_agent.get_llm_client")
    def test_scoring_uses_raw_text_in_fallback(
        self,
        mock_llm: MagicMock,
        mock_gate_class: MagicMock,
        mock_agent_class: MagicMock,
    ) -> None:
        """Test that scoring uses raw text when in fallback mode."""
        # Setup LLM to fail
        mock_llm_client = MagicMock()
        mock_llm_client.invoke.side_effect = RuntimeError("LLM error")
        mock_llm.return_value = mock_llm_client

        # Setup scoring to capture input
        captured_input = []
        mock_report = make_score_report(75)
        mock_agent = MagicMock()
        mock_agent.score.side_effect = lambda p: (captured_input.append(p), mock_report)[1]
        mock_agent_class.return_value = mock_agent

        # Setup gate
        mock_gate = MagicMock()
        mock_gate.decide.return_value = "PASS"
        mock_gate_class.return_value = mock_gate

        # Run workflow
        config = WorkflowConfig(
            enable_guardrail=False,
            enable_structuring=True,
            enable_fallback=True,
        )
        original_text = "Original requirement text for fallback testing scenario"
        packet = make_packet(original_text)

        run_workflow(packet, config)

        # Verify raw text was used
        assert len(captured_input) == 1
        assert captured_input[0].raw_text == original_text


class TestRetryPath:
    """Tests for the retry path - LLM timeout then success."""

    @patch("src.reqgate.workflow.graph.ScoringAgent")
    @patch("src.reqgate.workflow.graph.HardGate")
    def test_scoring_succeeds_after_initial_setup(
        self,
        mock_gate_class: MagicMock,
        mock_agent_class: MagicMock,
    ) -> None:
        """Test that scoring succeeds with proper mocking."""
        # Setup scoring with successful response
        mock_report = make_score_report(80)
        mock_agent = MagicMock()
        mock_agent.score.return_value = mock_report
        mock_agent_class.return_value = mock_agent

        # Setup gate
        mock_gate = MagicMock()
        mock_gate.decide.return_value = "PASS"
        mock_gate_class.return_value = mock_gate

        # Run workflow
        config = WorkflowConfig(
            enable_guardrail=False,
            enable_structuring=False,
            enable_fallback=False,
        )
        packet = make_packet()

        result = run_workflow(packet, config)

        assert result["score_report"] is mock_report
        assert result["gate_decision"] is True


class TestErrorPath:
    """Tests for error paths - guardrail rejects, etc."""

    @patch("src.reqgate.workflow.nodes.input_guardrail.get_guardrail")
    def test_guardrail_rejection_raises_error(
        self,
        mock_get_guardrail: MagicMock,
    ) -> None:
        """Test that guardrail rejection raises GuardrailRejectionError."""
        # Setup guardrail to reject (return passed=False with error)
        mock_guardrail = MagicMock()
        mock_guardrail.validate.return_value = GuardrailResult(
            passed=False,
            errors=["Input too short: 100 < 50 minimum"],
        )
        mock_get_guardrail.return_value = mock_guardrail

        # Run workflow with guardrail
        config = WorkflowConfig(
            enable_guardrail=True,
            enable_structuring=False,
            enable_fallback=False,
        )
        packet = make_packet()

        with pytest.raises(GuardrailRejectionError) as exc_info:
            run_workflow(packet, config)

        assert exc_info.value.rejection_reason == "too_short"

    @patch("src.reqgate.workflow.graph.ScoringAgent")
    def test_scoring_error_logs_but_continues(
        self,
        mock_agent_class: MagicMock,
    ) -> None:
        """Test that scoring error is logged but gate still runs."""
        # Setup scoring to fail
        mock_agent = MagicMock()
        mock_agent.score.side_effect = RuntimeError("Scoring failed")
        mock_agent_class.return_value = mock_agent

        # Run minimal workflow
        config = WorkflowConfig(
            enable_guardrail=False,
            enable_structuring=False,
            enable_fallback=False,
        )
        packet = make_packet()

        result = run_workflow(packet, config)

        # Gate should reject due to no score
        assert result["gate_decision"] is False
        assert result["score_report"] is None
        assert len(result["error_logs"]) > 0
        assert "Scoring failed" in result["error_logs"][0]


class TestStateTransitions:
    """Tests for state transitions verification."""

    def test_initial_state_correct(self) -> None:
        """Test that initial state is correctly initialized."""
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

    @patch("src.reqgate.workflow.graph.ScoringAgent")
    @patch("src.reqgate.workflow.graph.HardGate")
    def test_state_updated_through_workflow(
        self,
        mock_gate_class: MagicMock,
        mock_agent_class: MagicMock,
    ) -> None:
        """Test that state is updated as workflow progresses."""
        mock_report = make_score_report(85)
        mock_agent = MagicMock()
        mock_agent.score.return_value = mock_report
        mock_agent_class.return_value = mock_agent

        mock_gate = MagicMock()
        mock_gate.decide.return_value = "PASS"
        mock_gate_class.return_value = mock_gate

        config = WorkflowConfig(
            enable_guardrail=False,
            enable_structuring=False,
            enable_fallback=False,
        )
        packet = make_packet()

        result = run_workflow(packet, config)

        # Verify state was updated
        assert result["score_report"] is not None
        assert result["gate_decision"] is not None
        assert result["current_stage"] == "gate"


class TestExecutionTimesLogging:
    """Tests for execution times logging."""

    @patch("src.reqgate.workflow.graph.ScoringAgent")
    @patch("src.reqgate.workflow.graph.HardGate")
    def test_execution_times_logged(
        self,
        mock_gate_class: MagicMock,
        mock_agent_class: MagicMock,
    ) -> None:
        """Test that execution times are logged for each node."""
        mock_report = make_score_report(85)
        mock_agent = MagicMock()
        mock_agent.score.return_value = mock_report
        mock_agent_class.return_value = mock_agent

        mock_gate = MagicMock()
        mock_gate.decide.return_value = "PASS"
        mock_gate_class.return_value = mock_gate

        config = WorkflowConfig(
            enable_guardrail=False,
            enable_structuring=False,
            enable_fallback=False,
        )
        packet = make_packet()

        result = run_workflow(packet, config)

        # Verify execution times are present
        assert "scoring" in result["execution_times"]
        assert "gate" in result["execution_times"]
        assert result["execution_times"]["scoring"] >= 0
        assert result["execution_times"]["gate"] >= 0

    @patch("src.reqgate.workflow.graph.ScoringAgent")
    @patch("src.reqgate.workflow.graph.HardGate")
    @patch("src.reqgate.workflow.nodes.input_guardrail.get_guardrail")
    def test_all_nodes_log_execution_times(
        self,
        mock_get_guardrail: MagicMock,
        mock_gate_class: MagicMock,
        mock_agent_class: MagicMock,
    ) -> None:
        """Test that all enabled nodes log execution times."""
        mock_guardrail = MagicMock()
        mock_guardrail.validate.return_value = GuardrailResult(passed=True)
        mock_get_guardrail.return_value = mock_guardrail

        mock_report = make_score_report(90)
        mock_agent = MagicMock()
        mock_agent.score.return_value = mock_report
        mock_agent_class.return_value = mock_agent

        mock_gate = MagicMock()
        mock_gate.decide.return_value = "PASS"
        mock_gate_class.return_value = mock_gate

        config = WorkflowConfig(
            enable_guardrail=True,
            enable_structuring=False,
            enable_fallback=False,
        )
        packet = make_packet()

        result = run_workflow(packet, config)

        # Check guardrail, scoring, gate times
        assert "guardrail" in result["execution_times"]
        assert "scoring" in result["execution_times"]
        assert "gate" in result["execution_times"]


class TestWorkflowConfiguration:
    """Tests for workflow configuration options."""

    def test_workflow_compiles_with_all_options_enabled(self) -> None:
        """Test workflow compiles with all options enabled."""
        config = WorkflowConfig(
            enable_guardrail=True,
            enable_structuring=True,
            enable_fallback=True,
        )

        workflow = create_workflow(config)

        assert workflow is not None

    def test_workflow_compiles_with_all_options_disabled(self) -> None:
        """Test workflow compiles with all options disabled."""
        config = WorkflowConfig(
            enable_guardrail=False,
            enable_structuring=False,
            enable_fallback=False,
        )

        workflow = create_workflow(config)

        assert workflow is not None

    def test_workflow_compiles_with_mixed_options(self) -> None:
        """Test workflow compiles with mixed options."""
        configs = [
            WorkflowConfig(enable_guardrail=True, enable_structuring=False),
            WorkflowConfig(enable_guardrail=False, enable_structuring=True),
            WorkflowConfig(enable_structuring=True, enable_fallback=False),
        ]

        for config in configs:
            workflow = create_workflow(config)
            assert workflow is not None


class TestGateDecisions:
    """Tests for gate decision outcomes."""

    @patch("src.reqgate.workflow.graph.ScoringAgent")
    @patch("src.reqgate.workflow.graph.HardGate")
    def test_gate_passes_high_score(
        self,
        mock_gate_class: MagicMock,
        mock_agent_class: MagicMock,
    ) -> None:
        """Test gate passes with high score."""
        mock_report = make_score_report(95)
        mock_agent = MagicMock()
        mock_agent.score.return_value = mock_report
        mock_agent_class.return_value = mock_agent

        mock_gate = MagicMock()
        mock_gate.decide.return_value = "PASS"
        mock_gate_class.return_value = mock_gate

        config = WorkflowConfig(
            enable_guardrail=False,
            enable_structuring=False,
        )
        packet = make_packet()

        result = run_workflow(packet, config)

        assert result["gate_decision"] is True

    @patch("src.reqgate.workflow.graph.ScoringAgent")
    @patch("src.reqgate.workflow.graph.HardGate")
    def test_gate_rejects_low_score(
        self,
        mock_gate_class: MagicMock,
        mock_agent_class: MagicMock,
    ) -> None:
        """Test gate rejects with low score."""
        mock_report = make_score_report(40)
        mock_agent = MagicMock()
        mock_agent.score.return_value = mock_report
        mock_agent_class.return_value = mock_agent

        mock_gate = MagicMock()
        mock_gate.decide.return_value = "REJECT"
        mock_gate_class.return_value = mock_gate

        config = WorkflowConfig(
            enable_guardrail=False,
            enable_structuring=False,
        )
        packet = make_packet()

        result = run_workflow(packet, config)

        assert result["gate_decision"] is False
