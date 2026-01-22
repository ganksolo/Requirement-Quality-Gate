"""Internal state schemas for workflow management."""

from typing import TypedDict

from src.reqgate.schemas.inputs import RequirementPacket
from src.reqgate.schemas.outputs import TicketScoreReport


class AgentState(TypedDict):
    """
    LangGraph workflow state.

    This TypedDict defines the state passed between nodes
    in the LangGraph workflow.
    """

    # Input
    packet: RequirementPacket

    # Output
    score_report: TicketScoreReport | None

    # Flow control
    retry_count: int
    error_logs: list[str]
    current_stage: str
