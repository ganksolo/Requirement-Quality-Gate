"""
Input schemas for requirement processing.

These schemas define the contract for external inputs to the system.
Phase 1: Placeholder - Full implementation in later tasks.
"""

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


class RequirementPacket(BaseModel):
    """
    Standardized requirement input packet.

    This is the input contract for the system.
    All external inputs must be transformed to this format.
    """

    raw_text: str = Field(
        ...,
        min_length=10,
        description="Cleaned plain text requirement description",
    )

    source_type: Literal["Jira_Ticket", "PRD_Doc", "Meeting_Transcript"] = Field(
        ...,
        description="Input source type",
    )

    project_key: str = Field(
        ...,
        pattern=r"^[A-Z]{2,5}$",
        description="Project identifier, e.g., 'PAY', 'OPS'",
    )

    priority: Literal["P0", "P1", "P2"] = Field(
        default="P1",
        description="Priority level",
    )

    ticket_type: Literal["Feature", "Bug"] = Field(
        default="Feature",
        description="Requirement type",
    )

    attachments: list[HttpUrl] = Field(
        default_factory=list,
        description="List of attachment URLs",
    )

    @field_validator("raw_text")
    @classmethod
    def validate_text_not_empty(cls, v: str) -> str:
        """Validate text is not empty or whitespace only."""
        if not v.strip():
            raise ValueError("raw_text cannot be empty or whitespace only")
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "example": {
                "raw_text": "实现用户登录功能，支持邮箱和手机号登录",
                "source_type": "Jira_Ticket",
                "project_key": "AUTH",
                "priority": "P1",
                "ticket_type": "Feature",
            }
        }
    }
