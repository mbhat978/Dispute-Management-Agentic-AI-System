"""
Investigator Agent for Banking Dispute Management System

This module contains the investigator agent that gathers evidence using tools
based on the dispute category. It implements the Thought → Action → Observation loop.
"""

from typing import Dict, Any
import banking_tools
import models
from database import SessionLocal
from .state import DisputeState


def investigator_node(state: DisputeState) -> Dict[str, Any]:
    """
    Investigator Agent: The ReAct core that gathers evidence using tools.
    
    Based on the dispute category, this agent decides which tools to call,
    executes them, and stores the results. It implements the
    Thought → Action → Observation loop.
    
    Args:
        state (DisputeState): Current dispute state
        
    Returns:
        Dict with updated gathered_data and audit_trail
    """
    print("\n[INVESTIGATOR AGENT] Gathering evidence...")
    
    category = state["dispute_category"]
    ticket_id = state["ticket_id"]
    customer_id = state["customer_id"]
    gathered_data = dict(state["gathered_data"])
    audit_trail = list(state["audit_trail"])
    
    # Get transaction ID from the dispute ticket
    db = SessionLocal()
    try:
        ticket = db.query(models.DisputeTicket).filter(
            models.DisputeTicket.id == ticket_id
        ).first()
        
        if not ticket:
            audit_trail.append("Investigator Agent: ERROR - Ticket not found")
            return {"gathered_data": gathered_data, "audit_trail": audit_trail}
        
        transaction_id = ticket.transaction_id
        
        # THOUGHT: Determine investigation strategy based on category
        thought = f"Investigator Agent THOUGHT: Dispute categorized as '{category}'. Need to gather relevant evidence."
        audit_trail.append(thought)
        print(f"  [THOUGHT] {thought}")
        
        # Get transaction details (always needed)
        action = f"Investigator Agent ACTION: Retrieving transaction details for transaction {transaction_id}"
        audit_trail.append(action)
        print(f"  [ACTION] {action}")
        
        trans_details = banking_tools.get_transaction_details(transaction_id)
        gathered_data["transaction_details"] = trans_details
        
        observation = f"Investigator Agent OBSERVATION: Transaction details retrieved - Amount: ${trans_details.get('amount', 0)}, Merchant: {trans_details.get('merchant_name', 'Unknown')}, Status: {trans_details.get('status', 'Unknown')}"
        audit_trail.append(observation)
        print(f"  [OBSERVATION] {observation}")
        
        # Category-specific investigation
        if category == "fraud":
            # Check customer history for fraud patterns
            action = f"Investigator Agent ACTION: Checking customer history for transaction patterns"
            audit_trail.append(action)
            print(f"  [ACTION] {action}")
            
            history = banking_tools.get_customer_history(customer_id, limit=5)
            gathered_data["customer_history"] = history
            
            is_international = trans_details.get("is_international", False)
            observation = f"Investigator Agent OBSERVATION: Customer has {history.get('transaction_count', 0)} recent transactions. Current transaction is {'international' if is_international else 'domestic'}."
            audit_trail.append(observation)
            print(f"  [OBSERVATION] {observation}")
            
        elif category == "duplicate":
            # Check for duplicate transactions
            action = f"Investigator Agent ACTION: Checking for duplicate transactions"
            audit_trail.append(action)
            print(f"  [ACTION] {action}")
            
            duplicates = banking_tools.check_duplicate_transactions(
                customer_id=customer_id,
                merchant_name=trans_details.get("merchant_name", ""),
                amount=trans_details.get("amount", 0),
                date=trans_details.get("transaction_date", ""),
                time_window_hours=24
            )
            gathered_data["duplicate_check"] = duplicates
            
            observation = f"Investigator Agent OBSERVATION: {duplicates.get('message', 'Duplicate check completed')}"
            audit_trail.append(observation)
            print(f"  [OBSERVATION] {observation}")
            
        elif category == "atm_failure":
            # Check ATM logs
            action = f"Investigator Agent ACTION: Checking ATM logs for transaction {transaction_id}"
            audit_trail.append(action)
            print(f"  [ACTION] {action}")
            
            atm_logs = banking_tools.check_atm_logs(transaction_id)
            gathered_data["atm_logs"] = atm_logs
            
            observation = f"Investigator Agent OBSERVATION: {atm_logs.get('message', 'ATM log check completed')}"
            audit_trail.append(observation)
            print(f"  [OBSERVATION] {observation}")
            
        elif category == "failed_transaction":
            # Check transaction status
            status = trans_details.get("status", "")
            observation = f"Investigator Agent OBSERVATION: Transaction status is '{status}'. Verifying if amount was deducted despite failure."
            audit_trail.append(observation)
            print(f"  [OBSERVATION] {observation}")
            
        elif category == "merchant_dispute":
            # Get transaction and customer context
            action = f"Investigator Agent ACTION: Gathering merchant transaction context"
            audit_trail.append(action)
            print(f"  [ACTION] {action}")
            
            observation = f"Investigator Agent OBSERVATION: Merchant dispute requires human review for policy assessment."
            audit_trail.append(observation)
            print(f"  [OBSERVATION] {observation}")

        print(f"  [OK] Investigation complete. Gathered {len(gathered_data)} data points.")
        
        return {
            "gathered_data": gathered_data,
            "audit_trail": audit_trail
        }
        
    except Exception as e:
        print(f"  [ERROR] Error during investigation: {str(e)}")
        audit_trail.append(f"Investigator Agent ERROR: {str(e)}")
        return {"gathered_data": gathered_data, "audit_trail": audit_trail}
    finally:
        db.close()

# Made with Bob
