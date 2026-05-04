"""
Triage Agent for Banking Dispute Management System

This module contains the triage agent that analyzes customer queries
and categorizes disputes into predefined categories.
"""

from typing import Dict, Any
import logging
from .state import DisputeState


# Dispute categories for classification
DISPUTE_CATEGORIES = {
    "fraud": "Fraudulent or unauthorized transaction",
    "duplicate": "Duplicate charge or multiple identical transactions",
    "atm_failure": "ATM did not dispense cash but amount was debited",
    "merchant_dispute": "Dispute with merchant about goods/services",
    "failed_transaction": "Transaction failed but amount was deducted",
    "loan_dispute": "Dispute related to loan account or EMI",
    "refund_not_received": "Refund not received from merchant",
    "unknown": "Category not yet determined"
}


logger = logging.getLogger("dispute_management.agents.triage.rule_based")


def triage_node(state: DisputeState) -> Dict[str, Any]:
    """
    Triage Agent: Analyzes the customer query and categorizes the dispute.
    
    This agent uses an LLM to understand the customer's complaint and
    classify it into one of the predefined dispute categories.
    
    Args:
        state (DisputeState): Current dispute state
        
    Returns:
        Dict with updated dispute_category and audit_trail
    """
    logger.info(
        "[TRIAGE AGENT - RULE BASED] start | ticket_id=%s | customer_id=%s | query=%s",
        state.get("ticket_id"),
        state.get("customer_id"),
        state.get("customer_query"),
    )
    
    customer_query = state["customer_query"]
    
    # Use rule-based categorization to avoid external LLM client/version issues
    query_lower = customer_query.lower()
    
    try:
        if any(term in query_lower for term in ["loan", "emi", "interest", "principal", "tenure", "loan account"]):
            category = "loan_dispute"
        elif any(term in query_lower for term in ["refund not received", "refund pending", "refund status", "waiting for refund", "refund delayed"]):
            category = "refund_not_received"
        elif any(term in query_lower for term in ["atm", "cash", "dispense", "debited", "debit"]):
            category = "atm_failure"
        elif any(term in query_lower for term in ["fraud", "unauthorized", "unknown transaction", "didn't make", "did not make", "stolen"]):
            category = "fraud"
        elif any(term in query_lower for term in ["duplicate", "charged twice", "double charge", "multiple charge"]):
            category = "duplicate"
        elif any(term in query_lower for term in ["merchant", "service", "product", "goods", "refund"]):
            category = "merchant_dispute"
        elif any(term in query_lower for term in ["failed", "declined", "error", "not completed", "deducted"]):
            category = "failed_transaction"
        else:
            category = "unknown"
        
        # Update state
        audit_entry = f"Triage Agent: Categorized dispute as '{category}' - {DISPUTE_CATEGORIES.get(category, 'Unknown category')}"
        
        logger.info(
            "[TRIAGE AGENT - RULE BASED] result | category=%s | audit_entry=%s",
            category,
            audit_entry,
        )
        
        return {
            "dispute_category": category,
            "audit_trail": state["audit_trail"] + [audit_entry]
        }
        
    except Exception as e:
        logger.error("Error in rule-based triage: %s", str(e), exc_info=True)
        audit_entry = f"Triage Agent: Error during categorization - {str(e)}"
        return {
            "dispute_category": "unknown",
            "audit_trail": state["audit_trail"] + [audit_entry]
        }

# Made with Bob
