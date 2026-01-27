"""
Hard Check #1: Structure completeness validation node.

Validates PRD_Draft structure before scoring to ensure minimum quality standards.
This is a deterministic check (no LLM) that runs after Structuring Agent succeeds.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.reqgate.schemas.internal import AgentState

logger = logging.getLogger(__name__)


# Validation thresholds
MIN_AC_COUNT = 2
MIN_USER_STORY_LENGTH = 20
MIN_TITLE_LENGTH = 10
MAX_TITLE_LENGTH = 200


# Action verbs for title validation
ACTION_VERBS = (
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


def hard_check_structure_node(state: AgentState) -> AgentState:
    """
    Validate PRD structure completeness (Hard Check #1).

    This node performs deterministic validation on the structured PRD
    to ensure it meets minimum quality standards before scoring.

    Checks:
    1. AC count >= 2
    2. User Story length >= 20 characters
    3. Title length between 10-200 characters
    4. Title starts with an action verb

    Args:
        state: Current workflow state

    Returns:
        Updated state with structure_check_passed and structure_errors
    """
    start_time = time.time()
    state["current_stage"] = "structure_check"

    errors: list[str] = []
    structured_prd = state.get("structured_prd")

    # Skip check if no structured PRD (fallback mode)
    if structured_prd is None:
        logger.info("No structured PRD - skipping structure check")
        state["structure_check_passed"] = None
        state["structure_errors"] = []
        state["execution_times"]["structure_check"] = time.time() - start_time
        return state

    logger.info("Starting structure check (Hard Check #1)")

    # Check 1: AC count >= 2
    ac_count = len(structured_prd.acceptance_criteria)
    if ac_count < MIN_AC_COUNT:
        error = f"Insufficient acceptance criteria: found {ac_count}, minimum required is {MIN_AC_COUNT}"
        errors.append(error)
        logger.warning(error)

    # Check 2: User Story length >= 20 characters
    user_story_length = len(structured_prd.user_story.strip())
    if user_story_length < MIN_USER_STORY_LENGTH:
        error = f"User story too short: {user_story_length} characters, minimum required is {MIN_USER_STORY_LENGTH}"
        errors.append(error)
        logger.warning(error)

    # Check 3: Title length between 10-200 characters
    title_length = len(structured_prd.title.strip())
    if title_length < MIN_TITLE_LENGTH:
        error = f"Title too short: {title_length} characters, minimum required is {MIN_TITLE_LENGTH}"
        errors.append(error)
        logger.warning(error)
    elif title_length > MAX_TITLE_LENGTH:
        error = f"Title too long: {title_length} characters, maximum allowed is {MAX_TITLE_LENGTH}"
        errors.append(error)
        logger.warning(error)

    # Check 4: Title starts with action verb
    first_word = structured_prd.title.strip().split()[0].lower() if structured_prd.title.strip() else ""
    if not first_word.startswith(ACTION_VERBS):
        error = f"Title should start with an action verb (e.g., Implement, Add, Create). Got: '{first_word}'"
        errors.append(error)
        logger.warning(error)

    # Set results
    passed = len(errors) == 0
    state["structure_check_passed"] = passed
    state["structure_errors"] = errors

    if passed:
        logger.info("Structure check passed")
    else:
        logger.warning(f"Structure check failed with {len(errors)} error(s)")

    # Record execution time
    elapsed = time.time() - start_time
    state["execution_times"]["structure_check"] = elapsed
    logger.debug(f"Structure check completed in {elapsed:.4f}s")

    return state
