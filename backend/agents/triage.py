"""
Triage Agent for Banking Dispute Management System

This module contains the triage agent that analyzes customer queries
and categorizes disputes into predefined categories.
"""

from typing import Dict, Any
from langchain_openai import ChatOpenAI
import os
from .state import DisputeState


# Dispute categories for classification
DISPUTE_CATEGORIES = {
    "fraud": "Fraudulent or unauthorized transaction",
    "duplicate": "Duplicate charge or multiple identical transactions",
    "atm_failure": "ATM did not dispense cash but amount was debited",
    "merchant_dispute": "Dispute with merchant about goods/services",
    "failed_transaction": "Transaction failed but amount was deducted",
    "unknown": "Category not yet determined"
}


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
    print("\n🔍 TRIAGE AGENT: Analyzing customer query...")
    
    customer_query = state["customer_query"]
    
    # Create LLM instance
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4"),
        temperature=0.0,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Construct categorization prompt
    prompt = f"""You are a banking dispute triage agent. Analyze the customer's complaint and categorize it.

Customer Query: "{customer_query}"

Available Categories:
- fraud: Fraudulent or unauthorized transaction
- duplicate: Duplicate charge or multiple identical transactions  
- atm_failure: ATM did not dispense cash but amount was debited
- merchant_dispute: Dispute with merchant about goods/services
- failed_transaction: Transaction failed but amount was deducted

Respond with ONLY the category name (e.g., "fraud", "duplicate", etc.) that best matches this complaint.
Category:"""
    
    try:
        # Get LLM response
        response = llm.invoke(prompt)
        category = response.content.strip().lower()
        
        # Validate category
        if category not in DISPUTE_CATEGORIES:
            category = "unknown"
        
        # Update state
        audit_entry = f"Triage Agent: Categorized dispute as '{category}' - {DISPUTE_CATEGORIES.get(category, 'Unknown category')}"
        
        print(f"  ✓ Category determined: {category}")
        print(f"  ✓ Audit entry: {audit_entry}")
        
        return {
            "dispute_category": category,
            "audit_trail": state["audit_trail"] + [audit_entry]
        }
        
    except Exception as e:
        print(f"  ✗ Error in triage: {str(e)}")
        audit_entry = f"Triage Agent: Error during categorization - {str(e)}"
        return {
            "dispute_category": "unknown",
            "audit_trail": state["audit_trail"] + [audit_entry]
        }

# Made with Bob
