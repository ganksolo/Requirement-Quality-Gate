"""
Hard gate decision logic.

Implements deterministic pass/reject logic based on scoring results.
Phase 1: Placeholder - Full implementation in later tasks.
"""

from typing import Literal

from src.reqgate.gates.rules import get_rubric_loader
from src.reqgate.schemas.outputs import TicketScoreReport

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

        # Rule 1: Any BLOCKER issue = REJECT
        if len(report.blocking_issues) > 0:
            return "REJECT"

        # Rule 2: Score below threshold = REJECT
        if report.total_score < threshold:
            return "REJECT"

        return "PASS"
