"""Structuring Agent - Extracts structured PRD from unstructured text."""

import json
import logging
import time
from pathlib import Path

from src.reqgate.adapters.llm import LLMClientWithRetry
from src.reqgate.schemas.internal import AgentState, PRD_Draft
from src.reqgate.workflow.errors import StructuringFailureError

logger = logging.getLogger(__name__)

# Default prompt template path
DEFAULT_PROMPT_PATH = Path("prompts/structuring_agent_v1.txt")

# Example output for prompt
EXAMPLE_OUTPUT = {
    "title": "Implement user data export feature for GDPR compliance",
    "user_story": "As a user, I want to export my data, so that I can comply with GDPR requirements",
    "acceptance_criteria": [
        "User can access 'Export Data' option in settings",
        "System generates CSV file with profile information",
        "System includes activity history in export",
        "Download completes within 30 seconds for typical data size",
    ],
    "edge_cases": [],
    "resources": ["GDPR compliance documentation"],
    "missing_info": [
        "Maximum data retention period",
        "File size limits for export",
        "Supported export formats (only CSV mentioned)",
    ],
    "clarification_questions": [
        "Should we support other export formats like JSON?",
        "What is the expected maximum file size for exports?",
        "Should exports include data from connected third-party services?",
    ],
}

# PRD_Draft schema for prompt
PRD_DRAFT_SCHEMA = {
    "title": "string (10-200 chars, starts with action verb)",
    "user_story": "string (As a [role], I want [feature], so that [benefit])",
    "acceptance_criteria": ["string (list of testable criteria, min 1)"],
    "edge_cases": ["string (optional, error scenarios mentioned in input)"],
    "resources": ["string (optional, URLs, tickets, docs mentioned)"],
    "missing_info": ["string (information gaps identified)"],
    "clarification_questions": ["string (questions to ask PM)"],
}


def load_prompt_template(prompt_path: Path | None = None) -> str:
    """
    Load the prompt template from file.

    Args:
        prompt_path: Path to prompt template file

    Returns:
        Prompt template string
    """
    path = prompt_path or DEFAULT_PROMPT_PATH
    if not path.exists():
        logger.warning(f"Prompt template not found at {path}, using embedded template")
        return _get_embedded_template()

    with open(path) as f:
        return f.read()


def _get_embedded_template() -> str:
    """Get embedded prompt template as fallback."""
    return """# Role
You are a requirements structuring assistant. Extract structured PRD from unstructured text.

# Critical Rules
1. ONLY extract information explicitly present in the input
2. DO NOT invent or hallucinate details
3. If information is missing, add to "missing_info"
4. If clarification needed, add to "clarification_questions"

# Input Text
{input_text}

# Output Schema
{prd_draft_schema}

# Output ONLY valid JSON matching the schema above.
"""


def build_prompt(input_text: str, prompt_template: str | None = None) -> str:
    """
    Build the complete prompt for the LLM.

    Args:
        input_text: Raw requirement text to structure
        prompt_template: Optional custom prompt template

    Returns:
        Formatted prompt string
    """
    template = prompt_template or load_prompt_template()

    return template.format(
        input_text=input_text,
        prd_draft_schema=json.dumps(PRD_DRAFT_SCHEMA, indent=2),
        example_output=json.dumps(EXAMPLE_OUTPUT, indent=2),
    )


def parse_llm_response(response: str) -> PRD_Draft:
    """
    Parse LLM response into PRD_Draft.

    Args:
        response: Raw LLM response string

    Returns:
        Validated PRD_Draft instance

    Raises:
        StructuringFailureError: If parsing or validation fails
    """
    # Try to extract JSON from response
    json_str = _extract_json(response)

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise StructuringFailureError(
            message=f"Failed to parse JSON from LLM response: {e}",
            details=f"Response: {response[:500]}...",
        ) from e

    # Validate against PRD_Draft schema
    try:
        return PRD_Draft.model_validate(data)
    except Exception as e:
        raise StructuringFailureError(
            message=f"LLM output failed schema validation: {e}",
            details=f"Data: {data}",
        ) from e


def _extract_json(text: str) -> str:
    """
    Extract JSON from text that may contain markdown code blocks.

    Args:
        text: Text potentially containing JSON

    Returns:
        Extracted JSON string
    """
    # Remove markdown code blocks if present
    text = text.strip()

    # Try to find JSON in code blocks
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        if end > start:
            return text[start:end].strip()

    if "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        if end > start:
            return text[start:end].strip()

    # Try to find JSON object directly
    if "{" in text and "}" in text:
        start = text.find("{")
        # Find matching closing brace
        depth = 0
        for i, char in enumerate(text[start:], start):
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]

    return text


def validate_no_hallucination(input_text: str, prd_draft: PRD_Draft) -> list[str]:
    """
    Check if PRD contains information not present in input.

    This is a basic heuristic check - it looks for key terms in acceptance
    criteria that don't appear in the input text.

    Args:
        input_text: Original input text
        prd_draft: Extracted PRD draft

    Returns:
        List of suspicious phrases (empty if clean)
    """
    suspicious = []
    input_lower = input_text.lower()

    # Check acceptance criteria for potential hallucinations
    for ac in prd_draft.acceptance_criteria:
        # Extract significant words (nouns, verbs) - simple heuristic
        words = [w.lower() for w in ac.split() if len(w) > 4]

        # Check if key words appear in input
        missing_words = [w for w in words if w not in input_lower]

        # If more than half of significant words are missing, flag it
        if len(words) > 0 and len(missing_words) > len(words) * 0.7:
            suspicious.append(f"AC may contain invented content: '{ac[:50]}...'")

    return suspicious


class StructuringAgent:
    """
    Agent that structures unstructured requirement text into PRD format.

    Uses LLM to extract user stories, acceptance criteria, and identify
    missing information from raw requirement text.
    """

    def __init__(self, prompt_path: Path | None = None) -> None:
        """
        Initialize the structuring agent.

        Args:
            prompt_path: Optional path to custom prompt template
        """
        self.prompt_template = load_prompt_template(prompt_path)
        self.llm_client = LLMClientWithRetry()

    def structure(self, raw_text: str, validate_hallucination: bool = True) -> PRD_Draft:
        """
        Structure raw requirement text into PRD format.

        Args:
            raw_text: Unstructured requirement text
            validate_hallucination: Whether to check for hallucinated content

        Returns:
            Structured PRD_Draft

        Raises:
            StructuringFailureError: If structuring fails
        """
        # Build prompt
        prompt = build_prompt(raw_text, self.prompt_template)

        # Call LLM
        try:
            response = self.llm_client.generate(prompt)
        except Exception as e:
            raise StructuringFailureError(
                message=f"LLM call failed: {e}",
                details=str(e),
            ) from e

        # Parse response
        prd_draft = parse_llm_response(response)

        # Validate for hallucination
        if validate_hallucination:
            warnings = validate_no_hallucination(raw_text, prd_draft)
            for warning in warnings:
                logger.warning(f"Potential hallucination: {warning}")

        return prd_draft


def structuring_agent_node(state: AgentState) -> AgentState:
    """
    LangGraph node for structuring agent.

    Extracts structured PRD from raw requirement text.

    Args:
        state: Current workflow state

    Returns:
        Updated state with structured_prd populated

    Note:
        On failure, this node logs the error but does NOT raise an exception.
        The workflow should check if structured_prd is None and handle fallback.
    """
    start_time = time.time()

    # Get input text
    raw_text = state["packet"].raw_text

    # Update execution times
    execution_times = dict(state.get("execution_times", {}))
    error_logs = list(state.get("error_logs", []))

    try:
        agent = StructuringAgent()
        prd_draft = agent.structure(raw_text)

        execution_times["structuring"] = time.time() - start_time

        return {
            **state,
            "structured_prd": prd_draft,
            "current_stage": "structuring_complete",
            "execution_times": execution_times,
        }

    except StructuringFailureError as e:
        logger.error(f"Structuring failed: {e}")
        error_logs.append(f"Structuring: {e}")
        execution_times["structuring"] = time.time() - start_time

        # Return state with structured_prd as None (triggers fallback)
        return {
            **state,
            "structured_prd": None,
            "current_stage": "structuring_failed",
            "error_logs": error_logs,
            "execution_times": execution_times,
        }

    except Exception as e:
        logger.error(f"Unexpected error in structuring: {e}")
        error_logs.append(f"Structuring unexpected error: {e}")
        execution_times["structuring"] = time.time() - start_time

        return {
            **state,
            "structured_prd": None,
            "current_stage": "structuring_failed",
            "error_logs": error_logs,
            "execution_times": execution_times,
        }
