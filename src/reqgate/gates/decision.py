"""
Hard gate decision logic.

Implements deterministic pass/reject logic based on scoring results.
"""

import logging
from typing import Literal

from src.reqgate.gates.rules import get_rubric_loader
from src.reqgate.schemas.outputs import TicketScoreReport

logger = logging.getLogger("reqgate.gates")

GateDecision = Literal["PASS", "REJECT"]


class HardGate:
    """
    Hard gate for requirement quality.

    Makes deterministic pass/reject decisions based on:
    1. Presence of blocking issues
    2. Score threshold
    """

    def __init__(self) -> None:
        self.rubric_loader = get_rubric_loader()

    def decide(self, report: TicketScoreReport, ticket_type: str) -> GateDecision:
        """
        Make gate decision.

        Args:
            report: Scoring report
            ticket_type: 'Feature' or 'Bug'

        Returns:
            PASS or REJECT
        """
        config = self.rubric_loader.get_scenario_config(ticket_type)
        threshold = config["threshold"]

        logger.info(
            "Gate decision starting",
            extra={
                "ticket_type": ticket_type,
                "total_score": report.total_score,
                "threshold": threshold,
                "blocking_issues_count": len(report.blocking_issues),
            },
        )

        # Rule 1: Any BLOCKER issue = REJECT
        if len(report.blocking_issues) > 0:
            logger.warning(
                "Gate decision: REJECT (blocking issues found)",
                extra={
                    "decision": "REJECT",
                    "reason": "blocking_issues",
                    "blocking_count": len(report.blocking_issues),
                    "categories": [issue.category for issue in report.blocking_issues],
                },
            )
            return "REJECT"

        # Rule 2: Score below threshold = REJECT
        if report.total_score < threshold:
            logger.warning(
                "Gate decision: REJECT (score below threshold)",
                extra={
                    "decision": "REJECT",
                    "reason": "low_score",
                    "score": report.total_score,
                    "threshold": threshold,
                },
            )
            return "REJECT"

        logger.info(
            "Gate decision: PASS",
            extra={
                "decision": "PASS",
                "score": report.total_score,
                "threshold": threshold,
            },
        )
        return "PASS"

