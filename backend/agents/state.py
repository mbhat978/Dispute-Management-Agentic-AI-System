"""
State Management for Banking Dispute Resolution System

This module defines the DisputeState TypedDict that flows through the
multi-agent dispute resolution workflow with enhanced ReAct capabilities.
"""

from typing import TypedDict, List, Dict, Any, NotRequired
from datetime import datetime


class AgentMemory(TypedDict):
    """
    Lightweight per-agent memory used across workflow iterations.
    """
    agent_name: str
    past_actions: List[Dict[str, Any]]
    learned_patterns: Dict[str, Any]
    confidence_history: List[float]


class DisputeState(TypedDict):
    """
    Enhanced state object for ReAct-driven multi-agent workflow.
    
    This TypedDict defines all the information that flows through the
    multi-agent dispute resolution system. Each agent can read from and
    write to this state as it processes the dispute.
    
    Core Attributes:
        ticket_id (int): Unique identifier for the dispute ticket
        customer_id (int): Unique identifier for the customer
        customer_query (str): The customer's dispute description/reason
        dispute_category (str): Category of dispute (e.g., 'fraud', 'duplicate', 'atm_failure', 'merchant_dispute')
        gathered_data (dict): Dictionary storing outputs from various tool calls
        audit_trail (list[str]): List of agent thoughts, actions, and observations for transparency
        final_decision (str): The final resolution decision (e.g., 'auto_approved', 'auto_rejected', 'human_review_required')
    
    Enhanced ReAct Attributes:
        triage_confidence (float): Confidence score from triage classification (0.0-1.0)
        investigation_confidence (float): Confidence in gathered evidence (0.0-1.0)
        decision_confidence (float): Confidence in final decision (0.0-1.0)
        iteration_count (int): Number of investigation iterations performed
        max_iterations (int): Maximum allowed iterations to prevent infinite loops
        investigation_summary (str): LLM-generated summary of investigation findings
        decision_reasoning (dict): Detailed reasoning from decision agent
        working_memory (dict): Shared memory for inter-agent communication
        agent_memories (dict): Per-agent memory across workflow iterations
        processing_start_time (str): ISO timestamp when processing started
        processing_duration_seconds (float): Total workflow duration in seconds
        evidence_quality_score (float): Quality assessment of gathered evidence
        decision_quality_score (float): Quality assessment of the final decision
        escalation_reasons (list[str]): Reasons for human escalation if applicable
        human_review_priority (str): Priority level for human review (low/medium/high/urgent)
    """
    # Core fields (required)
    ticket_id: int
    customer_id: int
    customer_query: str
    dispute_category: str
    gathered_data: Dict[str, Any]
    audit_trail: List[str]
    final_decision: str
    
    # Human-in-the-loop override field
    human_override: NotRequired[str | None]
    
    # Enhanced ReAct fields (optional with NotRequired)
    triage_confidence: NotRequired[float]
    investigation_confidence: NotRequired[float]
    decision_confidence: NotRequired[float]
    iteration_count: NotRequired[int]
    max_iterations: NotRequired[int]
    investigation_summary: NotRequired[str]
    decision_reasoning: NotRequired[Dict[str, Any]]
    working_memory: NotRequired[Dict[str, Any]]
    agent_memories: NotRequired[Dict[str, AgentMemory]]
    processing_start_time: NotRequired[str]
    processing_duration_seconds: NotRequired[float]
    evidence_quality_score: NotRequired[float]
    decision_quality_score: NotRequired[float]
    escalation_reasons: NotRequired[List[str]]
    human_review_priority: NotRequired[str]


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
        final_decision="",
        triage_confidence=0.0,
        investigation_confidence=0.0,
        decision_confidence=0.0,
        iteration_count=0,
        max_iterations=3,
        investigation_summary="",
        decision_reasoning={},
        working_memory={},
        agent_memories={
            "triage": {
                "agent_name": "triage",
                "past_actions": [],
                "learned_patterns": {},
                "confidence_history": []
            },
            "investigator": {
                "agent_name": "investigator",
                "past_actions": [],
                "learned_patterns": {},
                "confidence_history": []
            },
            "decision": {
                "agent_name": "decision",
                "past_actions": [],
                "learned_patterns": {},
                "confidence_history": []
            }
        },
        processing_start_time=datetime.utcnow().isoformat(),
        processing_duration_seconds=0.0,
        evidence_quality_score=0.0,
        decision_quality_score=0.0,
        escalation_reasons=[],
        human_review_priority="low"
    )

# Made with Bob
