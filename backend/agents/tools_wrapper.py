"""
Tool Wrappers for Banking Dispute Management System

This module wraps banking tools for use by LLM agents using LangChain's @tool decorator.
The docstrings from banking_tools.py are used by the LLM to understand how and when to use each tool.
"""

from typing import Dict, Any, List
from langchain_core.tools import tool
from datetime import datetime
import sys
import os

# Add backend directory to path to import mcp_client
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Import mcp_client as banking_tools - routes requests to MCP server
try:
    import mcp_client as banking_tools  # type: ignore
except ImportError as e:
    raise ImportError(
        f"Failed to import mcp_client from {backend_path}. "
        f"Ensure mcp_client.py exists in backend/. Error: {e}"
    )


# ============================================================================
# TOOL WRAPPERS FOR LANGCHAIN
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


@tool
def get_loan_details_tool(customer_id: int) -> Dict[str, Any]:
    """
    Retrieve the customer's loan EMI schedule and outstanding balance.
    
    Use this tool when handling loan/EMI related disputes such as incorrect EMI
    deductions, payment processing issues, outstanding balance queries, or any
    dispute related to loan accounts.
    
    Args:
        customer_id (int): The unique identifier of the customer.
        
    Returns:
        Dict containing customer information, loan_found (bool), and loan_details
        with loan_id, monthly_emi_amount, and total_outstanding balance.
        
    Example:
        To check loan details for customer 1: get_loan_details_tool(1)
        
    Decision Logic:
        - If loan_found = False → Customer has no loan account
        - If loan details present → Use for EMI dispute verification
        - Compare disputed EMI amount with monthly_emi_amount
        - Verify outstanding balance for closure disputes
    """
    return banking_tools.get_loan_details(customer_id)


@tool
def check_merchant_refund_status_tool(transaction_id: int) -> Dict[str, Any]:
    """
    Check the refund status with the merchant/payment gateway.
    
    Use this tool when a customer reports that they haven't received a refund
    for a returned item or cancelled order. This checks if the merchant has
    initiated the refund and whether it's pending at the payment gateway.
    
    Args:
        transaction_id (int): The unique identifier of the transaction.
        
    Returns:
        Dict containing transaction_id, merchant_name, refund_status
        ('Refund Pending at Gateway' or 'No Refund Initiated by Merchant'),
        message, recommendation, and timestamp.
        
    Example:
        To check refund status: check_merchant_refund_status_tool(3)
        
    Decision Logic:
        - 'Refund Pending at Gateway' → Inform customer to wait 3-5 business days
        - 'No Refund Initiated by Merchant' → Contact merchant or consider chargeback
        - Use recommendation field for next steps
        
    Note: This is a simulated function that randomly returns one of two statuses.
    In production, this would integrate with actual payment gateway APIs.
    """
    return banking_tools.check_merchant_refund_status(transaction_id)


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
    route_to_human_tool,
    get_loan_details_tool,
    check_merchant_refund_status_tool
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

# Made with Bob
