"""
Orchestrator for Banking Dispute Management System

This module builds and compiles the LangGraph workflow that chains together
the triage, investigator, and decision agents.
"""

from langgraph.graph import StateGraph, END
from .state import DisputeState
from .triage import triage_node
from .investigator import investigator_node
from .decision import decision_node


def build_dispute_resolution_graph():
    """
    Build and compile the LangGraph workflow for dispute resolution.
    
    This function creates a state graph that chains together the three agent nodes:
    triage → investigator → decision
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Initialize the graph with DisputeState
    workflow = StateGraph(DisputeState)
    
    # Add the three agent nodes
    workflow.add_node("triage", triage_node)
    workflow.add_node("investigator", investigator_node)
    workflow.add_node("decision", decision_node)
    
    # Define the flow
    # Set triage as the entry point
    workflow.set_entry_point("triage")
    
    # Add edges to define the workflow
    workflow.add_edge("triage", "investigator")
    workflow.add_edge("investigator", "decision")
    workflow.add_edge("decision", END)
    
    # Compile the graph
    app = workflow.compile()
    
    return app


# Create a singleton instance of the compiled graph
dispute_resolution_workflow = build_dispute_resolution_graph()

# Made with Bob
