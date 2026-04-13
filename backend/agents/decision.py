"""
Decision Agent for Banking Dispute Management System

This module contains the decision agent that makes final decisions based on
gathered evidence and applies business logic to determine outcomes.
"""

from typing import Dict, Any
from datetime import datetime
import banking_tools
import models
from database import SessionLocal
from .state import DisputeState


def decision_node(state: DisputeState) -> Dict[str, Any]:
    """
    Decision Agent: Makes the final decision based on gathered evidence.
    
    This agent analyzes all the gathered data and applies business logic
    to determine whether to approve, reject, or route to human review.
    It also updates the database with the decision and audit trail.
    
    Args:
        state (DisputeState): Current dispute state
        
    Returns:
        Dict with updated final_decision and audit_trail, plus database updates
    """
    print("\n[DECISION AGENT] Making final decision...")
    
    category = state["dispute_category"]
    ticket_id = state["ticket_id"]
    customer_id = state["customer_id"]
    gathered_data = state["gathered_data"]
    audit_trail = list(state["audit_trail"])
    
    db = SessionLocal()
    try:
        # Retrieve transaction details from gathered data
        trans_details = gathered_data.get("transaction_details", {})
        transaction_id = trans_details.get("transaction_id")
        amount = trans_details.get("amount", 0)
        
        decision = ""
        justification = ""
        
        # Apply decision logic based on category and evidence
        if category == "atm_failure":
            atm_logs = gathered_data.get("atm_logs", {})
            has_fault = atm_logs.get("has_hardware_fault", False)
            
            if has_fault:
                decision = "auto_approved"
                justification = f"ATM hardware fault confirmed. Cash was not dispensed. Approving refund of ${amount}."
                # Initiate refund
                banking_tools.initiate_refund(transaction_id, amount, "ATM hardware fault confirmed")
            else:
                decision = "human_review_required"
                justification = "ATM logs unclear or show successful dispensing. Requires human verification."
                
        elif category == "duplicate":
            dup_check = gathered_data.get("duplicate_check", {})
            duplicates_found = dup_check.get("duplicates_found", False)
            dup_count = dup_check.get("duplicate_count", 0)
            
            if duplicates_found and dup_count >= 2:
                transactions = dup_check.get("transactions", [])
                if len(transactions) >= 2:
                    time_diff = transactions[1].get("time_difference_minutes", 999)
                    if time_diff < 5:
                        decision = "auto_approved"
                        justification = f"Duplicate charge confirmed ({dup_count} transactions within {time_diff:.1f} minutes). Approving refund of ${amount}."
                        banking_tools.initiate_refund(transaction_id, amount, "Duplicate charge detected")
                    else:
                        decision = "human_review_required"
                        justification = f"Multiple similar transactions found but timing unclear ({time_diff:.1f} minutes apart)."
            else:
                decision = "auto_rejected"
                justification = "No duplicate transactions found. Dispute not supported by evidence."
                
        elif category == "fraud":
            history = gathered_data.get("customer_history", {})
            is_international = trans_details.get("is_international", False)
            account_tier = trans_details.get("account_tier", "Basic")
            
            if is_international:
                # International transaction anomaly detected - auto-approve per UC4 Scenario 1
                decision = "auto_approved"
                justification = f"Fraudulent transaction anomaly detected (international transaction, ${amount}). Dispute auto-approved, card blocked, and refund initiated."
                # Block card for security
                banking_tools.block_card(customer_id, f"Suspected fraud - unauthorized ${amount} international transaction")
                # Initiate refund
                banking_tools.initiate_refund(transaction_id, amount, "Fraud - unauthorized international transaction")
            elif amount > 1000:
                decision = "human_review_required"
                justification = f"High-value transaction (${amount}) flagged as fraud. Requires human verification."
            else:
                decision = "auto_approved"
                justification = f"Fraud claim on transaction of ${amount}. Approving refund based on customer report."
                banking_tools.initiate_refund(transaction_id, amount, "Fraud - unauthorized transaction")
                
        elif category == "failed_transaction":
            status = trans_details.get("status", "")
            if status == "failed":
                decision = "auto_approved"
                justification = f"Transaction status is 'failed' but amount was deducted. Approving refund of ${amount}."
                banking_tools.initiate_refund(transaction_id, amount, "Failed transaction with amount deducted")
            else:
                decision = "auto_rejected"
                justification = f"Transaction status is '{status}', not 'failed'. Dispute not supported."
                
        elif category == "merchant_dispute":
            decision = "human_review_required"
            justification = "Merchant disputes require human review for policy assessment and merchant contact."
            
        else:  # unknown or other
            decision = "human_review_required"
            justification = "Unable to categorize or assess automatically. Routing to human review."
        
        # Add decision to audit trail
        decision_entry = f"Decision Agent DECISION: {decision.upper()} - {justification}"
        audit_trail.append(decision_entry)
        print(f"  [DECISION] {decision_entry}")
        
        # Update database: DisputeTicket
        ticket = db.query(models.DisputeTicket).filter(
            models.DisputeTicket.id == ticket_id
        ).first()
        
        if ticket:
            if decision == "human_review_required":
                ticket.status = "human_review_required"
                ticket.resolution_notes = justification
            elif decision == "auto_approved":
                ticket.status = "auto_approved"
                ticket.resolution_notes = justification
            elif decision == "auto_rejected":
                ticket.status = "auto_rejected"
                ticket.resolution_notes = justification
            
            ticket.updated_at = datetime.utcnow()
            db.commit()
            print(f"  [OK] Updated DisputeTicket #{ticket_id} status to: {ticket.status}")
        
        # Write audit trail to AuditLog table
        for entry in audit_trail:
            # Parse entry to determine action type
            if "THOUGHT:" in entry or "Triage Agent:" in entry:
                action_type = "thought"
                agent_name = "TriageAgent" if "Triage" in entry else "InvestigatorAgent" if "Investigator" in entry else "DecisionAgent"
            elif "ACTION:" in entry:
                action_type = "tool_call"
                agent_name = "InvestigatorAgent"
            elif "OBSERVATION:" in entry:
                action_type = "observation"
                agent_name = "InvestigatorAgent"
            elif "DECISION:" in entry:
                action_type = "decision"
                agent_name = "DecisionAgent"
            else:
                action_type = "thought"
                agent_name = "System"
            
            audit_log = models.AuditLog(
                ticket_id=ticket_id,
                agent_name=agent_name,
                action_type=action_type,
                description=entry,
                timestamp=datetime.utcnow()
            )
            db.add(audit_log)
        
        db.commit()
        print(f"  [OK] Saved {len(audit_trail)} audit log entries to database")
        
        # If human review required, use the route_to_human tool
        if decision == "human_review_required":
            banking_tools.route_to_human(ticket_id, justification)
        
        print(f"  [SUCCESS] Final decision: {decision.upper()}")
        
        return {
            "final_decision": decision,
            "audit_trail": audit_trail
        }
        
    except Exception as e:
        print(f"  [ERROR] Error during decision making: {str(e)}")
        audit_entry = f"Decision Agent ERROR: {str(e)}"
        audit_trail.append(audit_entry)
        return {
            "final_decision": "human_review_required",
            "audit_trail": audit_trail
        }
    finally:
        db.close()

# Made with Bob
