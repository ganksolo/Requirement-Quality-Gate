"""Internal state schemas for workflow management."""

import re
from typing import TypedDict

from pydantic import BaseModel, Field, field_validator, model_validator
from src.reqgate.schemas.inputs import RequirementPacket
from src.reqgate.schemas.outputs import TicketScoreReport


class PRD_Draft(BaseModel):
    """
    Structured PRD draft produced by Structuring Agent.

    This is an intermediate representation that bridges unstructured input
    and the scoring process. It may contain incomplete information, which
    is captured in missing_info and clarification_questions fields.

    Attributes:
        title: Descriptive title starting with an action verb (10-200 chars)
        user_story: User story in 'As a X, I want Y, so that Z' format
        acceptance_criteria: List of discrete acceptance criteria (min 1)
        edge_cases: Identified edge cases or error scenarios
        resources: Dependencies, related tickets, or external resources
        missing_info: Information gaps identified by the agent
        clarification_questions: Questions to ask the PM for clarification
    """

    title: str = Field(
        ...,
        min_length=10,
        max_length=200,
        description="Descriptive title starting with an action verb",
    )

    user_story: str = Field(
        ...,
        min_length=20,
        description="User story in 'As a X, I want Y, so that Z' format",
    )

    acceptance_criteria: list[str] = Field(
        ...,
        min_length=1,
        description="List of discrete acceptance criteria",
    )

    edge_cases: list[str] = Field(
        default_factory=list,
        description="Identified edge cases or error scenarios",
    )

    resources: list[str] = Field(
        default_factory=list,
        description="Dependencies, related tickets, or external resources",
    )

    # Agent self-diagnosis fields
    missing_info: list[str] = Field(
        default_factory=list,
        description="Information gaps identified by the agent",
    )

    clarification_questions: list[str] = Field(
        default_factory=list,
        description="Questions to ask the PM for clarification",
    )

    @field_validator("title")
    @classmethod
    def title_must_start_with_verb(cls, v: str) -> str:
        """Validate that title starts with an action verb."""
        # Common action verbs for PRD titles
        action_verbs = (
            "implement",
            "add",
            "create",
            "build",
            "develop",
            "design",
            "fix",
            "update",
            "remove",
            "delete",
            "refactor",
            "optimize",
            "improve",
            "enable",
            "disable",
            "configure",
            "setup",
            "integrate",
            "migrate",
            "support",
            "allow",
            "prevent",
            "validate",
            "verify",
            "test",
            "deploy",
            "release",
            "launch",
            "introduce",
            "extend",
            "enhance",
        )
        first_word = v.strip().split()[0].lower() if v.strip() else ""
        if not first_word.startswith(action_verbs):
            raise ValueError(
                f"Title must start with an action verb (e.g., Implement, Add, Create). "
                f"Got: '{first_word}'"
            )
        return v

    @field_validator("user_story")
    @classmethod
    def user_story_must_follow_format(cls, v: str) -> str:
        """Validate that user_story follows 'As a X, I want Y, so that Z' format."""
        # Pattern to match user story format (case-insensitive)
        pattern = r"^[Aa]s\s+a[n]?\s+.+,\s*[Ii]\s+want\s+.+,\s*[Ss]o\s+that\s+.+"
        if not re.match(pattern, v.strip()):
            raise ValueError(
                "User story must follow 'As a [role], I want [feature], so that [benefit]' format"
            )
        return v

    @model_validator(mode="after")
    def acceptance_criteria_not_empty_strings(self) -> PRD_Draft:
        """Validate that acceptance criteria items are not empty strings."""
        for i, ac in enumerate(self.acceptance_criteria):
            if not ac.strip():
                raise ValueError(f"Acceptance criteria item {i + 1} cannot be empty or whitespace")
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Implement user authentication with OAuth2",
                "user_story": "As a user, I want to log in with Google, so that I don't need to create a new password",
                "acceptance_criteria": [
                    "User can click 'Sign in with Google' button",
                    "System redirects to Google OAuth consent screen",
                    "After approval, user is logged into the application",
                ],
                "edge_cases": [
                    "User denies OAuth consent",
                    "Google service is down",
                ],
                "resources": [
                    "OAuth2 RFC 6749",
                    "Google OAuth documentation",
                ],
                "missing_info": ["Session timeout duration not specified"],
                "clarification_questions": ["Should we support other OAuth providers?"],
            }
        }
    }


class AgentState(TypedDict):
    """
    LangGraph workflow state.

    This TypedDict defines the state passed between nodes
    in the LangGraph workflow.

    Phase 1 fields:
        packet: Input requirement packet
        score_report: Scoring agent output
        retry_count: Number of retry attempts
        error_logs: List of error messages
        current_stage: Current workflow stage name

    Phase 2 additions:
        structured_prd: Structuring agent output (optional)
        gate_decision: Hard gate decision (optional)
        fallback_activated: Whether fallback mode was used
        execution_times: Execution time per node in seconds
    """

    # Input
    packet: RequirementPacket

    # Intermediate results (Phase 2)
    structured_prd: PRD_Draft | None

    # Output
    score_report: TicketScoreReport | None
    gate_decision: bool | None

    # Flow control
    retry_count: int
    error_logs: list[str]
    current_stage: str

    # Phase 2: Observability
    fallback_activated: bool
    execution_times: dict[str, float]

    # Phase 2 Section 10: Hard Check #1
    structure_check_passed: bool | None
    structure_errors: list[str]
