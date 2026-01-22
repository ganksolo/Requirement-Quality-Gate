"""
Scoring agent for requirement evaluation.

Uses LLM to score requirements against rubric.
"""

from src.reqgate.adapters.llm import get_llm_client
from src.reqgate.gates.rules import get_rubric_loader
from src.reqgate.schemas.config import RubricScenarioConfig
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
        llm_response = self.llm.invoke(prompt, TicketScoreReport)

        # 4. Parse and validate output
        report = TicketScoreReport.model_validate_json(llm_response)

        return report

    def _build_prompt(
        self, packet: RequirementPacket, config: RubricScenarioConfig
    ) -> str:
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

# Blocking Rules
You must mark an issue as **BLOCKER** if:
1. Missing acceptance criteria (验收标准)
2. Contains ambiguous words like "better", "fast", "nice" without metrics
3. Logic flow is incomplete

# Output Format (STRICT JSON)
You MUST return a JSON object exactly matching this structure:

{{
  "total_score": 75,
  "ready_for_review": true,
  "dimension_scores": {{"completeness": 80, "logic": 70, "clarity": 75}},
  "blocking_issues": [
    {{
      "severity": "BLOCKER",
      "category": "MISSING_AC",
      "description": "缺少验收标准",
      "suggestion": "请添加 Given/When/Then 格式的验收标准"
    }}
  ],
  "non_blocking_issues": [
    {{
      "severity": "WARNING",
      "category": "AMBIGUITY",
      "description": "描述不够清晰",
      "suggestion": "请明确具体行为"
    }}
  ],
  "summary_markdown": "## 评分结果\\n\\n总分: 75/100"
}}

IMPORTANT:
- severity MUST be "BLOCKER" or "WARNING"
- category MUST be one of: "MISSING_AC", "AMBIGUITY", "LOGIC_GAP", "SECURITY", "MISSING_FIELD"
- If no issues, use empty arrays: []
- ready_for_review is true if total_score >= {threshold} AND blocking_issues is empty

Be objective and direct. Provide actionable advice in Chinese.
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
        )
