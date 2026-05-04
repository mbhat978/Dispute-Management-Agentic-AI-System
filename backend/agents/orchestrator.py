"""
Orchestrator for Banking Dispute Management System

This module builds and compiles the LangGraph workflow that chains together
the triage, data retrieval, fraud analyst, vision expert, and decision agents.
"""

from typing import Any, Dict, Literal
from loguru import logger
from langgraph.graph import StateGraph, END
from .state import DisputeState
from .triage_react import triage_node_react
from .investigator import investigator_node
from .data_retrieval import data_retrieval_node
from .fraud_analyst import fraud_node
from .vision_expert import vision_node
from .decision import decision_node
from .config import (
    CONFIDENCE_THRESHOLD_MEDIUM,
    ESCALATION_CONFIDENCE_THRESHOLD,
    MAX_WORKFLOW_ITERATIONS,
)


def human_review_node(state: DisputeState) -> Dict[str, Any]:
    """
    Dummy node that pauses workflow for human review.
    The graph will interrupt before this node, allowing HITL intervention.
    """
    logger.info("[ORCHESTRATOR] Pausing at human_review_node")
    return {"ticket_id": state.get("ticket_id")}


def clarification_node(state: DisputeState) -> Dict[str, Any]:
    """
    Add clarification requests to working memory when triage confidence is low.
    """
    working_memory = dict(state.get("working_memory", {}))
    audit_trail = list(state["audit_trail"])
    questions = working_memory.get("clarification_questions", [])

    logger.info(
        f"[ORCHESTRATOR] clarification_node | ticket_id={state.get('ticket_id')} | "
        f"triage_confidence={state.get('triage_confidence', 0.0):.2f}"
    )

    audit_trail.append(
        "Clarification Agent: Low triage confidence detected. "
        f"Generated clarification questions: {questions if questions else ['Please confirm the dispute details.']}"
    )

    working_memory["clarification_needed"] = True
    logger.info(
        f"[ORCHESTRATOR] clarification_requested | questions={questions if questions else ['Please confirm the dispute details.']}"
    )
    return {
        "working_memory": working_memory,
        "audit_trail": audit_trail,
    }


def re_investigate_node(state: DisputeState) -> Dict[str, Any]:
    """
    Mark the state for another investigation pass when evidence is insufficient.
    """
    iteration_count = state.get("iteration_count", 0) + 1
    working_memory = dict(state.get("working_memory", {}))
    audit_trail = list(state["audit_trail"])

    logger.info(
        f"[ORCHESTRATOR] re_investigate_node | ticket_id={state.get('ticket_id')} | "
        f"next_iteration={iteration_count}"
    )

    working_memory["reinvestigation_requested"] = True
    logger.info(f"[ORCHESTRATOR] re-investigation requested | iteration={iteration_count}")
    audit_trail.append(
        f"Orchestrator: Re-investigation requested due to low evidence sufficiency. Iteration {iteration_count}."
    )

    return {
        "iteration_count": iteration_count,
        "working_memory": working_memory,
        "audit_trail": audit_trail,
    }


def route_after_triage(state: DisputeState) -> Literal["clarification", "investigator"]:
    """
    Route low-confidence triage results through clarification first.
    """
    confidence = state.get("triage_confidence", 0.0)
    requires_clarification = state.get("working_memory", {}).get("requires_clarification", False)

    if requires_clarification or confidence < CONFIDENCE_THRESHOLD_MEDIUM:
        logger.info(
            f"[ORCHESTRATOR] route_after_triage -> clarification | "
            f"confidence={confidence:.2f} | requires_clarification={requires_clarification}"
        )
        return "clarification"
    logger.info(
        f"[ORCHESTRATOR] route_after_triage -> investigator | "
        f"confidence={confidence:.2f} | requires_clarification={requires_clarification}"
    )
    return "investigator"


def route_after_investigation(state: DisputeState) -> Literal["re_investigate", "decision"]:
    """
    Route to re-investigation if evidence is insufficient and iterations remain.
    Otherwise proceed to decision.
    """
    confidence = state.get("investigation_confidence", 0.0)
    quality = state.get("evidence_quality_score", 0.0)
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", MAX_WORKFLOW_ITERATIONS)
    summary = state.get("investigation_summary", "").lower()
    
    insufficient = (
        confidence < CONFIDENCE_THRESHOLD_MEDIUM
        or quality < CONFIDENCE_THRESHOLD_MEDIUM
        or "insufficient evidence" in summary
        or "need more information" in summary
    )
    
    if insufficient and iteration_count < max_iterations:
        logger.info(
            f"[ORCHESTRATOR] route_after_investigation -> re_investigate | "
            f"confidence={confidence:.2f} | quality={quality:.2f} | iteration={iteration_count}/{max_iterations}"
        )
        return "re_investigate"
    
    logger.info(
        f"[ORCHESTRATOR] route_after_investigation -> decision | "
        f"confidence={confidence:.2f} | quality={quality:.2f} | iteration={iteration_count}/{max_iterations}"
    )
    return "decision"


def route_specialists(state: dict) -> list[str]:
    """
    Dynamic conditional router based on the Supervisor's plan.
    Routes to specialist agents (fraud_analyst, vision_expert) in parallel
    based on the routing_plan created by the investigator (Supervisor).
    
    If no specialists are needed, goes straight to decision.
    """
    plan = state.get("routing_plan", [])
    next_nodes = []
    
    if "vision_expert" in plan:
        logger.info("[ORCHESTRATOR] route_specialists -> vision_expert (from Supervisor plan)")
        next_nodes.append("vision_expert")
    if "fraud_analyst" in plan:
        logger.info("[ORCHESTRATOR] route_specialists -> fraud_analyst (from Supervisor plan)")
        next_nodes.append("fraud_analyst")
        
    # If no specialists are needed, go straight to decision
    if not next_nodes:
        logger.info("[ORCHESTRATOR] route_specialists -> decision (no specialists needed)")
        return ["decision"]
        
    # Otherwise, run the required specialists in parallel!
    logger.info(f"[ORCHESTRATOR] route_specialists -> {next_nodes} (parallel execution)")
    return next_nodes


def route_after_decision(state: DisputeState) -> Literal["data_retrieval", "human_review", "END"]:
    """
    Loop back to data retrieval only when a follow-up pass was explicitly requested
    and iterations remain. Route to human_review when decision requires human intervention.
    """
    confidence = state.get("decision_confidence", 0.0)
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", MAX_WORKFLOW_ITERATIONS)
    final_decision = state.get("final_decision", "")
    working_memory = state.get("working_memory", {})

    if final_decision == "human_review_required":
        logger.success("[ORCHESTRATOR] route_after_decision -> human_review | final_decision=HUMAN_REVIEW_REQUIRED")
        return "human_review"

    if (
        working_memory.get("reinvestigation_requested", False)
        and confidence < ESCALATION_CONFIDENCE_THRESHOLD
        and iteration_count < max_iterations
    ):
        logger.info(
            f"[ORCHESTRATOR] route_after_decision -> data_retrieval | "
            f"confidence={confidence:.2f} | iteration={iteration_count}/{max_iterations}"
        )
        return "data_retrieval"

    logger.success(
        f"[ORCHESTRATOR] route_after_decision -> END | "
        f"final_decision={final_decision.upper() if final_decision else 'UNKNOWN'}"
    )
    return "END"


def build_dispute_resolution_graph():
    """
    Build and compile the LangGraph workflow for dispute resolution.
    
    This function creates a dynamic state graph with Supervisor-based conditional routing:
    triage → clarification/investigator → re_investigate/data_retrieval → [conditional specialists] → decision → END or loop
    
    The workflow includes:
    - Clarification loop: Low triage confidence triggers clarification requests
    - Re-investigation loop: Insufficient evidence triggers another investigation pass
    - Supervisor routing: The investigator creates a routing_plan that determines which specialists
      (fraud_analyst, vision_expert) should run in parallel after data_retrieval
    
    The checkpointer must be attached separately before execution.
    
    Returns:
        Compiled StateGraph ready for execution (checkpointer to be attached at runtime)
    """
    logger.info("[ORCHESTRATOR] Building dispute resolution graph with Supervisor-based dynamic routing")
    
    # Initialize the graph with DisputeState
    workflow = StateGraph(DisputeState)

    # Add all agent nodes including the Supervisor (investigator)
    workflow.add_node("triage", triage_node_react)
    workflow.add_node("clarification", clarification_node)
    workflow.add_node("investigator", investigator_node)  # The Supervisor
    workflow.add_node("data_retrieval", data_retrieval_node)
    workflow.add_node("fraud_analyst", fraud_node)
    workflow.add_node("vision_expert", vision_node)
    workflow.add_node("re_investigate", re_investigate_node)
    workflow.add_node("decision", decision_node)
    workflow.add_node("human_review", human_review_node)

    # Set entry point
    workflow.set_entry_point("triage")

    # Conditional routing after triage
    workflow.add_conditional_edges(
        "triage",
        route_after_triage,
        {
            "clarification": "clarification",
            "investigator": "investigator",  # Route to Supervisor first
        }
    )

    # After clarification, continue to Supervisor (investigator)
    workflow.add_edge("clarification", "investigator")

    # Conditional routing after investigation - check if re-investigation is needed
    workflow.add_conditional_edges(
        "investigator",
        route_after_investigation,
        {
            "re_investigate": "re_investigate",
            "decision": "data_retrieval",  # Proceed to data retrieval if evidence is sufficient
        }
    )

    # Re-investigation loops back to investigator for another pass
    workflow.add_edge("re_investigate", "investigator")

    # Data Retrieval hands off to the conditional parallel router
    # This uses the Supervisor's routing_plan to determine which specialists to activate
    workflow.add_conditional_edges(
        "data_retrieval",
        route_specialists,
        {
            "vision_expert": "vision_expert",
            "fraud_analyst": "fraud_analyst",
            "decision": "decision"
        }
    )

    # Specialists converge on the Decision Agent
    workflow.add_edge("vision_expert", "decision")
    workflow.add_edge("fraud_analyst", "decision")

    # Conditional routing after decision
    workflow.add_conditional_edges(
        "decision",
        route_after_decision,
        {
            "data_retrieval": "investigator",  # Loop back through Supervisor
            "human_review": "human_review",
            "END": END,
        }
    )

    # After human review, loop back to decision for final processing
    workflow.add_edge("human_review", "decision")

    # Compile the graph with interrupt before human_review node for HITL
    # Checkpointer will be attached at runtime via context manager
    app = workflow.compile(interrupt_before=['human_review'])

    logger.success("[ORCHESTRATOR] Dispute resolution graph compiled successfully with Supervisor-based dynamic routing (checkpointer to be attached at runtime)")
    return app


# Create the workflow instance (synchronous initialization)
dispute_resolution_workflow = build_dispute_resolution_graph()


def get_workflow():
    """Get the dispute resolution workflow instance."""
    return dispute_resolution_workflow

# Made with Bob
