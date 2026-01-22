"""Tests for Hard Gate."""

import pytest
from src.reqgate.gates.decision import HardGate
from src.reqgate.schemas.outputs import ReviewIssue, TicketScoreReport


@pytest.fixture
def passing_report():
    """Create a passing report."""
    return TicketScoreReport(
        total_score=75,
        ready_for_review=True,
        dimension_scores={"completeness": 80, "logic": 70},
        blocking_issues=[],
        non_blocking_issues=[],
        summary_markdown="Good quality",
    )


@pytest.fixture
def failing_low_score_report():
    """Create a failing report due to low score."""
    return TicketScoreReport(
        total_score=45,
        ready_for_review=False,
        dimension_scores={"completeness": 40, "logic": 50},
        blocking_issues=[],
        non_blocking_issues=[],
        summary_markdown="Low score",
    )


@pytest.fixture
def failing_blocking_issues_report():
    """Create a failing report due to blocking issues."""
    blocking_issue = ReviewIssue(
        severity="BLOCKER",
        category="MISSING_AC",
        description="缺少验收标准",
        suggestion="添加验收标准",
    )
    return TicketScoreReport(
        total_score=70,  # Score is above threshold but has blockers
        ready_for_review=False,
        dimension_scores={"completeness": 70, "logic": 70},
        blocking_issues=[blocking_issue],
        non_blocking_issues=[],
        summary_markdown="Has blocking issues",
    )


class TestHardGate:
    """Test suite for HardGate."""

    def test_initialization(self):
        """Test gate initialization."""
        gate = HardGate()
        assert gate.rubric_loader is not None

    def test_pass_feature_above_threshold(self, passing_report):
        """Test PASS decision for Feature above threshold."""
        gate = HardGate()
        decision = gate.decide(passing_report, "Feature")

        assert decision == "PASS"

    def test_reject_feature_below_threshold(self, failing_low_score_report):
        """Test REJECT decision for Feature below threshold (60)."""
        gate = HardGate()
        decision = gate.decide(failing_low_score_report, "Feature")

        assert decision == "REJECT"

    def test_reject_for_blocking_issues(self, failing_blocking_issues_report):
        """Test REJECT even with good score if blocking issues exist."""
        gate = HardGate()
        decision = gate.decide(failing_blocking_issues_report, "Feature")

        assert decision == "REJECT"

    def test_pass_bug_above_threshold(self, passing_report):
        """Test PASS decision for Bug above threshold (50)."""
        gate = HardGate()
        decision = gate.decide(passing_report, "Bug")

        assert decision == "PASS"

    def test_reject_bug_below_threshold(self):
        """Test REJECT decision for Bug below threshold (50)."""
        report = TicketScoreReport(
            total_score=40,
            ready_for_review=False,
            dimension_scores={},
            blocking_issues=[],
            non_blocking_issues=[],
            summary_markdown="Low score",
        )

        gate = HardGate()
        decision = gate.decide(report, "Bug")

        assert decision == "REJECT"

    def test_boundary_at_threshold_feature(self):
        """Test boundary: exactly at threshold (60) for Feature."""
        report = TicketScoreReport(
            total_score=60,
            ready_for_review=True,
            dimension_scores={},
            blocking_issues=[],
            non_blocking_issues=[],
            summary_markdown="At threshold",
        )

        gate = HardGate()
        decision = gate.decide(report, "Feature")

        assert decision == "PASS"

    def test_boundary_one_below_threshold_feature(self):
        """Test boundary: one below threshold (59) for Feature."""
        report = TicketScoreReport(
            total_score=59,
            ready_for_review=False,
            dimension_scores={},
            blocking_issues=[],
            non_blocking_issues=[],
            summary_markdown="Just below threshold",
        )

        gate = HardGate()
        decision = gate.decide(report, "Feature")

        assert decision == "REJECT"

    def test_boundary_at_threshold_bug(self):
        """Test boundary: exactly at threshold (50) for Bug."""
        report = TicketScoreReport(
            total_score=50,
            ready_for_review=True,
            dimension_scores={},
            blocking_issues=[],
            non_blocking_issues=[],
            summary_markdown="At threshold",
        )

        gate = HardGate()
        decision = gate.decide(report, "Bug")

        assert decision == "PASS"

    def test_multiple_blocking_issues(self):
        """Test REJECT with multiple blocking issues."""
        issues = [
            ReviewIssue(
                severity="BLOCKER",
                category="MISSING_AC",
                description="Issue 1",
                suggestion="Fix 1",
            ),
            ReviewIssue(
                severity="BLOCKER",
                category="LOGIC_GAP",
                description="Issue 2",
                suggestion="Fix 2",
            ),
        ]

        report = TicketScoreReport(
            total_score=80,
            ready_for_review=False,
            dimension_scores={},
            blocking_issues=issues,
            non_blocking_issues=[],
            summary_markdown="Multiple blockers",
        )

        gate = HardGate()
        decision = gate.decide(report, "Feature")

        assert decision == "REJECT"

    def test_non_blocking_issues_dont_cause_reject(self):
        """Test that non-blocking issues alone don't cause REJECT."""
        non_blocking = ReviewIssue(
            severity="WARNING",
            category="AMBIGUITY",
            description="Some ambiguity",
            suggestion="Clarify",
        )

        report = TicketScoreReport(
            total_score=75,
            ready_for_review=True,
            dimension_scores={},
            blocking_issues=[],
            non_blocking_issues=[non_blocking],
            summary_markdown="Only warnings",
        )

        gate = HardGate()
        decision = gate.decide(report, "Feature")

        assert decision == "PASS"

    def test_decision_type(self, passing_report):
        """Test that decision is of correct type."""
        gate = HardGate()
        decision = gate.decide(passing_report, "Feature")

        # GateDecision is Literal["PASS", "REJECT"]
        assert decision in ("PASS", "REJECT")
