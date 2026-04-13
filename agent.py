"""
Agent Orchestration for Banking Dispute Management System

This module defines the LangGraph state and wraps banking tools for use by LLM agents.
It provides the foundation for multi-agent orchestration using the ReAct pattern.
"""

from typing import TypedDict, List, Dict, Any, Annotated
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from datetime import datetime
from database import SessionLocal
import banking_tools
import models
import os
import json
import re


# ============================================================================
# GRAPH STATE DEFINITION
# ============================================================================

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


# ============================================================================
# TOOL WRAPPERS FOR LANGCHAIN
# ============================================================================
# These decorators allow the LLM to discover and invoke the banking tools
# The docstrings from banking_tools.py are used by the LLM to understand
# how and when to use each tool.
# ============================================================================

@tool
def get_transaction_details_tool(transaction_id: int) -> Dict[str, Any]:
    """
    Retrieve complete details for a specific transaction.
    
    Use this tool to get comprehensive information about a transaction including
    customer details, merchant information, transaction status, amount, date, and
    whether it was an international transaction.
    
    Args:
        transaction_id (int): The unique identifier of the transaction to retrieve.
        
    Returns:
        Dict containing transaction details including customer_id, customer_name,
        account_tier, amount, merchant_name, transaction_date, status, and is_international.
        
    Example:
        To investigate transaction 1: get_transaction_details_tool(1)
    """
    return banking_tools.get_transaction_details(transaction_id)


@tool
def get_customer_history_tool(customer_id: int, limit: int = 5) -> Dict[str, Any]:
    """
    Retrieve the transaction history for a specific customer.
    
    Use this tool to understand customer spending patterns, detect unusual behavior,
    and provide context for fraud detection. Returns the most recent transactions
    for the customer.
    
    Args:
        customer_id (int): The unique identifier of the customer.
        limit (int, optional): Maximum number of transactions to return. Defaults to 5.
        
    Returns:
        Dict containing customer information and a list of recent transactions with
        their amounts, merchants, dates, statuses, and international flags.
        
    Example:
        To check customer 2's history: get_customer_history_tool(2, limit=5)
    """
    return banking_tools.get_customer_history(customer_id, limit)


@tool
def check_atm_logs_tool(transaction_id: int) -> Dict[str, Any]:
    """
    Query ATM logs for a specific transaction to verify hardware status.
    
    Use this tool for ANY ATM-related dispute. It checks if there are ATM logs
    associated with a transaction and analyzes status codes to determine if cash
    was dispensed or if there was a hardware fault.
    
    Args:
        transaction_id (int): The unique identifier of the transaction.
        
    Returns:
        Dict containing atm_log_found (bool), list of atm_logs with status codes,
        has_hardware_fault (bool), has_successful_dispense (bool), and a message
        interpreting the findings.
        
    Example:
        To verify ATM transaction 6: check_atm_logs_tool(6)
        
    Decision Logic:
        - If has_hardware_fault = True → Approve refund (cash not dispensed)
        - If has_successful_dispense = True → Investigate further or deny
        - If atm_log_found = False → Route to human review
    """
    return banking_tools.check_atm_logs(transaction_id)


@tool
def check_duplicate_transactions_tool(
    customer_id: int,
    merchant_name: str,
    amount: float,
    date: str,
    time_window_hours: int = 24
) -> Dict[str, Any]:
    """
    Check for duplicate transactions within a time window.
    
    Use this tool when a customer reports duplicate charges or when investigating
    suspicious multiple transactions to the same merchant. Searches for transactions
    with identical merchant name and amount within a specified time window.
    
    Args:
        customer_id (int): The unique identifier of the customer.
        merchant_name (str): The name of the merchant to search for.
        amount (float): The transaction amount to match.
        date (str): The reference date/time in ISO format (YYYY-MM-DDTHH:MM:SS).
        time_window_hours (int, optional): Hours before/after date to search. Defaults to 24.
        
    Returns:
        Dict containing duplicates_found (bool), duplicate_count, list of matching
        transactions with time differences, and a message summarizing findings.
        
    Example:
        To check for duplicates: check_duplicate_transactions_tool(
            customer_id=4, 
            merchant_name="Coffee Shop Downtown", 
            amount=89.99, 
            date="2026-04-09T18:37:43"
        )
        
    Decision Logic:
        - Duplicates < 5 min apart → High confidence duplicate, approve refund
        - Duplicates < 1 hour apart → Medium confidence, investigate merchant
        - Duplicates spread over hours → May be legitimate purchases
    """
    # Convert string date to datetime object
    date_obj = datetime.fromisoformat(date)
    return banking_tools.check_duplicate_transactions(
        customer_id, merchant_name, amount, date_obj, time_window_hours
    )


@tool
def block_card_tool(customer_id: int, reason: str = "Suspected fraud") -> Dict[str, str]:
    """
    Block a customer's card due to suspected fraud or security concerns.
    
    Use this tool when fraud is highly suspected, especially for high-value unauthorized
    international transactions or when multiple suspicious transactions are detected.
    This is a protective action that should be taken before approving refunds for fraud.
    
    Args:
        customer_id (int): The unique identifier of the customer whose card to block.
        reason (str, optional): The reason for blocking. Defaults to "Suspected fraud".
        
    Returns:
        Dict containing status, customer information, action taken, reason, timestamp,
        and a confirmation message.
        
    Example:
        To block card for fraud: block_card_tool(2, "High-value unauthorized international transaction")
        
    Important: This is a protective security measure. Use before escalating suspected fraud cases.
    """
    return banking_tools.block_card(customer_id, reason)


@tool
def initiate_refund_tool(
    transaction_id: int,
    amount: float,
    reason: str = "Approved dispute"
) -> Dict[str, Any]:
    """
    Initiate a refund for a disputed transaction.
    
    Use this tool when evidence clearly supports the customer's claim and you have
    decided to approve the dispute. Can refund full or partial amounts.
    
    Args:
        transaction_id (int): The unique identifier of the transaction to refund.
        amount (float): The amount to refund (can be partial or full).
        reason (str, optional): The reason for the refund. Defaults to "Approved dispute".
        
    Returns:
        Dict containing status, transaction and customer IDs, merchant name, original
        amount, refund amount, reason, timestamp, estimated processing days, and message.
        
    Example:
        To refund ATM failure: initiate_refund_tool(6, 200.00, "ATM hardware fault confirmed")
        
    Use Cases:
        - ATM hardware fault confirmed
        - Duplicate charge verified
        - Failed transaction with amount deducted
        - After blocking card for fraud (if applicable)
        
    Note: Function validates that refund amount doesn't exceed transaction amount.
    """
    return banking_tools.initiate_refund(transaction_id, amount, reason)


@tool
def route_to_human_tool(ticket_id: int, summary: str) -> Dict[str, Any]:
    """
    Route a dispute ticket to human review.
    
    Use this tool when automated decision confidence is low, for complex cases requiring
    judgment, when policy exceptions might apply, or for high-value disputes with unclear
    evidence. Updates the ticket status to 'human_review_required'.
    
    Args:
        ticket_id (int): The unique identifier of the dispute ticket.
        summary (str): A detailed explanation of why human review is needed, including
                      key findings, concerns, and any actions already taken.
        
    Returns:
        Dict containing status, ticket and transaction IDs, customer ID, previous status,
        new status, summary, timestamp, and confirmation message.
        
    Example:
        To route for review: route_to_human_tool(
            1, 
            "High-value international transaction ($8,500) with no prior international "
            "history. Customer claims unauthorized. Card blocked as precaution. "
            "Recommend direct customer verification."
        )
        
    Best Practices:
        - Provide detailed summary with key findings
        - Mention specific concerns or ambiguities
        - Include customer tier and risk factors
        - Note any protective actions already taken (e.g., card blocked)
        
    When to Use:
        - Low confidence in automated decision
        - Complex cases requiring human judgment
        - Policy exceptions may apply
        - High-value disputes with unclear evidence
        - VIP/Gold tier customers with significant history
    """
    return banking_tools.route_to_human(ticket_id, summary)


# ============================================================================
# TOOL LIST FOR AGENT CONFIGURATION
# ============================================================================

# List of all available tools for easy agent configuration
ALL_TOOLS = [
    get_transaction_details_tool,
    get_customer_history_tool,
    check_atm_logs_tool,
    check_duplicate_transactions_tool,
    block_card_tool,
    initiate_refund_tool,
    route_to_human_tool
]


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_tool_names() -> List[str]:
    """
    Get a list of all available tool names.
    
    Returns:
        List of tool name strings.
    """
    return [tool.name for tool in ALL_TOOLS]


def get_tool_descriptions() -> Dict[str, str]:
    """
    Get a dictionary mapping tool names to their descriptions.
    
    Returns:
        Dict mapping tool names to description strings.
    """
    return {
        tool.name: tool.description 
        for tool in ALL_TOOLS
    }


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


def add_to_audit_trail(state: DisputeState, entry: str) -> None:
    """
    Add an entry to the dispute state's audit trail.
    
    Args:
        state (DisputeState): The current dispute state.
        entry (str): The audit trail entry to add (thought, action, or observation).
        
    Example:
        add_to_audit_trail(state, "THOUGHT: Customer reports duplicate charge")
        add_to_audit_trail(state, "ACTION: Checking for duplicate transactions")
        add_to_audit_trail(state, "OBSERVATION: Found 2 identical transactions 3 min apart")
    """
    state["audit_trail"].append(entry)


def store_tool_result(state: DisputeState, tool_name: str, result: Any) -> None:
    """
    Store a tool's result in the gathered_data dictionary.
    
    Args:
        state (DisputeState): The current dispute state.
        tool_name (str): The name of the tool that was called.
        result (Any): The result returned by the tool.
        
    Example:
        store_tool_result(state, "transaction_details", transaction_data)
    """
    state["gathered_data"][tool_name] = result


# ============================================================================
# AGENT NODE FUNCTIONS
# ============================================================================

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
    print("\n🔎 INVESTIGATOR AGENT: Gathering evidence...")
    
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
        print(f"  💭 {thought}")
        
        # Get transaction details (always needed)
        action = f"Investigator Agent ACTION: Retrieving transaction details for transaction {transaction_id}"
        audit_trail.append(action)
        print(f"  🔧 {action}")
        
        trans_details = banking_tools.get_transaction_details(transaction_id)
        gathered_data["transaction_details"] = trans_details
        
        observation = f"Investigator Agent OBSERVATION: Transaction details retrieved - Amount: ${trans_details.get('amount', 0)}, Merchant: {trans_details.get('merchant_name', 'Unknown')}, Status: {trans_details.get('status', 'Unknown')}"
        audit_trail.append(observation)
        print(f"  📊 {observation}")
        
        # Category-specific investigation
        if category == "fraud":
            # Check customer history for fraud patterns
            action = f"Investigator Agent ACTION: Checking customer history for transaction patterns"
            audit_trail.append(action)
            print(f"  🔧 {action}")
            
            history = banking_tools.get_customer_history(customer_id, limit=5)
            gathered_data["customer_history"] = history
            
            is_international = trans_details.get("is_international", False)
            observation = f"Investigator Agent OBSERVATION: Customer has {history.get('transaction_count', 0)} recent transactions. Current transaction is {'international' if is_international else 'domestic'}."
            audit_trail.append(observation)
            print(f"  📊 {observation}")
            
        elif category == "duplicate":
            # Check for duplicate transactions
            action = f"Investigator Agent ACTION: Checking for duplicate transactions"
            audit_trail.append(action)
            print(f"  🔧 {action}")
            
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
            print(f"  📊 {observation}")
            
        elif category == "atm_failure":
            # Check ATM logs
            action = f"Investigator Agent ACTION: Checking ATM logs for transaction {transaction_id}"
            audit_trail.append(action)
            print(f"  🔧 {action}")
            
            atm_logs = banking_tools.check_atm_logs(transaction_id)
            gathered_data["atm_logs"] = atm_logs
            
            observation = f"Investigator Agent OBSERVATION: {atm_logs.get('message', 'ATM log check completed')}"
            audit_trail.append(observation)
            print(f"  📊 {observation}")
            
        elif category == "failed_transaction":
            # Check transaction status
            status = trans_details.get("status", "")
            observation = f"Investigator Agent OBSERVATION: Transaction status is '{status}'. Verifying if amount was deducted despite failure."
            audit_trail.append(observation)
            print(f"  📊 {observation}")
            
        elif category == "merchant_dispute":
            # Get transaction and customer context
            action = f"Investigator Agent ACTION: Gathering merchant transaction context"
            audit_trail.append(action)
            print(f"  🔧 {action}")
            
            observation = f"Investigator Agent OBSERVATION: Merchant dispute requires human review for policy assessment."
            audit_trail.append(observation)
            print(f"  📊 {observation}")
        
        print(f"  ✓ Investigation complete. Gathered {len(gathered_data)} data points.")
        
        return {
            "gathered_data": gathered_data,
            "audit_trail": audit_trail
        }
        
    except Exception as e:
        print(f"  ✗ Error during investigation: {str(e)}")
        audit_trail.append(f"Investigator Agent ERROR: {str(e)}")
        return {"gathered_data": gathered_data, "audit_trail": audit_trail}
    finally:
        db.close()


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
    print("\n⚖️  DECISION AGENT: Making final decision...")
    
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
            
            if is_international and amount > 5000:
                # High-value international - requires human review
                decision = "human_review_required"
                justification = f"High-value international transaction (${amount}). Blocking card and routing to human review for verification."
                # Block card as precaution
                banking_tools.block_card(customer_id, f"Suspected fraud - unauthorized ${amount} international transaction")
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
        print(f"  ⚖️  {decision_entry}")
        
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
            print(f"  ✓ Updated DisputeTicket #{ticket_id} status to: {ticket.status}")
        
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
        print(f"  ✓ Saved {len(audit_trail)} audit log entries to database")
        
        # If human review required, use the route_to_human tool
        if decision == "human_review_required":
            banking_tools.route_to_human(ticket_id, justification)
        
        print(f"  ✅ Final decision: {decision.upper()}")
        
        return {
            "final_decision": decision,
            "audit_trail": audit_trail
        }
        
    except Exception as e:
        print(f"  ✗ Error during decision making: {str(e)}")
        audit_entry = f"Decision Agent ERROR: {str(e)}"
        audit_trail.append(audit_entry)
        return {
            "final_decision": "human_review_required",
            "audit_trail": audit_trail
        }
    finally:
        db.close()


# ============================================================================
# LANGGRAPH WORKFLOW
# ============================================================================

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


# ============================================================================
# CONFIGURATION
# ============================================================================

# Dispute categories for classification
DISPUTE_CATEGORIES = {
    "fraud": "Fraudulent or unauthorized transaction",
    "duplicate": "Duplicate charge or multiple identical transactions",
    "atm_failure": "ATM did not dispense cash but amount was debited",
    "merchant_dispute": "Dispute with merchant about goods/services",
    "failed_transaction": "Transaction failed but amount was deducted",
    "unknown": "Category not yet determined"
}

# Decision outcomes
DECISION_OUTCOMES = {
    "auto_approved": "Dispute automatically approved, refund initiated",
    "auto_rejected": "Dispute automatically rejected based on evidence",
    "human_review_required": "Case requires human review due to complexity or unclear evidence"
}


if __name__ == "__main__":
    # Example: Initialize a dispute state
    print("Agent Configuration Loaded Successfully!")
    print(f"\nAvailable Tools: {len(ALL_TOOLS)}")
    for i, tool in enumerate(ALL_TOOLS, 1):
        print(f"  {i}. {tool.name}")
    
    print(f"\nDispute Categories: {len(DISPUTE_CATEGORIES)}")
    for category, description in DISPUTE_CATEGORIES.items():
        print(f"  - {category}: {description}")
    
    print(f"\nDecision Outcomes: {len(DECISION_OUTCOMES)}")
    for outcome, description in DECISION_OUTCOMES.items():
        print(f"  - {outcome}: {description}")
    
    # Test state initialization
    print("\n" + "="*70)
    print("Testing DisputeState initialization...")
    print("="*70)
    
    test_state = initialize_dispute_state(
        ticket_id=1,
        customer_id=2,
        customer_query="I did not authorize this high-value international transaction",
        dispute_category="fraud"
    )
    
    print(f"\nInitialized State:")
    print(f"  Ticket ID: {test_state['ticket_id']}")
    print(f"  Customer ID: {test_state['customer_id']}")
    print(f"  Query: {test_state['customer_query']}")
    print(f"  Category: {test_state['dispute_category']}")
    print(f"  Gathered Data: {test_state['gathered_data']}")
    print(f"  Audit Trail: {test_state['audit_trail']}")
    print(f"  Final Decision: {test_state['final_decision']}")
    
    print("\n✅ Agent module configured successfully!")
