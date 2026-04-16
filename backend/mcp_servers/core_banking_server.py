import sys
from pathlib import Path

# Add the mcp_servers directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP
from banking_tools import (
    get_transaction_details,
    get_customer_history,
    check_atm_logs,
    block_card,
    initiate_refund
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


if __name__ == "__main__":
    mcp.run()
