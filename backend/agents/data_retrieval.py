"""
Data Retrieval Agent for Banking Dispute Management System

This specialist agent retrieves standard database information based on the
dispute category without requiring LLM planning. It executes predefined
tools based on category rules.
"""

from typing import Dict, Any, List
from loguru import logger
from datetime import datetime

try:
    from .. import mcp_client as banking_tools
    from .. import models
    from ..database import SessionLocal
    from .state import DisputeState
except ImportError:
    import mcp_client as banking_tools
    import models
    from database import SessionLocal
    from agents.state import DisputeState


def data_retrieval_node(state: DisputeState) -> Dict[str, Any]:
    """
    Data Retrieval Agent: Gathers standard database information based on category.
    
    This agent executes predefined database tools without LLM planning:
    - Always retrieves transaction details
    - Executes category-specific tools (ATM logs, loan details, refund status, etc.)
    - Does NOT perform fraud analysis or vision analysis (handled by specialists)
    
    Args:
        state: The current dispute state
        
    Returns:
        Dict with updated gathered_data and audit_trail
    """
    ticket_id = state["ticket_id"]
    customer_id = state["customer_id"]
    category = state["dispute_category"]
    gathered_data = dict(state["gathered_data"])
    audit_trail = list(state["audit_trail"])
    
    logger.info(
        f"[DATA RETRIEVAL AGENT] start | ticket_id={ticket_id} | "
        f"customer_id={customer_id} | category={category}"
    )
    
    db = SessionLocal()
    try:
        # Get transaction_id from ticket
        ticket = db.query(models.DisputeTicket).filter(
            models.DisputeTicket.id == ticket_id
        ).first()
        
        if not ticket:
            audit_trail.append("Data Retrieval Agent: ERROR - Ticket not found")
            return {
                "gathered_data": gathered_data,
                "audit_trail": audit_trail
            }
        
        transaction_id: int = ticket.transaction_id  # type: ignore[assignment]
        
        # Build retrieval plan based on category
        plan = _build_retrieval_plan(category, customer_id, transaction_id, gathered_data)
        
        logger.info(
            f"[DATA RETRIEVAL AGENT] plan_created | "
            f"steps={[step['tool'] for step in plan]}"
        )
        audit_trail.append(
            f"Data Retrieval Agent THOUGHT: Built retrieval plan for category '{category}'. "
            f"Planned steps: {[step['tool'] for step in plan]}"
        )
        
        # Execute each tool in the plan
        for step in plan:
            tool_name = step["tool"]
            tool_input = step["input"]
            data_key = step["data_key"]
            
            logger.info(f"[DATA RETRIEVAL AGENT] Action: calling {tool_name}")
            audit_trail.append(
                f"Data Retrieval Agent ACTION: Calling {tool_name} with input {tool_input}"
            )
            
            try:
                observation = _execute_tool(tool_name, tool_input)
                gathered_data[data_key] = observation
                
                logger.info(f"[DATA RETRIEVAL AGENT] Observation: {tool_name} returned data")
                audit_trail.append(
                    f"Data Retrieval Agent OBSERVATION: {tool_name} output: {str(observation)}"
                )
                
            except Exception as e:
                logger.error(f"[DATA RETRIEVAL AGENT] Tool execution failed: {tool_name} - {str(e)}")
                audit_trail.append(f"Data Retrieval Agent ERROR: {tool_name} failed - {str(e)}")
        
        logger.success(
            f"[DATA RETRIEVAL AGENT] complete | gathered_data_points={len(gathered_data)}"
        )
        
        return {
            "gathered_data": gathered_data,
            "audit_trail": audit_trail
        }
        
    except Exception as e:
        logger.exception(f"Error during data retrieval: {str(e)}")
        audit_trail.append(f"Data Retrieval Agent ERROR: {str(e)}")
        return {
            "gathered_data": gathered_data,
            "audit_trail": audit_trail
        }
    finally:
        db.close()


def _build_retrieval_plan(
    category: str,
    customer_id: int,
    transaction_id: int,
    prior_gathered_data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Build a rule-based retrieval plan based on dispute category.
    
    Args:
        category: The dispute category
        customer_id: The customer ID
        transaction_id: The transaction ID
        prior_gathered_data: Already gathered data to avoid duplicates
        
    Returns:
        List of tool execution steps
    """
    plan: List[Dict[str, Any]] = []
    
    # Always get transaction details first if not already gathered
    if "transaction_details" not in prior_gathered_data:
        plan.append({
            "tool": "get_transaction_details",
            "data_key": "transaction_details",
            "input": {"transaction_id": transaction_id}
        })
    
    # Category-specific tools (excluding fraud and vision analysis)
    if category == "atm_failure":
        plan.append({
            "tool": "check_atm_logs",
            "data_key": "atm_logs",
            "input": {"transaction_id": transaction_id}
        })
        
    elif category == "duplicate":
        plan.append({
            "tool": "check_duplicate_transactions",
            "data_key": "duplicate_check",
            "input": {"customer_id": customer_id, "transaction_id": transaction_id}
        })
        
    elif category == "loan_dispute":
        plan.append({
            "tool": "get_loan_details",
            "data_key": "loan_details",
            "input": {"customer_id": customer_id}
        })
        
    elif category == "refund_not_received":
        plan.append({
            "tool": "check_merchant_refund_status",
            "data_key": "refund_status",
            "input": {"transaction_id": transaction_id}
        })
        plan.append({
            "tool": "get_refund_timeline",
            "data_key": "refund_timeline",
            "input": {"transaction_id": transaction_id}
        })
        
    elif category == "incorrect_amount":
        plan.append({
            "tool": "verify_receipt_amount",
            "data_key": "receipt_verification",
            "input": {"transaction_id": transaction_id, "claimed_amount": 0.0}
        })
        
    elif category == "merchant_dispute":
        plan.append({
            "tool": "get_delivery_tracking_status",
            "data_key": "delivery_status",
            "input": {"transaction_id": transaction_id}
        })
        # Merchant reputation will be added after transaction details
        
    # Always get customer history for context
    # For fraud cases, get more history to detect velocity patterns
    if "customer_history" not in prior_gathered_data:
        history_limit = 20 if category == "fraud" else 5
        plan.append({
            "tool": "get_customer_history",
            "data_key": "customer_history",
            "input": {"customer_id": customer_id, "limit": history_limit}
        })
    
    return plan


def _execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a single tool and return its result.
    
    Args:
        tool_name: Name of the tool to execute
        tool_input: Input parameters for the tool
        
    Returns:
        Tool execution result as a dictionary
    """
    if tool_name == "get_transaction_details":
        return banking_tools.get_transaction_details(tool_input["transaction_id"])
        
    elif tool_name == "get_customer_history":
        return banking_tools.get_customer_history(
            tool_input["customer_id"],
            tool_input.get("limit", 5)
        )
        
    elif tool_name == "check_atm_logs":
        return banking_tools.check_atm_logs(tool_input["transaction_id"])
        
    elif tool_name == "check_duplicate_transactions":
        # Get transaction details for duplicate check
        trans_details = banking_tools.get_transaction_details(
            tool_input.get("transaction_id", 0)
        )
        return banking_tools.check_duplicate_transactions(
            customer_id=tool_input["customer_id"],
            merchant_name=trans_details.get("merchant_name", ""),
            amount=trans_details.get("amount", 0),
            date=trans_details.get("transaction_date", ""),
            time_window_hours=24
        )
        
    elif tool_name == "get_loan_details":
        return banking_tools.get_loan_details(tool_input["customer_id"])
        
    elif tool_name == "check_merchant_refund_status":
        return banking_tools.check_merchant_refund_status(tool_input["transaction_id"])
        
    elif tool_name == "get_refund_timeline":
        return banking_tools.get_refund_timeline(tool_input["transaction_id"])
        
    elif tool_name == "verify_receipt_amount":
        return banking_tools.verify_receipt_amount(
            tool_input["transaction_id"],
            tool_input.get("claimed_amount", 0.0)
        )
        
    elif tool_name == "get_delivery_tracking_status":
        return banking_tools.get_delivery_tracking_status(tool_input["transaction_id"])
        
    elif tool_name == "check_merchant_reputation_score":
        return banking_tools.check_merchant_reputation_score(
            tool_input.get("merchant_name", "")
        )
        
    elif tool_name == "get_merchant_dispute_history":
        return banking_tools.get_merchant_dispute_history(
            tool_input.get("merchant_name", "")
        )
        
    else:
        return {"error": f"Unsupported tool: {tool_name}"}


# Made with Bob