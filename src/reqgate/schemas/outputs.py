"""
Output schemas for scoring results.

These schemas define the contract for system outputs.
Phase 1: Placeholder - Full implementation in later tasks.
"""

from typing import Literal

from pydantic import BaseModel, Field


class ReviewIssue(BaseModel):
    """Single review issue found during scoring."""

    severity: Literal["BLOCKER", "WARNING"] = Field(
        ...,
        description="Issue severity level",
    )

    category: Literal[
        "MISSING_AC",
        "AMBIGUITY",
        "LOGIC_GAP",
        "SECURITY",
        "MISSING_FIELD",
    ] = Field(
        ...,
        description="Issue category",
    )

    description: str = Field(
        ...,
        description="Issue description",
    )

    suggestion: str = Field(
        ...,
        description="Suggested fix",
    )


class TicketScoreReport(BaseModel):
    """
    Ticket scoring report.

    This is the output of the Scoring Agent and input to the Hard Gate.
    """

    total_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Overall score (0-100)",
    )

    ready_for_review: bool = Field(
        ...,
        description="Whether the ticket passed the gate",
    )

    dimension_scores: dict[str, int] = Field(
        ...,
        description="Scores by dimension, e.g., {'completeness': 80, 'logic': 60}",
    )

    blocking_issues: list[ReviewIssue] = Field(
        default_factory=list,
        description="List of blocking issues (cause rejection)",
    )

    non_blocking_issues: list[ReviewIssue] = Field(
        default_factory=list,
        description="List of non-blocking issues (suggestions)",
    )

    summary_markdown: str = Field(
        ...,
        description="Markdown summary for PM",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_score": 45,
                "ready_for_review": False,
                "dimension_scores": {
                    "completeness": 40,
                    "logic": 50,
                },
                "blocking_issues": [
                    {
                        "severity": "BLOCKER",
                        "category": "MISSING_AC",
                        "description": "缺少验收标准",
                        "suggestion": "请添加至少 3 条 Given/When/Then 格式的验收标准",
                    }
                ],
                "non_blocking_issues": [],
                "summary_markdown": "## 评分结果\n\n总分: 45/100 ❌\n\n### 阻塞性问题\n- 缺少验收标准",
            }
        }
    }
