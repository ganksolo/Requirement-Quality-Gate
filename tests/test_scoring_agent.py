"""Tests for Scoring Agent."""

from unittest.mock import MagicMock, patch

import pytest
from src.reqgate.agents.scoring import ScoringAgent
from src.reqgate.schemas.inputs import RequirementPacket
from src.reqgate.schemas.outputs import TicketScoreReport


@pytest.fixture
def sample_packet():
    """Create a sample RequirementPacket for testing."""
    return RequirementPacket(
        raw_text="作为用户，我希望能够使用邮箱登录系统，以便快速访问我的账户。",
        source_type="Jira_Ticket",
        project_key="AUTH",
        priority="P1",
        ticket_type="Feature",
    )


@pytest.fixture
def sample_bug_packet():
    """Create a sample Bug RequirementPacket for testing."""
    return RequirementPacket(
        raw_text="登录页面在 Chrome 浏览器中显示错误，无法点击登录按钮。",
        source_type="Jira_Ticket",
        project_key="AUTH",
        priority="P0",
        ticket_type="Bug",
    )


class TestScoringAgent:
    """Test suite for ScoringAgent."""

    @patch("src.reqgate.agents.scoring.get_llm_client")
    @patch("src.reqgate.agents.scoring.get_rubric_loader")
    def test_initialization(self, mock_rubric, mock_llm):
        """Test agent initialization."""
        agent = ScoringAgent()

        assert agent.llm is not None
        assert agent.rubric_loader is not None

    @patch("src.reqgate.agents.scoring.get_llm_client")
    @patch("src.reqgate.agents.scoring.get_rubric_loader")
    def test_score_returns_report(self, mock_rubric, mock_llm, sample_packet):
        """Test that score method returns a TicketScoreReport."""
        # Setup mock LLM response
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = """
        {
            "total_score": 75,
            "ready_for_review": true,
            "dimension_scores": {"completeness": 80, "logic": 70},
            "blocking_issues": [],
            "non_blocking_issues": [],
            "summary_markdown": "Good quality requirement"
        }
        """
        mock_llm.return_value = mock_llm_instance

        # Setup mock rubric
        mock_rubric_instance = MagicMock()
        mock_rubric_instance.get_scenario_config.return_value = {
            "threshold": 60,
            "weights": {"completeness": 0.4, "logic": 0.3},
            "required_fields": [],
            "negative_patterns": [],
        }
        mock_rubric.return_value = mock_rubric_instance

        agent = ScoringAgent()
        report = agent.score(sample_packet)

        assert isinstance(report, TicketScoreReport)
        assert report.total_score == 75
        assert report.ready_for_review is True

    @patch("src.reqgate.agents.scoring.get_llm_client")
    @patch("src.reqgate.agents.scoring.get_rubric_loader")
    def test_score_with_blocking_issues(self, mock_rubric, mock_llm, sample_packet):
        """Test scoring with blocking issues."""
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = """
        {
            "total_score": 35,
            "ready_for_review": false,
            "dimension_scores": {"completeness": 30, "logic": 40},
            "blocking_issues": [
                {
                    "severity": "BLOCKER",
                    "category": "MISSING_AC",
                    "description": "缺少验收标准",
                    "suggestion": "添加 Given/When/Then"
                }
            ],
            "non_blocking_issues": [],
            "summary_markdown": "Missing acceptance criteria"
        }
        """
        mock_llm.return_value = mock_llm_instance

        mock_rubric_instance = MagicMock()
        mock_rubric_instance.get_scenario_config.return_value = {
            "threshold": 60,
            "weights": {},
            "required_fields": [],
            "negative_patterns": [],
        }
        mock_rubric.return_value = mock_rubric_instance

        agent = ScoringAgent()
        report = agent.score(sample_packet)

        assert report.total_score == 35
        assert report.ready_for_review is False
        assert len(report.blocking_issues) == 1
        assert report.blocking_issues[0].category == "MISSING_AC"

    @patch("src.reqgate.agents.scoring.get_llm_client")
    @patch("src.reqgate.agents.scoring.get_rubric_loader")
    def test_build_prompt_feature(self, mock_rubric, mock_llm, sample_packet):
        """Test prompt building for Feature type."""
        mock_rubric_instance = MagicMock()
        mock_rubric_instance.get_scenario_config.return_value = {
            "threshold": 60,
            "weights": {"completeness": 0.4},
            "required_fields": [{"field": "ac", "error_msg": "Missing AC"}],
            "negative_patterns": [{"pattern": "TBD", "severity": "WARNING"}],
        }
        mock_rubric.return_value = mock_rubric_instance

        agent = ScoringAgent()
        config = mock_rubric_instance.get_scenario_config("Feature")
        prompt = agent._build_prompt(sample_packet, config)

        assert "FEATURE" in prompt
        assert "60" in prompt  # threshold
        assert "AUTH" in prompt  # project_key
        assert "P1" in prompt  # priority

    @patch("src.reqgate.agents.scoring.get_llm_client")
    @patch("src.reqgate.agents.scoring.get_rubric_loader")
    def test_build_prompt_bug(self, mock_rubric, mock_llm, sample_bug_packet):
        """Test prompt building for Bug type."""
        mock_rubric_instance = MagicMock()
        mock_rubric_instance.get_scenario_config.return_value = {
            "threshold": 50,
            "weights": {"reproduction": 0.5},
            "required_fields": [],
            "negative_patterns": [],
        }
        mock_rubric.return_value = mock_rubric_instance

        agent = ScoringAgent()
        config = mock_rubric_instance.get_scenario_config("Bug")
        prompt = agent._build_prompt(sample_bug_packet, config)

        assert "BUG" in prompt
        assert "50" in prompt  # threshold
        assert "P0" in prompt  # priority

    @patch("src.reqgate.agents.scoring.get_llm_client")
    @patch("src.reqgate.agents.scoring.get_rubric_loader")
    def test_score_calls_llm(self, mock_rubric, mock_llm, sample_packet):
        """Test that score method calls LLM with correct parameters."""
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = """
        {
            "total_score": 70,
            "ready_for_review": true,
            "dimension_scores": {},
            "blocking_issues": [],
            "non_blocking_issues": [],
            "summary_markdown": "OK"
        }
        """
        mock_llm.return_value = mock_llm_instance

        mock_rubric_instance = MagicMock()
        mock_rubric_instance.get_scenario_config.return_value = {
            "threshold": 60,
            "weights": {},
            "required_fields": [],
            "negative_patterns": [],
        }
        mock_rubric.return_value = mock_rubric_instance

        agent = ScoringAgent()
        agent.score(sample_packet)

        mock_llm_instance.invoke.assert_called_once()
        call_args = mock_llm_instance.invoke.call_args
        assert "prompt" in call_args.kwargs or len(call_args.args) > 0
