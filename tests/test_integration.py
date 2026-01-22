"""Integration tests for the complete scoring flow."""

from unittest.mock import MagicMock, patch

import pytest
from src.reqgate.agents.scoring import ScoringAgent
from src.reqgate.gates.decision import HardGate
from src.reqgate.schemas.inputs import RequirementPacket
from src.reqgate.schemas.outputs import ReviewIssue, TicketScoreReport


class TestEndToEndFlow:
    """Test the complete flow: Input → Scoring → Gate."""

    @pytest.fixture
    def good_requirement(self) -> RequirementPacket:
        """Create a well-written requirement packet."""
        return RequirementPacket(
            raw_text="""
            # Feature: User Login with OAuth

            ## Description
            As a user, I want to login using my Google account so that I don't need to remember another password.

            ## Acceptance Criteria
            - Given I am on the login page, when I click "Login with Google", then I am redirected to Google OAuth
            - Given I complete Google OAuth, when I am redirected back, then I am logged in and see my dashboard
            - Given I am already logged in, when I click "Logout", then my session is terminated

            ## Technical Notes
            - Use Google OAuth 2.0
            - Store refresh token securely
            - Session timeout: 24 hours
            """,
            source_type="Jira_Ticket",
            project_key="AUTH",
            priority="P1",
            ticket_type="Feature",
        )

    @pytest.fixture
    def bad_requirement(self) -> RequirementPacket:
        """Create a poorly-written requirement packet (missing AC)."""
        return RequirementPacket(
            raw_text="""
            # Feature: User Login

            Make login work better. It should be fast and nice.
            Users should be able to login somehow.
            """,
            source_type="Jira_Ticket",
            project_key="AUTH",
            priority="P2",
            ticket_type="Feature",
        )

    @pytest.fixture
    def mock_passing_llm_response(self) -> str:
        """LLM response for a passing requirement."""
        return TicketScoreReport(
            total_score=85,
            ready_for_review=True,
            dimension_scores={"completeness": 90, "logic": 80, "clarity": 85},
            blocking_issues=[],
            non_blocking_issues=[],
            summary_markdown="## 评分结果\n\n总分: 85/100 ✅\n\n需求描述清晰，验收标准完整。",
        ).model_dump_json()

    @pytest.fixture
    def mock_failing_llm_response(self) -> str:
        """LLM response for a failing requirement."""
        return TicketScoreReport(
            total_score=35,
            ready_for_review=False,
            dimension_scores={"completeness": 20, "logic": 40, "clarity": 45},
            blocking_issues=[
                ReviewIssue(
                    severity="BLOCKER",
                    category="MISSING_AC",
                    description="缺少验收标准",
                    suggestion="请添加至少 3 条 Given/When/Then 格式的验收标准",
                ),
                ReviewIssue(
                    severity="BLOCKER",
                    category="AMBIGUITY",
                    description="描述过于模糊，使用了'更好'、'快速'等无法量化的词汇",
                    suggestion="请明确具体的性能指标，如响应时间 < 500ms",
                ),
            ],
            non_blocking_issues=[],
            summary_markdown="## 评分结果\n\n总分: 35/100 ❌\n\n需求缺少验收标准，描述不够具体。",
        ).model_dump_json()

    @patch("src.reqgate.agents.scoring.get_llm_client")
    @patch("src.reqgate.agents.scoring.get_rubric_loader")
    def test_good_requirement_passes_gate(
        self,
        mock_rubric_loader,
        mock_llm_client,
        good_requirement,
        mock_passing_llm_response,
    ):
        """Test that a good requirement passes the gate."""
        # Setup rubric mock
        mock_rubric_instance = MagicMock()
        mock_rubric_instance.get_scenario_config.return_value = {
            "threshold": 60,
            "weights": {"completeness": 0.4, "logic": 0.3, "clarity": 0.3},
            "required_fields": [],
            "negative_patterns": [],
        }
        mock_rubric_loader.return_value = mock_rubric_instance

        # Setup LLM mock
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = mock_passing_llm_response
        mock_llm_client.return_value = mock_llm_instance

        # Execute flow
        agent = ScoringAgent()
        report = agent.score(good_requirement)

        gate = HardGate()
        decision = gate.decide(report, good_requirement.ticket_type)

        # Assertions
        assert report.total_score == 85
        assert report.ready_for_review is True
        assert len(report.blocking_issues) == 0
        assert decision == "PASS"

    @patch("src.reqgate.agents.scoring.get_llm_client")
    @patch("src.reqgate.agents.scoring.get_rubric_loader")
    def test_bad_requirement_fails_gate(
        self,
        mock_rubric_loader,
        mock_llm_client,
        bad_requirement,
        mock_failing_llm_response,
    ):
        """Test that a bad requirement fails the gate."""
        # Setup rubric mock
        mock_rubric_instance = MagicMock()
        mock_rubric_instance.get_scenario_config.return_value = {
            "threshold": 60,
            "weights": {"completeness": 0.4, "logic": 0.3, "clarity": 0.3},
            "required_fields": [],
            "negative_patterns": [],
        }
        mock_rubric_loader.return_value = mock_rubric_instance

        # Setup LLM mock
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = mock_failing_llm_response
        mock_llm_client.return_value = mock_llm_instance

        # Execute flow
        agent = ScoringAgent()
        report = agent.score(bad_requirement)

        gate = HardGate()
        decision = gate.decide(report, bad_requirement.ticket_type)

        # Assertions
        assert report.total_score == 35
        assert report.ready_for_review is False
        assert len(report.blocking_issues) == 2
        assert report.blocking_issues[0].category == "MISSING_AC"
        assert decision == "REJECT"

    @patch("src.reqgate.agents.scoring.get_llm_client")
    @patch("src.reqgate.agents.scoring.get_rubric_loader")
    def test_borderline_score_without_blockers_passes(
        self,
        mock_rubric_loader,
        mock_llm_client,
        good_requirement,
    ):
        """Test that a score exactly at threshold passes if no blockers."""
        # Setup rubric mock
        mock_rubric_instance = MagicMock()
        mock_rubric_instance.get_scenario_config.return_value = {
            "threshold": 60,
            "weights": {"completeness": 0.5, "logic": 0.5},
            "required_fields": [],
            "negative_patterns": [],
        }
        mock_rubric_loader.return_value = mock_rubric_instance

        # LLM returns exactly threshold score
        borderline_response = TicketScoreReport(
            total_score=60,
            ready_for_review=True,
            dimension_scores={"completeness": 60, "logic": 60},
            blocking_issues=[],
            non_blocking_issues=[],
            summary_markdown="Borderline pass",
        ).model_dump_json()

        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = borderline_response
        mock_llm_client.return_value = mock_llm_instance

        # Execute flow
        agent = ScoringAgent()
        report = agent.score(good_requirement)

        gate = HardGate()
        decision = gate.decide(report, good_requirement.ticket_type)

        # Assertions
        assert report.total_score == 60
        assert decision == "PASS"

    @patch("src.reqgate.agents.scoring.get_llm_client")
    @patch("src.reqgate.agents.scoring.get_rubric_loader")
    def test_high_score_with_blockers_fails(
        self,
        mock_rubric_loader,
        mock_llm_client,
        good_requirement,
    ):
        """Test that even a high score fails if there are blockers."""
        # Setup rubric mock
        mock_rubric_instance = MagicMock()
        mock_rubric_instance.get_scenario_config.return_value = {
            "threshold": 60,
            "weights": {"completeness": 0.5, "logic": 0.5},
            "required_fields": [],
            "negative_patterns": [],
        }
        mock_rubric_loader.return_value = mock_rubric_instance

        # LLM returns high score but with blocker
        high_score_with_blocker = TicketScoreReport(
            total_score=90,
            ready_for_review=False,
            dimension_scores={"completeness": 90, "logic": 90},
            blocking_issues=[
                ReviewIssue(
                    severity="BLOCKER",
                    category="SECURITY",
                    description="安全漏洞风险",
                    suggestion="添加安全审核",
                )
            ],
            non_blocking_issues=[],
            summary_markdown="High score but security issue",
        ).model_dump_json()

        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = high_score_with_blocker
        mock_llm_client.return_value = mock_llm_instance

        # Execute flow
        agent = ScoringAgent()
        report = agent.score(good_requirement)

        gate = HardGate()
        decision = gate.decide(report, good_requirement.ticket_type)

        # Assertions
        assert report.total_score == 90
        assert len(report.blocking_issues) == 1
        assert decision == "REJECT"  # Blockers override high score


class TestRealLLMIntegration:
    """Real LLM integration tests (optional, requires API key)."""

    @pytest.fixture
    def sample_requirement(self) -> RequirementPacket:
        """Create a sample requirement for real LLM testing."""
        return RequirementPacket(
            raw_text="""
            # Feature: Add Dark Mode

            ## Description
            Users should be able to switch between light and dark theme.

            ## Acceptance Criteria
            - Given I am in settings, when I toggle dark mode, then the UI switches to dark theme
            - Given dark mode is on, when I restart the app, then dark mode persists

            ## Technical Notes
            - Use CSS variables for theming
            - Store preference in localStorage
            """,
            source_type="Jira_Ticket",
            project_key="UI",
            priority="P2",
            ticket_type="Feature",
        )

    @pytest.mark.skipif(
        False,  # Enabled for testing
        reason="Real LLM test requires API key and incurs costs",
    )
    def test_real_llm_scoring(self, sample_requirement):
        """Test with real LLM (requires OPENROUTER_API_KEY in .env)."""

        # Clear singletons for clean test
        import src.reqgate.adapters.llm as llm_module
        import src.reqgate.gates.rules as rules_module

        llm_module._llm_client = None
        rules_module.get_rubric_loader.cache_clear()

        agent = ScoringAgent()
        report = agent.score(sample_requirement)

        # Basic assertions
        assert 0 <= report.total_score <= 100
        assert isinstance(report.ready_for_review, bool)
        assert isinstance(report.blocking_issues, list)
        assert report.summary_markdown is not None

        print("\n=== Real LLM Result ===")
        print(f"Score: {report.total_score}")
        print(f"Ready: {report.ready_for_review}")
        print(f"Blockers: {len(report.blocking_issues)}")
        print(f"Summary: {report.summary_markdown[:200]}...")
