"""
Internal schemas for agent state and workflow.

These schemas are used internally and not exposed via API.
Phase 1: Placeholder - Full implementation in later tasks.
"""

from typing import TypedDict

from src.reqgate.schemas.inputs import RequirementPacket
from src.reqgate.schemas.outputs import TicketScoreReport


class AgentState(TypedDict):
    """
    Agent workflow state.

    Used by LangGraph to manage workflow state.
    Phase 1 doesn't use LangGraph yet, but we define the state for future use.
    """

    # Input
    packet: RequirementPacket

    # Output
    score_report: TicketScoreReport | None

    # Flow control
    retry_count: int
    error_logs: list[str]
    current_stage: str
