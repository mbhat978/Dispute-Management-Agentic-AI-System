"""
Orchestrator for Banking Dispute Management System

This module builds and compiles the LangGraph workflow that chains together
the triage, investigator, and decision agents.
"""

from typing import Any, Dict, Literal
from langgraph.graph import StateGraph, END
from .state import DisputeState
from .triage_react import triage_node_react
from .investigator import investigator_node
from .decision import decision_node
from .config import (
    CONFIDENCE_THRESHOLD_MEDIUM,
    ESCALATION_CONFIDENCE_THRESHOLD,
    MAX_WORKFLOW_ITERATIONS,
)


def clarification_node(state: DisputeState) -> Dict[str, Any]:
    """
    Add clarification requests to working memory when triage confidence is low.
    """
    working_memory = dict(state.get("working_memory", {}))
    audit_trail = list(state["audit_trail"])
    questions = working_memory.get("clarification_questions", [])

    audit_trail.append(
        "Clarification Agent: Low triage confidence detected. "
        f"Generated clarification questions: {questions if questions else ['Please confirm the dispute details.']}"
    )

    working_memory["clarification_needed"] = True
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

    working_memory["reinvestigation_requested"] = True
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
        return "clarification"
    return "investigator"


def route_after_investigation(state: DisputeState) -> Literal["re_investigate", "decision"]:
    """
    Re-investigate if evidence quality/confidence is too low and iterations remain.
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
        return "re_investigate"
    return "decision"


def route_after_decision(state: DisputeState) -> Literal["investigator", "END"]:
    """
    Loop back to investigation for low-confidence decisions while under iteration cap.
    """
    confidence = state.get("decision_confidence", 0.0)
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", MAX_WORKFLOW_ITERATIONS)

    if confidence < ESCALATION_CONFIDENCE_THRESHOLD and iteration_count < max_iterations:
        return "investigator"
    return "END"


def build_dispute_resolution_graph():
    """
    Build and compile the LangGraph workflow for dispute resolution.
    
    This function creates a dynamic state graph for ReAct-style dispute resolution:
    triage → clarification/investigator → re_investigate/decision → END or loop
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Initialize the graph with DisputeState
    workflow = StateGraph(DisputeState)

    # Add the agent nodes
    workflow.add_node("triage", triage_node_react)
    workflow.add_node("clarification", clarification_node)
    workflow.add_node("investigator", investigator_node)
    workflow.add_node("re_investigate", re_investigate_node)
    workflow.add_node("decision", decision_node)

    # Set entry point
    workflow.set_entry_point("triage")

    # Conditional routing after triage
    workflow.add_conditional_edges(
        "triage",
        route_after_triage,
        {
            "clarification": "clarification",
            "investigator": "investigator",
        }
    )

    # After clarification, continue investigation
    workflow.add_edge("clarification", "investigator")

    # Conditional routing after investigation
    workflow.add_conditional_edges(
        "investigator",
        route_after_investigation,
        {
            "re_investigate": "re_investigate",
            "decision": "decision",
        }
    )

    # Re-investigation feeds back into decision with updated state
    workflow.add_edge("re_investigate", "decision")

    # Conditional routing after decision
    workflow.add_conditional_edges(
        "decision",
        route_after_decision,
        {
            "investigator": "investigator",
            "END": END,
        }
    )

    # Compile the graph
    app = workflow.compile()

    return app


# Create a singleton instance of the compiled graph
dispute_resolution_workflow = build_dispute_resolution_graph()

# Made with Bob
