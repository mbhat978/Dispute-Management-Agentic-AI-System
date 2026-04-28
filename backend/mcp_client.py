"""
MCP Client for Core Banking Server

This module provides a client interface to communicate with the core_banking_server.py
MCP server using Server-Sent Events (SSE). It maintains a persistent connection to the
server and reuses the same session for all tool calls.
"""

import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession


# SSE server configuration
SSE_SERVER_URL = "http://localhost:8001/sse"
COMPLIANCE_SSE_SERVER_URL = "http://localhost:8002/sse"
ENHANCED_BANKING_SSE_SERVER_URL = "http://localhost:8003/sse"


async def _call_mcp_tool_async(
    tool_name: str,
    arguments: dict,
    server_url: str = SSE_SERVER_URL,
) -> Dict[str, Any]:
    """
    Internal async function to call MCP tools via an MCP SSE server.
    Uses SSE connection to communicate with the persistent server.

    Args:
        tool_name (str): Name of the tool to call
        arguments (dict): Arguments to pass to the tool
        server_url (str): SSE endpoint for the target MCP server

    Returns:
        Dict[str, Any]: Parsed result from the MCP server
    """
    try:
        async with sse_client(server_url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)

                if result.content:
                    for content_item in result.content:
                        if hasattr(content_item, 'type') and content_item.type == 'text':
                            if hasattr(content_item, 'text'):
                                return json.loads(content_item.text)

                return {}

    except Exception as e:
        print(f"Error calling MCP tool {tool_name} on {server_url}: {str(e)}")
        return {
            "error": str(e),
            "tool_name": tool_name,
            "server_url": server_url,
            "status": "failed"
        }


def call_mcp_tool(
    tool_name: str,
    arguments: dict,
    server_url: str = SSE_SERVER_URL,
) -> Dict[str, Any]:
    """
    Synchronous wrapper to call MCP tools.

    This function allows synchronous code (like our agents) to easily call
    async MCP tools without dealing with async/await syntax.

    Args:
        tool_name (str): Name of the tool to call
        arguments (dict): Arguments to pass to the tool
        server_url (str): SSE endpoint for the target MCP server

    Returns:
        Dict[str, Any]: Result from the MCP server
    """
    return asyncio.run(_call_mcp_tool_async(tool_name, arguments, server_url))


# ============================================================================
# Banking Tool Wrapper Functions
# ============================================================================
# These functions provide the same interface as banking_tools.py but use
# MCP to communicate with the core banking server instead of direct DB access.
# ============================================================================


def get_transaction_details(transaction_id: int) -> Dict[str, Any]:
    """
    Retrieve complete details for a specific transaction.
    
    Args:
        transaction_id (int): The unique identifier of the transaction.
        
    Returns:
        Dict[str, Any]: Transaction details including customer info, amount,
                       merchant name, status, and whether it's international.
    """
    return call_mcp_tool('get_transaction_details_tool', {'transaction_id': transaction_id})


def get_customer_history(customer_id: int, limit: int = 5) -> Dict[str, Any]:
    """
    Retrieve the transaction history for a specific customer.
    
    Args:
        customer_id (int): The unique identifier of the customer.
        limit (int, optional): Maximum number of transactions to return.
                              Defaults to 5.
        
    Returns:
        Dict[str, Any]: Customer information and list of recent transactions.
    """
    return call_mcp_tool('get_customer_history_tool', {
        'customer_id': customer_id,
        'limit': limit
    })


def check_atm_logs(transaction_id: int) -> Dict[str, Any]:
    """
    Query ATM logs for a specific transaction.
    
    Args:
        transaction_id (int): The unique identifier of the transaction.
        
    Returns:
        Dict[str, Any]: ATM log information including status codes and
                       whether cash was dispensed or if there was a fault.
    """
    return call_mcp_tool('check_atm_logs_tool', {'transaction_id': transaction_id})


def check_duplicate_transactions(
    customer_id: int,
    merchant_name: str,
    amount: float,
    date: str,
    time_window_hours: int = 24
) -> Dict[str, Any]:
    """
    Check for duplicate transactions within a time window.
    
    Args:
        customer_id (int): The unique identifier of the customer.
        merchant_name (str): The name of the merchant to search for.
        amount (float): The transaction amount to match.
        date (str): The reference date/time for the search window (ISO format string).
        time_window_hours (int, optional): Hours before and after the reference
                                          date to search. Defaults to 24 hours.
        
    Returns:
        Dict[str, Any]: Information about duplicate transactions found.
    """
    return call_mcp_tool('check_duplicate_transactions_tool', {
        'customer_id': customer_id,
        'merchant_name': merchant_name,
        'amount': amount,
        'date': date,
        'time_window_hours': time_window_hours
    })


def block_card(customer_id: int, reason: str = "Suspected fraud") -> Dict[str, Any]:
    """
    Block a customer's card due to suspected fraud or security concerns.
    
    Args:
        customer_id (int): The unique identifier of the customer whose
                          card should be blocked.
        reason (str, optional): The reason for blocking the card.
                               Defaults to "Suspected fraud".
        
    Returns:
        Dict[str, Any]: Confirmation of card block with timestamp and reason.
    """
    return call_mcp_tool('block_card_tool', {
        'customer_id': customer_id,
        'reason': reason
    })


def issue_replacement_card(customer_id: int, expedited_shipping: bool = True) -> Dict[str, Any]:
    """
    Issues a replacement card for a customer whose previous card was blocked due to fraud or loss.
    
    Args:
        customer_id (int): The unique identifier of the customer.
        expedited_shipping (bool, optional): Whether to use expedited shipping.
                                            Defaults to True.
    
    Returns:
        Dict[str, Any]: Confirmation of replacement card issuance with shipping details.
    """
    return call_mcp_tool('issue_replacement_card_tool', {
        'customer_id': customer_id,
        'expedited_shipping': expedited_shipping
    })


def initiate_refund(
    transaction_id: int,
    amount: float,
    reason: str = "Approved dispute"
) -> Dict[str, Any]:
    """
    Initiate a refund for a disputed transaction.
    
    Args:
        transaction_id (int): The unique identifier of the transaction to refund.
        amount (float): The amount to refund (can be partial or full).
        reason (str, optional): The reason for the refund.
                               Defaults to "Approved dispute".
        
    Returns:
        Dict[str, Any]: Refund confirmation with processing time estimate.
    """
    return call_mcp_tool('initiate_refund_tool', {
        'transaction_id': transaction_id,
        'amount': amount,
        'reason': reason
    })


def route_to_human(ticket_id: int, summary: str) -> Dict[str, Any]:
    """
    Route a dispute ticket to human review.
    
    Args:
        ticket_id (int): The unique identifier of the dispute ticket.
        summary (str): A summary explaining why human review is required.
        
    Returns:
        Dict[str, Any]: Confirmation of routing with previous and new status.
    """
    return call_mcp_tool('route_to_human_tool', {
        'ticket_id': ticket_id,
        'summary': summary
    })


def get_loan_details(customer_id: int) -> Dict[str, Any]:
    """
    Retrieve the customer's loan EMI schedule and outstanding balance.
    
    Args:
        customer_id (int): The unique identifier of the customer.
        
    Returns:
        Dict[str, Any]: Loan information including EMI amount and outstanding balance.
    """
    return call_mcp_tool('get_loan_details_tool', {'customer_id': customer_id})


def check_merchant_refund_status(transaction_id: int) -> Dict[str, Any]:
    """
    Check the refund status with the merchant/payment gateway.
    
    Args:
        transaction_id (int): The unique identifier of the transaction.
        
    Returns:
        Dict[str, Any]: Refund status information and recommendations.
    """
    return call_mcp_tool('check_merchant_refund_status_tool', {'transaction_id': transaction_id})


def query_compliance_policy(query: str) -> Dict[str, Any]:
    """
    Query the compliance MCP server for the most relevant dispute policy text.

    Args:
        query (str): Natural language query describing the dispute context.

    Returns:
        Dict[str, Any]: Policy lookup result including matched policy text.
    """
    return call_mcp_tool(
        'query_compliance_policy',
        {'query': query},
        server_url=COMPLIANCE_SSE_SERVER_URL,
    )


def verify_receipt_amount(transaction_id: int, claimed_amount: float) -> Dict[str, Any]:
    """
    Verify a customer-uploaded receipt amount against the ledger.

    Args:
        transaction_id (int): The unique identifier of the transaction.
        claimed_amount (float): The amount the customer claims they should have been charged.

    Returns:
        Dict[str, Any]: Receipt verification result including billed and claimed amounts.
    """
    return call_mcp_tool('verify_receipt_amount_tool', {
        'transaction_id': transaction_id,
        'claimed_amount': claimed_amount,
    })


def initiate_chargeback(transaction_id: int, chargeback_amount: float, network_reason_code: str, notes: str) -> Dict[str, Any]:
    """
    Initiate a chargeback with the card network for merchant disputes.

    Args:
        transaction_id (int): The unique identifier of the transaction.
        chargeback_amount (float): The amount to claim from the merchant.
        network_reason_code (str): The Visa/Mastercard reason code.
        notes (str): Additional notes about the chargeback.

    Returns:
        Dict[str, Any]: Chargeback initiation result and status.
    """
    return call_mcp_tool('initiate_chargeback_tool', {
        'transaction_id': transaction_id,
        'chargeback_amount': chargeback_amount,
        'network_reason_code': network_reason_code,
        'notes': notes
    })


def analyze_receipt_evidence(receipt_base64: str, expected_merchant: str) -> str:
    """
    Analyzes a Base64 receipt image to extract the actual charged amount and merchant name.
    Use this tool whenever a customer uploads a receipt to verify 'incorrect_amount' claims.

    Args:
        receipt_base64 (str): Base64-encoded receipt image data.
        expected_merchant (str): The merchant name from the transaction record for comparison.

    Returns:
        str: JSON string containing extracted merchant, amount, legibility, and fraud indicators.
    """
    result = call_mcp_tool('analyze_receipt_evidence_tool', {
        'receipt_base64': receipt_base64,
        'expected_merchant': expected_merchant,
    })
    # Return as JSON string to match the banking_tools.py interface
    return json.dumps(result)


def calculate_timeline_from_evidence(evidence_base64: str, transaction_id: int) -> Dict[str, Any]:
    """
    Calculates refund timeline from uploaded receipt/email evidence using Vision AI.
    Extracts the return date from the evidence and calculates expected refund timeline.
    
    Args:
        evidence_base64 (str): Base64-encoded receipt or email image data.
        transaction_id (int): The transaction ID for context.
        
    Returns:
        Dict[str, Any]: Timeline analysis including extracted return date, days elapsed, and expected refund date.
    """
    result = call_mcp_tool('calculate_timeline_from_evidence_tool', {
        'evidence_base64': evidence_base64,
        'transaction_id': transaction_id,
    })
    return result


# ============================================================================
# Enhanced Banking Tool Wrapper Functions (New MCP Server on Port 8003)
# ============================================================================

def get_delivery_tracking_status(transaction_id: int, tracking_number: Optional[str] = None) -> Dict[str, Any]:
    """
    Get delivery tracking status for merchant disputes involving undelivered items.
    
    Args:
        transaction_id (int): The unique identifier of the transaction.
        tracking_number (str, optional): Tracking number if available.
        
    Returns:
        Dict[str, Any]: Delivery status, location, and estimated delivery date.
    """
    return call_mcp_tool(
        'get_delivery_tracking_status_tool',
        {
            'transaction_id': transaction_id,
            'tracking_number': tracking_number
        },
        server_url=ENHANCED_BANKING_SSE_SERVER_URL
    )


def check_merchant_reputation_score(merchant_name: str) -> Dict[str, Any]:
    """
    Check merchant reputation score based on historical dispute patterns.
    
    Args:
        merchant_name (str): The name of the merchant.
        
    Returns:
        Dict[str, Any]: Reputation score (0-100), dispute rate, and risk level.
    """
    return call_mcp_tool(
        'check_merchant_reputation_score_tool',
        {'merchant_name': merchant_name},
        server_url=ENHANCED_BANKING_SSE_SERVER_URL
    )


def get_merchant_dispute_history(merchant_name: str, days: int = 90) -> Dict[str, Any]:
    """
    Get historical dispute data for a specific merchant.
    
    Args:
        merchant_name (str): The name of the merchant.
        days (int, optional): Number of days to look back. Defaults to 90.
        
    Returns:
        Dict[str, Any]: Total disputes, resolution rate, common issues, and patterns.
    """
    return call_mcp_tool(
        'get_merchant_dispute_history_tool',
        {
            'merchant_name': merchant_name,
            'days': days
        },
        server_url=ENHANCED_BANKING_SSE_SERVER_URL
    )


def check_subscription_status(customer_id: int, merchant_name: str) -> Dict[str, Any]:
    """
    Check if customer has an active subscription with the merchant.
    
    Args:
        customer_id (int): The unique identifier of the customer.
        merchant_name (str): The name of the merchant.
        
    Returns:
        Dict[str, Any]: Subscription status, billing cycle, and next charge date.
    """
    return call_mcp_tool(
        'check_subscription_status_tool',
        {
            'customer_id': customer_id,
            'merchant_name': merchant_name
        },
        server_url=ENHANCED_BANKING_SSE_SERVER_URL
    )


def verify_subscription_cancellation(customer_id: int, merchant_name: str, cancellation_date: str) -> Dict[str, Any]:
    """
    Verify if customer properly cancelled subscription before disputed charge.
    
    Args:
        customer_id (int): The unique identifier of the customer.
        merchant_name (str): The name of the merchant.
        cancellation_date (str): Date customer claims they cancelled (ISO format).
        
    Returns:
        Dict[str, Any]: Cancellation verification status and merchant confirmation.
    """
    return call_mcp_tool(
        'verify_subscription_cancellation_tool',
        {
            'customer_id': customer_id,
            'merchant_name': merchant_name,
            'cancellation_date': cancellation_date
        },
        server_url=ENHANCED_BANKING_SSE_SERVER_URL
    )


def get_refund_timeline(transaction_id: int) -> Dict[str, Any]:
    """
    Get detailed refund processing timeline and current stage.
    
    Args:
        transaction_id (int): The unique identifier of the transaction.
        
    Returns:
        Dict[str, Any]: Refund stage, days elapsed, expected completion, and recommendations.
    """
    return call_mcp_tool(
        'get_refund_timeline_tool',
        {'transaction_id': transaction_id},
        server_url=ENHANCED_BANKING_SSE_SERVER_URL
    )


# Helper function for agent introspection
def get_available_tools() -> list:
    """
    Get a list of all available banking tools with their descriptions.
    
    Returns:
        list: List of tool metadata dictionaries.
    """
    tools = [
        {
            "name": "get_transaction_details",
            "description": "Retrieve complete details for a specific transaction including customer info and transaction status"
        },
        {
            "name": "get_customer_history",
            "description": "Get the last 5 transactions for a customer to understand spending patterns"
        },
        {
            "name": "check_atm_logs",
            "description": "Query ATM logs to verify if cash was dispensed or if there was a hardware fault"
        },
        {
            "name": "check_duplicate_transactions",
            "description": "Search for duplicate transactions with same merchant and amount within a time window"
        },
        {
            "name": "block_card",
            "description": "Block a customer's card due to suspected fraud or security concerns"
        },
        {
            "name": "initiate_refund",
            "description": "Initiate a refund for a disputed transaction"
        },
        {
            "name": "route_to_human",
            "description": "Route a dispute ticket to human review when automated resolution is not possible"
        },
        {
            "name": "get_loan_details",
            "description": "Retrieve customer's loan EMI schedule and outstanding balance for loan/EMI disputes"
        },
        {
            "name": "check_merchant_refund_status",
            "description": "Check refund status with merchant/payment gateway to verify if refund has been initiated"
        },
        {
            "name": "query_compliance_policy",
            "description": "Query the compliance MCP server for the most relevant bank dispute policy paragraph"
        },
        {
            "name": "verify_receipt_amount",
            "description": "Verify customer-uploaded receipt amount against ledger for incorrect amount disputes"
        },
        {
            "name": "initiate_chargeback",
            "description": "Initiate a chargeback with the card network for merchant disputes"
        },
        {
            "name": "analyze_receipt_evidence",
            "description": "Analyze a Base64 receipt image to extract charged amount and merchant name for 'incorrect_amount' disputes"
        },
        {
            "name": "get_delivery_tracking_status",
            "description": "Get delivery tracking status for merchant disputes involving undelivered items"
        },
        {
            "name": "check_merchant_reputation_score",
            "description": "Check merchant reputation score based on historical dispute patterns"
        },
        {
            "name": "get_merchant_dispute_history",
            "description": "Get historical dispute data for a specific merchant to identify patterns"
        },
        {
            "name": "check_subscription_status",
            "description": "Check if customer has an active subscription with the merchant"
        },
        {
            "name": "verify_subscription_cancellation",
            "description": "Verify if customer properly cancelled subscription before disputed charge"
        },
        {
            "name": "get_refund_timeline",
            "description": "Get detailed refund processing timeline and current stage with recommendations"
        }
    ]
    return tools

# Made with Bob
