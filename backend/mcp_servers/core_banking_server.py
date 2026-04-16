import sys
from pathlib import Path

# Add the mcp_servers directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP
from banking_tools import (
    get_transaction_details,
    get_customer_history,
    check_atm_logs,
    check_duplicate_transactions,
    block_card,
    initiate_refund,
    route_to_human,
    get_loan_details,
    check_merchant_refund_status
)


mcp = FastMCP("CoreBanking")


@mcp.tool()
def get_transaction_details_tool(transaction_id: int) -> dict:
    """
    Retrieve complete details for a specific transaction.
    
    Args:
        transaction_id: The unique identifier of the transaction
        
    Returns:
        Dictionary containing transaction details including customer info,
        merchant name, amount, status, and whether it's international
    """
    return get_transaction_details(transaction_id)


@mcp.tool()
def get_customer_history_tool(customer_id: int, limit: int = 5) -> dict:
    """
    Retrieve the transaction history for a specific customer.
    
    Args:
        customer_id: The unique identifier of the customer
        limit: Maximum number of transactions to return (default: 5)
        
    Returns:
        Dictionary containing customer details and list of recent transactions
    """
    return get_customer_history(customer_id, limit)


@mcp.tool()
def check_atm_logs_tool(transaction_id: int) -> dict:
    """
    Query ATM logs for a specific transaction.
    
    Args:
        transaction_id: The unique identifier of the transaction
        
    Returns:
        Dictionary containing ATM log information including status codes
        and whether cash was dispensed or if there was a hardware fault
    """
    return check_atm_logs(transaction_id)


@mcp.tool()
def check_duplicate_transactions_tool(
    customer_id: int,
    merchant_name: str,
    amount: float,
    date: str,
    time_window_hours: int = 24
) -> dict:
    """
    Check for duplicate transactions within a time window.
    
    Args:
        customer_id: The unique identifier of the customer
        merchant_name: The name of the merchant to search for
        amount: The transaction amount to match
        date: The reference date/time for the search window (ISO format)
        time_window_hours: Hours before and after the reference date to search (default: 24)
        
    Returns:
        Dictionary containing information about duplicate transactions found
    """
    from datetime import datetime
    date_obj = datetime.fromisoformat(date)
    return check_duplicate_transactions(customer_id, merchant_name, amount, date_obj, time_window_hours)


@mcp.tool()
def block_card_tool(customer_id: int, reason: str = "Suspected fraud") -> dict:
    """
    Block a customer's card due to suspected fraud or security concerns.
    
    Args:
        customer_id: The unique identifier of the customer whose card should be blocked
        reason: The reason for blocking the card (default: "Suspected fraud")
        
    Returns:
        Dictionary containing status, customer info, and confirmation message
    """
    return block_card(customer_id, reason)


@mcp.tool()
def initiate_refund_tool(
    transaction_id: int,
    amount: float,
    reason: str = "Approved dispute"
) -> dict:
    """
    Initiate a refund for a disputed transaction.
    
    Args:
        transaction_id: The unique identifier of the transaction to refund
        amount: The amount to refund (can be partial or full)
        reason: The reason for the refund (default: "Approved dispute")
        
    Returns:
        Dictionary containing refund status, amount, and processing information
    """
    return initiate_refund(transaction_id, amount, reason)


@mcp.tool()
def route_to_human_tool(ticket_id: int, summary: str) -> dict:
    """
    Route a dispute ticket to human review.
    
    Args:
        ticket_id: The unique identifier of the dispute ticket
        summary: A summary explaining why human review is required
        
    Returns:
        Dictionary containing confirmation of routing with previous and new status
    """
    return route_to_human(ticket_id, summary)


@mcp.tool()
def get_loan_details_tool(customer_id: int) -> dict:
    """
    Retrieve the customer's loan EMI schedule and outstanding balance.
    
    Args:
        customer_id: The unique identifier of the customer
        
    Returns:
        Dictionary containing loan information including EMI amount and outstanding balance
    """
    return get_loan_details(customer_id)


@mcp.tool()
def check_merchant_refund_status_tool(transaction_id: int) -> dict:
    """
    Check the refund status with the merchant/payment gateway.
    
    Args:
        transaction_id: The unique identifier of the transaction
        
    Returns:
        Dictionary containing refund status information and recommendations
    """
    return check_merchant_refund_status(transaction_id)


if __name__ == "__main__":
    mcp.run()

# Made with Bob
