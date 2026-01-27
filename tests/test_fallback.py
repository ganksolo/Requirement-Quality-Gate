"""Tests for Fallback Mechanism.

This module tests the fallback behavior when structuring fails:
1. Fallback is activated when structured_prd is None
2. Scoring continues using raw_text
3. fallback_activated flag is set correctly
4. Score penalty (-5 points) is applied in fallback mode
"""

from unittest.mock import MagicMock, patch

from src.reqgate.schemas.config import WorkflowConfig
from src.reqgate.schemas.inputs import RequirementPacket
from src.reqgate.schemas.internal import AgentState, PRD_Draft
from src.reqgate.schemas.outputs import TicketScoreReport
from src.reqgate.workflow.graph import (
    _prepare_scoring_input,
    activate_fallback,
    create_initial_state,
    format_prd_for_scoring,
    run_workflow,
    scoring_node,
    should_fallback,
)


def make_packet(
    raw_text: str = "This is a test requirement with sufficient content for testing",
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
        acceptance_criteria=["User can enter credentials", "User sees dashboard"],
    )


def make_state(
    packet: RequirementPacket | None = None,
    structured_prd: PRD_Draft | None = None,
    fallback_activated: bool = False,
) -> AgentState:
    """Create a test AgentState."""
    return AgentState(
        packet=packet or make_packet(),
        structured_prd=structured_prd,
        score_report=None,
        gate_decision=None,
        retry_count=0,
        error_logs=[],
        current_stage="init",
        fallback_activated=fallback_activated,
        execution_times={},
    )


class TestFallbackActivation:
    """Tests for fallback activation on structuring failure."""

    def test_should_fallback_returns_fallback_when_no_prd(self) -> None:
        """Test that should_fallback returns 'fallback_scoring' when no structured PRD."""
        state = make_state(structured_prd=None)

        result = should_fallback(state)

        assert result == "fallback_scoring"

    def test_should_fallback_returns_scoring_when_prd_available(self) -> None:
        """Test that should_fallback returns 'structure_check' when PRD is available."""
        state = make_state(structured_prd=make_prd())

        result = should_fallback(state)

        assert result == "structure_check"

    def test_activate_fallback_sets_flag(self) -> None:
        """Test that activate_fallback sets the fallback_activated flag."""
        state = make_state(fallback_activated=False)

        result = activate_fallback(state)

        assert result["fallback_activated"] is True

    def test_activate_fallback_logs_message(self) -> None:
        """Test that activate_fallback logs the activation."""
        state = make_state()

        result = activate_fallback(state)

        assert len(result["error_logs"]) > 0
        assert "Fallback activated" in result["error_logs"][0]


class TestScoringContinuesWithRawText:
    """Tests for scoring continuation with raw text in fallback mode."""

    def test_prepare_scoring_input_uses_raw_packet_when_no_prd(self) -> None:
        """Test that _prepare_scoring_input returns original packet when no PRD."""
        packet = make_packet("Original requirement text for fallback")

        result = _prepare_scoring_input(packet, structured_prd=None)

        assert result is packet  # Same object
        assert result.raw_text == "Original requirement text for fallback"

    def test_prepare_scoring_input_uses_formatted_prd_when_available(self) -> None:
        """Test that _prepare_scoring_input formats PRD when available."""
        packet = make_packet("Original requirement text")
        prd = make_prd()

        result = _prepare_scoring_input(packet, structured_prd=prd)

        assert result is not packet  # Different object
        assert "# Implement user authentication feature" in result.raw_text
        assert "## Acceptance Criteria" in result.raw_text

    @patch("src.reqgate.workflow.graph.ScoringAgent")
    def test_scoring_node_processes_raw_text_in_fallback(self, mock_agent_class: MagicMock) -> None:
        """Test that scoring node processes raw text when fallback is active."""
        mock_report = MagicMock(spec=TicketScoreReport)
        mock_report.total_score = 70
        mock_agent = MagicMock()
        mock_agent.score.return_value = mock_report
        mock_agent_class.return_value = mock_agent

        state = make_state(
            packet=make_packet("Fallback mode requirement text here"),
            structured_prd=None,
            fallback_activated=True,
        )

        result = scoring_node(state)

        # Scoring should complete even without structured PRD
        assert result["score_report"] is mock_report
        mock_agent.score.assert_called_once()

        # Verify raw_text was used (original packet)
        call_args = mock_agent.score.call_args[0][0]
        assert "Fallback mode requirement text" in call_args.raw_text


class TestFallbackFlagCorrectness:
    """Tests for fallback_activated flag correctness."""

    def test_initial_state_has_fallback_false(self) -> None:
        """Test that initial state has fallback_activated=False."""
        packet = make_packet()
        state = create_initial_state(packet)

        assert state["fallback_activated"] is False

    def test_fallback_flag_preserved_through_scoring(self) -> None:
        """Test that fallback flag is preserved through scoring node."""
        state = make_state(fallback_activated=True)

        with patch("src.reqgate.workflow.graph.ScoringAgent") as mock_class:
            mock_report = MagicMock(spec=TicketScoreReport)
            mock_report.total_score = 80
            mock_agent = MagicMock()
            mock_agent.score.return_value = mock_report
            mock_class.return_value = mock_agent

            result = scoring_node(state)

        assert result["fallback_activated"] is True

    def test_fallback_flag_false_when_prd_available(self) -> None:
        """Test that fallback flag stays False when PRD is available."""
        state = make_state(structured_prd=make_prd(), fallback_activated=False)

        with patch("src.reqgate.workflow.graph.ScoringAgent") as mock_class:
            mock_report = MagicMock(spec=TicketScoreReport)
            mock_report.total_score = 90
            mock_agent = MagicMock()
            mock_agent.score.return_value = mock_report
            mock_class.return_value = mock_agent

            result = scoring_node(state)

        assert result["fallback_activated"] is False


class TestScorePenalty:
    """Tests for score penalty in fallback mode."""

    @patch("src.reqgate.workflow.graph.ScoringAgent")
    def test_score_penalty_applied_in_fallback_mode(self, mock_agent_class: MagicMock) -> None:
        """Test that -5 score penalty is applied in fallback mode."""
        mock_report = MagicMock(spec=TicketScoreReport)
        mock_report.total_score = 80  # Original score
        mock_agent = MagicMock()
        mock_agent.score.return_value = mock_report
        mock_agent_class.return_value = mock_agent

        state = make_state(fallback_activated=True)

        scoring_node(state)

        # Score should be reduced by 5
        assert mock_report.total_score == 75

    @patch("src.reqgate.workflow.graph.ScoringAgent")
    def test_no_penalty_when_not_in_fallback(self, mock_agent_class: MagicMock) -> None:
        """Test that no penalty is applied when not in fallback mode."""
        mock_report = MagicMock(spec=TicketScoreReport)
        mock_report.total_score = 80  # Original score
        mock_agent = MagicMock()
        mock_agent.score.return_value = mock_report
        mock_agent_class.return_value = mock_agent

        state = make_state(fallback_activated=False)

        scoring_node(state)

        # Score should not be changed
        assert mock_report.total_score == 80

    @patch("src.reqgate.workflow.graph.ScoringAgent")
    def test_penalty_does_not_go_below_zero(self, mock_agent_class: MagicMock) -> None:
        """Test that penalty doesn't cause negative score."""
        mock_report = MagicMock(spec=TicketScoreReport)
        mock_report.total_score = 3  # Low score
        mock_agent = MagicMock()
        mock_agent.score.return_value = mock_report
        mock_agent_class.return_value = mock_agent

        state = make_state(fallback_activated=True)

        scoring_node(state)

        # Score should be 0, not negative
        assert mock_report.total_score == 0

    @patch("src.reqgate.workflow.graph.ScoringAgent")
    def test_penalty_boundary_case(self, mock_agent_class: MagicMock) -> None:
        """Test penalty boundary case (score exactly 5)."""
        mock_report = MagicMock(spec=TicketScoreReport)
        mock_report.total_score = 5
        mock_agent = MagicMock()
        mock_agent.score.return_value = mock_report
        mock_agent_class.return_value = mock_agent

        state = make_state(fallback_activated=True)

        scoring_node(state)

        assert mock_report.total_score == 0


class TestFormatPRDForScoring:
    """Tests for format_prd_for_scoring helper function."""

    def test_formats_title(self) -> None:
        """Test that title is formatted as H1."""
        prd = make_prd()
        result = format_prd_for_scoring(prd)
        assert "# Implement user authentication feature" in result

    def test_formats_user_story(self) -> None:
        """Test that user story section is included."""
        prd = make_prd()
        result = format_prd_for_scoring(prd)
        assert "## User Story" in result
        assert "As a user, I want to log in" in result

    def test_formats_acceptance_criteria(self) -> None:
        """Test that acceptance criteria are numbered."""
        prd = make_prd()
        result = format_prd_for_scoring(prd)
        assert "## Acceptance Criteria" in result
        assert "1. User can enter credentials" in result
        assert "2. User sees dashboard" in result

    def test_includes_edge_cases_when_present(self) -> None:
        """Test that edge cases are included when present."""
        prd = PRD_Draft(
            title="Implement feature with edge cases",
            user_story="As a user, I want X, so that Y",
            acceptance_criteria=["AC1"],
            edge_cases=["Edge case 1", "Edge case 2"],
        )
        result = format_prd_for_scoring(prd)
        assert "## Edge Cases" in result
        assert "- Edge case 1" in result
        assert "- Edge case 2" in result

    def test_excludes_edge_cases_when_empty(self) -> None:
        """Test that edge cases section is excluded when empty."""
        prd = PRD_Draft(
            title="Implement feature without edge cases",
            user_story="As a user, I want X, so that Y",
            acceptance_criteria=["AC1"],
            edge_cases=[],
        )
        result = format_prd_for_scoring(prd)
        assert "## Edge Cases" not in result

    def test_includes_missing_info_when_present(self) -> None:
        """Test that missing info is included when present."""
        prd = PRD_Draft(
            title="Implement feature with gaps",
            user_story="As a user, I want X, so that Y",
            acceptance_criteria=["AC1"],
            missing_info=["Gap 1", "Gap 2"],
        )
        result = format_prd_for_scoring(prd)
        assert "## Identified Gaps" in result
        assert "- Gap 1" in result
        assert "- Gap 2" in result


class TestFallbackWorkflowIntegration:
    """Integration tests for fallback workflow path."""

    @patch("src.reqgate.workflow.graph.ScoringAgent")
    @patch("src.reqgate.workflow.graph.HardGate")
    @patch("src.reqgate.workflow.nodes.structuring_agent.LLMClientWithRetry")
    def test_full_fallback_path(
        self,
        mock_llm: MagicMock,
        mock_gate_class: MagicMock,
        mock_agent_class: MagicMock,
    ) -> None:
        """Test complete workflow with fallback path."""
        # Setup structuring to fail (returns None)
        mock_llm_client = MagicMock()
        mock_llm_client.invoke.side_effect = RuntimeError("LLM failed")
        mock_llm.return_value = mock_llm_client

        # Setup scoring to succeed
        mock_report = MagicMock(spec=TicketScoreReport)
        mock_report.total_score = 70
        mock_agent = MagicMock()
        mock_agent.score.return_value = mock_report
        mock_agent_class.return_value = mock_agent

        # Setup gate to pass
        mock_gate = MagicMock()
        mock_gate.decide.return_value = "PASS"
        mock_gate_class.return_value = mock_gate

        # Run workflow with structuring enabled (will fail and fallback)
        config = WorkflowConfig(
            enable_guardrail=False,
            enable_structuring=True,
            enable_fallback=True,
        )
        packet = make_packet("Test requirement for fallback integration test")

        result = run_workflow(packet, config)

        # Verify fallback was activated
        assert result["fallback_activated"] is True
        # Score should have penalty applied (70 - 5 = 65)
        assert mock_report.total_score == 65
        # Gate should still make decision
        assert result["gate_decision"] is True

    @patch("src.reqgate.workflow.graph.ScoringAgent")
    @patch("src.reqgate.workflow.graph.HardGate")
    def test_no_fallback_when_structuring_succeeds(
        self,
        mock_gate_class: MagicMock,
        mock_agent_class: MagicMock,
    ) -> None:
        """Test that fallback is not activated when structuring succeeds."""
        # Setup scoring
        mock_report = MagicMock(spec=TicketScoreReport)
        mock_report.total_score = 85
        mock_agent = MagicMock()
        mock_agent.score.return_value = mock_report
        mock_agent_class.return_value = mock_agent

        # Setup gate
        mock_gate = MagicMock()
        mock_gate.decide.return_value = "PASS"
        mock_gate_class.return_value = mock_gate

        # Run minimal workflow (no structuring = no fallback path)
        config = WorkflowConfig(
            enable_guardrail=False,
            enable_structuring=False,
            enable_fallback=False,
        )
        packet = make_packet("Test requirement without fallback")

        result = run_workflow(packet, config)

        # Verify no fallback
        assert result["fallback_activated"] is False
        # Score should be unchanged
        assert mock_report.total_score == 85
