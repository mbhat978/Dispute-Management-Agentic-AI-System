"""
State Management for Banking Dispute Resolution System

This module defines the DisputeState TypedDict that flows through the
multi-agent dispute resolution workflow.
"""

from typing import TypedDict, List, Dict, Any


class DisputeState(TypedDict):
    """
    State object passed between agents in the LangGraph workflow.
    
    This TypedDict defines all the information that flows through the
    multi-agent dispute resolution system. Each agent can read from and
    write to this state as it processes the dispute.
    
    Attributes:
        ticket_id (int): Unique identifier for the dispute ticket
        customer_id (int): Unique identifier for the customer
        customer_query (str): The customer's dispute description/reason
        dispute_category (str): Category of dispute (e.g., 'fraud', 'duplicate', 'atm_failure', 'merchant_dispute')
        gathered_data (dict): Dictionary storing outputs from various tool calls
        audit_trail (list[str]): List of agent thoughts, actions, and observations for transparency
        final_decision (str): The final resolution decision (e.g., 'auto_approved', 'auto_rejected', 'human_review_required')
    """
    ticket_id: int
    customer_id: int
    customer_query: str
    dispute_category: str
    gathered_data: Dict[str, Any]
    audit_trail: List[str]
    final_decision: str


def initialize_dispute_state(
    ticket_id: int,
    customer_id: int,
    customer_query: str,
    dispute_category: str = "unknown"
) -> DisputeState:
    """
    Initialize a new DisputeState object for a dispute ticket.
    
    Args:
        ticket_id (int): The dispute ticket ID.
        customer_id (int): The customer ID.
        customer_query (str): The customer's dispute description.
        dispute_category (str, optional): Category of dispute. Defaults to "unknown".
        
    Returns:
        DisputeState: Initialized state object.
        
    Example:
        state = initialize_dispute_state(
            ticket_id=1,
            customer_id=2,
            customer_query="I did not authorize this international transaction",
            dispute_category="fraud"
        )
    """
    return DisputeState(
        ticket_id=ticket_id,
        customer_id=customer_id,
        customer_query=customer_query,
        dispute_category=dispute_category,
        gathered_data={},
        audit_trail=[],
        final_decision=""
    )

# Made with Bob
