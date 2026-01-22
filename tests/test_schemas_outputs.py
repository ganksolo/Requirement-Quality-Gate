"""Tests for output schemas."""

import pytest
from pydantic import ValidationError

from src.reqgate.schemas.outputs import ReviewIssue, TicketScoreReport


class TestReviewIssue:
    """Test suite for ReviewIssue schema."""

    def test_valid_blocker_issue(self):
        """Test creating a valid BLOCKER issue."""
        issue = ReviewIssue(
            severity="BLOCKER",
            category="MISSING_AC",
            description="缺少验收标准",
            suggestion="请添加至少 3 条 Given/When/Then 格式的验收标准",
        )

        assert issue.severity == "BLOCKER"
        assert issue.category == "MISSING_AC"

    def test_valid_warning_issue(self):
        """Test creating a valid WARNING issue."""
        issue = ReviewIssue(
            severity="WARNING",
            category="AMBIGUITY",
            description="描述不够清晰",
            suggestion="请明确具体行为",
        )

        assert issue.severity == "WARNING"

    def test_invalid_severity(self):
        """Test that invalid severity fails."""
        with pytest.raises(ValidationError):
            ReviewIssue(
                severity="ERROR",
                category="MISSING_AC",
                description="test",
                suggestion="test",
            )

    def test_invalid_category(self):
        """Test that invalid category fails."""
        with pytest.raises(ValidationError):
            ReviewIssue(
                severity="BLOCKER",
                category="UNKNOWN_CATEGORY",
                description="test",
                suggestion="test",
            )

    def test_all_valid_categories(self):
        """Test all valid categories."""
        categories = ["MISSING_AC", "AMBIGUITY", "LOGIC_GAP", "SECURITY", "MISSING_FIELD"]

        for category in categories:
            issue = ReviewIssue(
                severity="BLOCKER",
                category=category,
                description="test",
                suggestion="test",
            )
            assert issue.category == category


class TestTicketScoreReport:
    """Test suite for TicketScoreReport schema."""

    def test_valid_passing_report(self):
        """Test creating a valid passing report."""
        report = TicketScoreReport(
            total_score=85,
            ready_for_review=True,
            dimension_scores={"completeness": 90, "logic": 80},
            blocking_issues=[],
            non_blocking_issues=[],
            summary_markdown="## 评分结果\n\n总分: 85/100 ✅",
        )

        assert report.total_score == 85
        assert report.ready_for_review is True
        assert len(report.blocking_issues) == 0

    def test_valid_failing_report(self):
        """Test creating a valid failing report with blocking issues."""
        blocking_issue = ReviewIssue(
            severity="BLOCKER",
            category="MISSING_AC",
            description="缺少验收标准",
            suggestion="请添加验收标准",
        )

        report = TicketScoreReport(
            total_score=45,
            ready_for_review=False,
            dimension_scores={"completeness": 40, "logic": 50},
            blocking_issues=[blocking_issue],
            non_blocking_issues=[],
            summary_markdown="## 评分结果\n\n总分: 45/100 ❌",
        )

        assert report.total_score == 45
        assert report.ready_for_review is False
        assert len(report.blocking_issues) == 1

    def test_score_boundary_min(self):
        """Test minimum valid score (0)."""
        report = TicketScoreReport(
            total_score=0,
            ready_for_review=False,
            dimension_scores={},
            blocking_issues=[],
            non_blocking_issues=[],
            summary_markdown="Failed",
        )

        assert report.total_score == 0

    def test_score_boundary_max(self):
        """Test maximum valid score (100)."""
        report = TicketScoreReport(
            total_score=100,
            ready_for_review=True,
            dimension_scores={"all": 100},
            blocking_issues=[],
            non_blocking_issues=[],
            summary_markdown="Perfect",
        )

        assert report.total_score == 100

    def test_score_below_min(self):
        """Test that score below 0 fails."""
        with pytest.raises(ValidationError):
            TicketScoreReport(
                total_score=-1,
                ready_for_review=False,
                dimension_scores={},
                blocking_issues=[],
                non_blocking_issues=[],
                summary_markdown="Invalid",
            )

    def test_score_above_max(self):
        """Test that score above 100 fails."""
        with pytest.raises(ValidationError):
            TicketScoreReport(
                total_score=101,
                ready_for_review=True,
                dimension_scores={},
                blocking_issues=[],
                non_blocking_issues=[],
                summary_markdown="Invalid",
            )

    def test_multiple_blocking_issues(self):
        """Test report with multiple blocking issues."""
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
            total_score=30,
            ready_for_review=False,
            dimension_scores={"completeness": 20, "logic": 40},
            blocking_issues=issues,
            non_blocking_issues=[],
            summary_markdown="Multiple issues found",
        )

        assert len(report.blocking_issues) == 2

    def test_json_serialization(self):
        """Test that report can be serialized to JSON."""
        report = TicketScoreReport(
            total_score=75,
            ready_for_review=True,
            dimension_scores={"completeness": 80},
            blocking_issues=[],
            non_blocking_issues=[],
            summary_markdown="Good",
        )

        json_str = report.model_dump_json()
        assert "total_score" in json_str
        assert "75" in json_str

    def test_json_schema_example(self):
        """Test that model has valid JSON schema example."""
        schema = TicketScoreReport.model_json_schema()
        assert "example" in schema or "examples" in schema or "$defs" in schema
