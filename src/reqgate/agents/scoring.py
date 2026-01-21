"""
Scoring agent for requirement evaluation.

Uses LLM to score requirements against rubric.
Phase 1: Placeholder - Full implementation in later tasks.
"""

from typing import Any

from src.reqgate.adapters.llm import get_llm_client
from src.reqgate.gates.rules import get_rubric_loader
from src.reqgate.schemas.inputs import RequirementPacket
from src.reqgate.schemas.outputs import TicketScoreReport


class ScoringAgent:
    """
    Scoring agent for requirement evaluation.

    Uses LLM to analyze requirements and produce score reports.
    """

    def __init__(self) -> None:
        self.llm = get_llm_client()
        self.rubric_loader = get_rubric_loader()

    def score(self, packet: RequirementPacket) -> TicketScoreReport:
        """
        Score a requirement.

        Args:
            packet: Standardized requirement input

        Returns:
            Scoring report
        """
        # 1. Load rules
        config = self.rubric_loader.get_scenario_config(packet.ticket_type)

        # 2. Build prompt
        prompt = self._build_prompt(packet, config)

        # 3. Call LLM
        llm_response = self.llm.invoke(
            prompt=prompt,
            response_schema=TicketScoreReport,
        )

        # 4. Parse and validate output
        report = TicketScoreReport.model_validate_json(llm_response)

        return report

    def _build_prompt(self, packet: RequirementPacket, config: dict[str, Any]) -> str:
        """Build scoring prompt."""
        prompt_template = """# Role
You are a strict Tech Lead and Gatekeeper for the engineering team.
Your job is to review the following Ticket/PRD and decide if it is **Ready for Development**.

# Context & Configuration
- Scenario: {scenario}
- Pass Threshold: {threshold} points
- Weights: {weights}

# Input Ticket
Type: {ticket_type}
Project: {project_key}
Priority: {priority}
Content:
{raw_text}

# Scoring Rubric
Required Fields: {required_fields}
Negative Patterns: {negative_patterns}

# Blocking Rules
You must mark an issue as **BLOCKER** if:
1. Missing any required field
2. Contains ambiguous words without quantitative metrics
3. Logic flow is incomplete

# Output Format
Produce a JSON matching the TicketScoreReport schema with:
- total_score: 0-100
- ready_for_review: true/false based on threshold
- dimension_scores: breakdown by weights
- blocking_issues: fatal errors (array of ReviewIssue)
- non_blocking_issues: suggestions (array of ReviewIssue)
- summary_markdown: concise summary for PM

Be objective and direct. Provide actionable advice.
"""

        scenario = "BUG" if packet.ticket_type == "Bug" else "FEATURE"

        return prompt_template.format(
            scenario=scenario,
            threshold=config["threshold"],
            weights=config["weights"],
            ticket_type=packet.ticket_type,
            project_key=packet.project_key,
            priority=packet.priority,
            raw_text=packet.raw_text,
            required_fields=config.get("required_fields", []),
            negative_patterns=config.get("negative_patterns", []),
        )
