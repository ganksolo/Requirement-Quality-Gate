"""
LangGraph workflow definition for requirement processing.

Implements the DAG: Guardrail → Structuring → Scoring → Gate
with fallback support when structuring fails.
"""

import logging
import time
from typing import Literal

from langgraph.graph import END, StateGraph
from src.reqgate.agents.scoring import ScoringAgent
from src.reqgate.gates.decision import HardGate
from src.reqgate.schemas.config import WorkflowConfig
from src.reqgate.schemas.inputs import RequirementPacket
from src.reqgate.schemas.internal import AgentState, PRD_Draft
from src.reqgate.workflow.errors import (
    GuardrailRejectionError,
    WorkflowExecutionError,
)
from src.reqgate.workflow.nodes.input_guardrail import input_guardrail_node
from src.reqgate.workflow.nodes.structuring_agent import structuring_agent_node

logger = logging.getLogger(__name__)


# ============================================
# Node Implementations
# ============================================


def scoring_node(state: AgentState) -> AgentState:
    """
    Scoring agent node - evaluates requirement quality.

    This node:
    1. Uses structured PRD if available
    2. Falls back to raw text if structuring failed
    3. Applies scoring penalty in fallback mode

    Args:
        state: Current workflow state

    Returns:
        Updated state with score_report
    """
    start_time = time.time()
    state["current_stage"] = "scoring"

    try:
        logger.info("Starting scoring node")

        # Get the scoring input
        packet = state["packet"]
        structured_prd = state.get("structured_prd")

        # Prepare scoring input
        scoring_input = _prepare_scoring_input(packet, structured_prd)

        # Run scoring
        agent = ScoringAgent()
        report = agent.score(scoring_input)

        # Apply fallback penalty if applicable
        if state.get("fallback_activated", False):
            logger.warning("Applying fallback score penalty (-5 points)")
            report.total_score = max(0, report.total_score - 5)

        state["score_report"] = report
        logger.info(f"Scoring complete: {report.total_score}/100")

    except Exception as e:
        error_msg = f"Scoring failed: {e}"
        logger.error(error_msg)
        state["error_logs"].append(error_msg)
        # Don't raise - let gate handle missing score
    finally:
        elapsed = time.time() - start_time
        state["execution_times"]["scoring"] = elapsed
        logger.debug(f"Scoring node completed in {elapsed:.2f}s")

    return state


def _prepare_scoring_input(
    packet: RequirementPacket,
    structured_prd: PRD_Draft | None,
) -> RequirementPacket:
    """
    Prepare input for scoring agent.

    If structured PRD is available, format it as enhanced raw_text.
    Otherwise, use original packet.

    Args:
        packet: Original requirement packet
        structured_prd: Structured PRD (may be None)

    Returns:
        RequirementPacket for scoring
    """
    if structured_prd is None:
        return packet

    # Format structured PRD as enhanced text
    formatted_text = format_prd_for_scoring(structured_prd)

    return RequirementPacket(
        raw_text=formatted_text,
        source_type=packet.source_type,
        project_key=packet.project_key,
        priority=packet.priority,
        ticket_type=packet.ticket_type,
    )


def format_prd_for_scoring(prd: PRD_Draft) -> str:
    """
    Format PRD_Draft as text for scoring.

    Creates a well-structured representation that the scoring
    agent can evaluate effectively.

    Args:
        prd: Structured PRD draft

    Returns:
        Formatted text for scoring
    """
    sections = [
        f"# {prd.title}",
        "",
        "## User Story",
        prd.user_story,
        "",
        "## Acceptance Criteria",
    ]

    for i, ac in enumerate(prd.acceptance_criteria, 1):
        sections.append(f"{i}. {ac}")

    if prd.edge_cases:
        sections.append("")
        sections.append("## Edge Cases")
        for case in prd.edge_cases:
            sections.append(f"- {case}")

    if prd.resources:
        sections.append("")
        sections.append("## Resources")
        for resource in prd.resources:
            sections.append(f"- {resource}")

    if prd.missing_info:
        sections.append("")
        sections.append("## Identified Gaps")
        for info in prd.missing_info:
            sections.append(f"- {info}")

    return "\n".join(sections)


def hard_gate_node(state: AgentState) -> AgentState:
    """
    Hard gate node - makes pass/reject decision.

    Args:
        state: Current workflow state

    Returns:
        Updated state with gate_decision
    """
    start_time = time.time()
    state["current_stage"] = "gate"

    try:
        logger.info("Starting hard gate node")

        score_report = state.get("score_report")

        if score_report is None:
            # No score report - automatic reject
            logger.warning("No score report available - rejecting")
            state["gate_decision"] = False
            state["error_logs"].append("Gate decision: REJECT (no score report)")
        else:
            # Make gate decision
            gate = HardGate()
            decision = gate.decide(score_report, state["packet"].ticket_type)
            state["gate_decision"] = decision == "PASS"

            logger.info(f"Gate decision: {decision}")

    except Exception as e:
        error_msg = f"Gate decision failed: {e}"
        logger.error(error_msg)
        state["error_logs"].append(error_msg)
        state["gate_decision"] = False
    finally:
        elapsed = time.time() - start_time
        state["execution_times"]["gate"] = elapsed
        logger.debug(f"Gate node completed in {elapsed:.2f}s")

    return state


# ============================================
# Routing Functions
# ============================================


def should_fallback(state: AgentState) -> Literal["scoring", "fallback_scoring"]:
    """
    Determine if fallback mode should be used.

    Called after structuring node to decide the next step.

    Args:
        state: Current workflow state

    Returns:
        "scoring" if structured PRD available, "fallback_scoring" otherwise
    """
    structured_prd = state.get("structured_prd")

    if structured_prd is not None:
        logger.info("Structured PRD available - proceeding to scoring")
        return "scoring"
    else:
        logger.warning("No structured PRD - activating fallback mode")
        return "fallback_scoring"


def activate_fallback(state: AgentState) -> AgentState:
    """
    Activate fallback mode when structuring fails.

    Sets the fallback flag before proceeding to scoring.

    Args:
        state: Current workflow state

    Returns:
        Updated state with fallback_activated=True
    """
    state["fallback_activated"] = True
    state["error_logs"].append("Fallback activated: scoring will use raw text")
    logger.warning("Fallback mode activated")
    return state


# ============================================
# Workflow Factory
# ============================================


def create_workflow(config: WorkflowConfig | None = None) -> StateGraph:
    """
    Create the requirement processing workflow.

    The workflow follows this DAG:
    ```
    [START] → [guardrail] → [structuring] → {check}
                                              ↓
                                     ┌───────────────┐
                                     ↓               ↓
                                [scoring]    [fallback] → [scoring]
                                     ↓               ↓
                                  [gate] ←──────────┘
                                     ↓
                                   [END]
    ```

    Args:
        config: Workflow configuration (uses defaults if None)

    Returns:
        Compiled StateGraph workflow
    """
    if config is None:
        config = WorkflowConfig()

    logger.info(f"Creating workflow with config: {config.model_dump()}")

    # Create state graph
    graph = StateGraph(AgentState)

    # Add nodes
    if config.enable_guardrail:
        graph.add_node("guardrail", input_guardrail_node)

    if config.enable_structuring:
        graph.add_node("structuring", structuring_agent_node)

    graph.add_node("scoring", scoring_node)
    graph.add_node("gate", hard_gate_node)

    if config.enable_fallback:
        graph.add_node("fallback", activate_fallback)

    # Define edges based on configuration
    if config.enable_guardrail and config.enable_structuring:
        # Full workflow: guardrail → structuring → (check) → scoring → gate
        graph.set_entry_point("guardrail")
        graph.add_edge("guardrail", "structuring")

        if config.enable_fallback:
            # Add conditional edge for fallback
            graph.add_conditional_edges(
                "structuring",
                should_fallback,
                {
                    "scoring": "scoring",
                    "fallback_scoring": "fallback",
                },
            )
            graph.add_edge("fallback", "scoring")
        else:
            graph.add_edge("structuring", "scoring")

    elif config.enable_guardrail:
        # Guardrail only: guardrail → scoring → gate
        graph.set_entry_point("guardrail")
        graph.add_edge("guardrail", "scoring")

    elif config.enable_structuring:
        # Structuring only: structuring → (check) → scoring → gate
        graph.set_entry_point("structuring")

        if config.enable_fallback:
            graph.add_conditional_edges(
                "structuring",
                should_fallback,
                {
                    "scoring": "scoring",
                    "fallback_scoring": "fallback",
                },
            )
            graph.add_edge("fallback", "scoring")
        else:
            graph.add_edge("structuring", "scoring")

    else:
        # Minimal: scoring → gate
        graph.set_entry_point("scoring")

    # Final edges
    graph.add_edge("scoring", "gate")
    graph.add_edge("gate", END)

    # Compile and return
    compiled = graph.compile()
    logger.info("Workflow compiled successfully")

    return compiled


# ============================================
# Workflow Execution
# ============================================


def create_initial_state(packet: RequirementPacket) -> AgentState:
    """
    Create initial workflow state from a requirement packet.

    Args:
        packet: Input requirement

    Returns:
        Initialized AgentState
    """
    return AgentState(
        packet=packet,
        structured_prd=None,
        score_report=None,
        gate_decision=None,
        retry_count=0,
        error_logs=[],
        current_stage="init",
        fallback_activated=False,
        execution_times={},
    )


def run_workflow(
    packet: RequirementPacket,
    config: WorkflowConfig | None = None,
) -> AgentState:
    """
    Execute the requirement processing workflow.

    This is the main entry point for processing requirements.

    Args:
        packet: Input requirement packet
        config: Optional workflow configuration

    Returns:
        Final workflow state with all results

    Raises:
        GuardrailRejectionError: If input is rejected by guardrail
        WorkflowExecutionError: If workflow fails unexpectedly
    """
    start_time = time.time()
    logger.info(f"Starting workflow for packet: {packet.project_key}")

    try:
        # Create workflow and initial state
        workflow = create_workflow(config)
        state = create_initial_state(packet)

        # Execute workflow
        final_state = workflow.invoke(state)

        # Log completion
        total_time = time.time() - start_time
        logger.info(
            f"Workflow completed in {total_time:.2f}s",
            extra={
                "total_time": total_time,
                "gate_decision": final_state.get("gate_decision"),
                "fallback_activated": final_state.get("fallback_activated"),
            },
        )

        return final_state

    except GuardrailRejectionError:
        # Re-raise guardrail rejections as-is
        raise

    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"Workflow failed after {total_time:.2f}s: {e}")
        raise WorkflowExecutionError(
            message=f"Workflow execution failed: {e}",
            stage="workflow",
        ) from e
