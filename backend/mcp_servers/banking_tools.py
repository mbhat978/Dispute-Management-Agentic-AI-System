"""
Banking Tools for ReAct Agents

This module provides a set of tools that AI agents can use to interact with
the banking dispute management system. Each function queries or modifies the
database and returns structured information that agents can use for decision-making.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, cast
from sqlalchemy.orm import Session
import json
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Navigate up from the backend directory to the project root to find .env
root_dir = backend_dir.parent
load_dotenv(root_dir / '.env')

from database import SessionLocal
import models


def get_transaction_details(transaction_id: int) -> Dict[str, Any]:
    """
    Retrieve complete details for a specific transaction.
    
    This function fetches all information about a transaction including
    customer details, merchant information, transaction status, and whether
    it was an international transaction.
    
    Args:
        transaction_id (int): The unique identifier of the transaction.
        
    Returns:
        Dict[str, Any]: A dictionary containing transaction details including:
            - transaction_id: Transaction ID
            - customer_id: Customer ID
            - customer_name: Name of the customer
            - account_tier: Customer's account tier (Basic, Premium, Gold)
            - amount: Transaction amount
            - merchant_name: Name of the merchant
            - transaction_date: Date and time of transaction
            - status: Transaction status (success, failed, pending)
            - is_international: Boolean indicating if international
            - error: Error message if transaction not found
            
    Example:
        >>> details = get_transaction_details(1)
        >>> print(details['amount'])
        8500.0
    """
    db = SessionLocal()
    try:
        transaction = db.query(models.Transaction).filter(
            models.Transaction.id == transaction_id
        ).first()
        
        if not transaction:
            return {
                "error": f"Transaction ID {transaction_id} not found",
                "transaction_id": transaction_id
            }
        
        # Get customer information
        customer = db.query(models.Customer).filter(
            models.Customer.id == transaction.customer_id
        ).first()
        
        # Query past disputes for this transaction
        past_tickets = db.query(models.DisputeTicket).filter(
            models.DisputeTicket.transaction_id == transaction_id
        ).all()
        
        result = {
            "transaction_id": transaction.id,
            "customer_id": transaction.customer_id,
            "customer_name": customer.name if customer else "Unknown",
            "account_tier": customer.account_tier if customer else "Unknown",
            "amount": transaction.amount,
            "merchant_name": transaction.merchant_name,
            "transaction_date": transaction.transaction_date.isoformat(),
            "status": transaction.status,
            "is_international": transaction.is_international,
            "refunded_amount": transaction.refunded_amount,
            "transaction_type": transaction.transaction_type,
            "past_disputes": [
                {
                    "ticket_id": t.id,
                    "status": t.status,
                    "category": t.dispute_category,
                    "created_at": t.created_at.isoformat()
                }
                for t in past_tickets
            ]
        }
        
        return result
        
    finally:
        db.close()


def get_customer_history(customer_id: int, limit: int = 5) -> Dict[str, Any]:
    """
    Retrieve the transaction history for a specific customer.
    
    This function returns the most recent transactions for a customer,
    which is useful for understanding spending patterns, detecting fraud,
    and providing context for dispute resolution.
    
    Args:
        customer_id (int): The unique identifier of the customer.
        limit (int, optional): Maximum number of transactions to return. 
            Defaults to 5.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - customer_id: Customer ID
            - customer_name: Name of the customer
            - account_tier: Customer's account tier
            - average_monthly_balance: Customer's average balance
            - transaction_count: Total number of transactions found
            - transactions: List of transaction dictionaries with details
            - error: Error message if customer not found
            
    Example:
        >>> history = get_customer_history(1)
        >>> print(f"Found {history['transaction_count']} transactions")
        Found 2 transactions
    """
    db = SessionLocal()
    try:
        customer = db.query(models.Customer).filter(
            models.Customer.id == customer_id
        ).first()
        
        if not customer:
            return {
                "error": f"Customer ID {customer_id} not found",
                "customer_id": customer_id
            }
        
        # Get recent transactions
        transactions = db.query(models.Transaction).filter(
            models.Transaction.customer_id == customer_id
        ).order_by(models.Transaction.transaction_date.desc()).limit(limit).all()
        
        transaction_list = []
        for trans in transactions:
            transaction_list.append({
                "transaction_id": trans.id,
                "amount": trans.amount,
                "merchant_name": trans.merchant_name,
                "transaction_date": trans.transaction_date.isoformat(),
                "status": trans.status,
                "is_international": trans.is_international,
                "transaction_type": getattr(trans, "transaction_type", "debit")
            })
        
        result = {
            "customer_id": customer.id,
            "customer_name": customer.name,
            "account_tier": customer.account_tier,
            "current_account_balance": customer.current_account_balance,
            "transaction_count": len(transaction_list),
            "transactions": transaction_list
        }
        
        return result
        
    finally:
        db.close()


def check_atm_logs(transaction_id: int) -> Dict[str, Any]:
    """
    Query ATM logs for a specific transaction.
    
    This function checks if there are any ATM logs associated with a
    transaction, which is critical for verifying ATM-related disputes.
    ATM logs contain status codes that indicate whether cash was dispensed
    or if there was a hardware fault.
    
    Args:
        transaction_id (int): The unique identifier of the transaction.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - transaction_id: Transaction ID
            - atm_log_found: Boolean indicating if ATM log exists
            - atm_logs: List of ATM log entries (if found) with:
                - log_id: ATM log ID
                - atm_id: ATM machine identifier
                - status_code: Status code (e.g., '200_DISPENSED', '500_HARDWARE_FAULT')
            - message: Human-readable message about the findings
            
    Example:
        >>> atm_info = check_atm_logs(6)
        >>> print(atm_info['atm_logs'][0]['status_code'])
        500_HARDWARE_FAULT
    """
    db = SessionLocal()
    try:
        atm_logs = db.query(models.ATM_Log).filter(
            models.ATM_Log.transaction_id == transaction_id
        ).all()
        
        if not atm_logs:
            return {
                "transaction_id": transaction_id,
                "atm_log_found": False,
                "atm_logs": [],
                "message": f"No ATM logs found for transaction {transaction_id}"
            }
        
        log_list = []
        for log in atm_logs:
            log_list.append({
                "log_id": log.id,
                "atm_id": log.atm_id,
                "status_code": log.status_code
            })
        
        # Analyze the status codes
        has_fault = any('FAULT' in log.status_code or '500' in log.status_code 
                       for log in atm_logs)
        has_dispensed = any('DISPENSED' in log.status_code or '200' in log.status_code 
                           for log in atm_logs)
        
        if has_fault:
            message = "ATM hardware fault detected. Cash was likely not dispensed."
        elif has_dispensed:
            message = "ATM log shows successful cash dispensing."
        else:
            message = "ATM log status is unclear."
        
        result = {
            "transaction_id": transaction_id,
            "atm_log_found": True,
            "atm_logs": log_list,
            "has_hardware_fault": has_fault,
            "has_successful_dispense": has_dispensed,
            "message": message
        }
        
        return result
        
    finally:
        db.close()


def check_duplicate_transactions(
    customer_id: int,
    merchant_name: str,
    amount: float,
    date: datetime,
    time_window_hours: int = 24
) -> Dict[str, Any]:
    """
    Check for duplicate transactions within a time window.
    
    This function searches for transactions with the same merchant name
    and amount within a specified time window, which is useful for
    detecting duplicate charges or fraudulent activity.
    
    Args:
        customer_id (int): The unique identifier of the customer.
        merchant_name (str): The name of the merchant to search for.
        amount (float): The transaction amount to match.
        date (datetime): The reference date/time for the search window.
        time_window_hours (int, optional): Hours before and after the reference
            date to search. Defaults to 24 hours.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - customer_id: Customer ID
            - merchant_name: Merchant name searched
            - amount: Amount searched
            - reference_date: The reference date used
            - time_window_hours: Time window used for search
            - duplicates_found: Boolean indicating if duplicates exist
            - duplicate_count: Number of duplicate transactions found
            - transactions: List of matching transactions with details
            - message: Human-readable summary of findings
            
    Example:
        >>> duplicates = check_duplicate_transactions(4, "Coffee Shop Downtown", 89.99, datetime.now())
        >>> print(f"Found {duplicates['duplicate_count']} duplicate transactions")
        Found 2 duplicate transactions
    """
    db = SessionLocal()
    try:
        # Calculate time window
        start_time = date - timedelta(hours=time_window_hours)
        end_time = date + timedelta(hours=time_window_hours)
        
        # Query for matching transactions
        transactions = db.query(models.Transaction).filter(
            models.Transaction.customer_id == customer_id,
            models.Transaction.merchant_name == merchant_name,
            models.Transaction.amount == amount,
            models.Transaction.transaction_date >= start_time,
            models.Transaction.transaction_date <= end_time
        ).order_by(models.Transaction.transaction_date).all()
        
        transaction_list = []
        for trans in transactions:
            transaction_list.append({
                "transaction_id": trans.id,
                "amount": trans.amount,
                "merchant_name": trans.merchant_name,
                "transaction_date": trans.transaction_date.isoformat(),
                "status": trans.status,
                "time_difference_minutes": abs(
                    (trans.transaction_date - date).total_seconds() / 60
                )
            })
        
        duplicate_count = len(transaction_list)
        duplicates_found = duplicate_count > 1
        
        if duplicates_found:
            # Calculate time between first and last transaction
            if duplicate_count >= 2:
                time_diff = (transactions[-1].transaction_date - 
                           transactions[0].transaction_date).total_seconds() / 60
                message = (f"Found {duplicate_count} transactions to {merchant_name} "
                          f"for ${amount:.2f} within {time_diff:.1f} minutes. "
                          f"Likely duplicate charge.")
            else:
                message = f"Found {duplicate_count} matching transactions."
        else:
            message = f"No duplicate transactions found for {merchant_name} at ${amount:.2f}"
        
        result = {
            "customer_id": customer_id,
            "merchant_name": merchant_name,
            "amount": amount,
            "reference_date": date.isoformat(),
            "time_window_hours": time_window_hours,
            "duplicates_found": duplicates_found,
            "duplicate_count": duplicate_count,
            "transactions": transaction_list,
            "message": message
        }
        
        return result
        
    finally:
        db.close()


def block_card(customer_id: int, reason: str = "Suspected fraud") -> Dict[str, Any]:
    """
    Block a customer's card due to suspected fraud or security concerns.
    
    This is a dummy function that simulates blocking a card. In a real
    system, this would interact with card management systems to
    immediately block the card and prevent further transactions.
    
    Args:
        customer_id (int): The unique identifier of the customer whose
            card should be blocked.
        reason (str, optional): The reason for blocking the card.
            Defaults to "Suspected fraud".
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status: "success" or "error"
            - customer_id: Customer ID
            - action: Description of the action taken
            - reason: Reason for blocking
            - timestamp: When the block was initiated
            - message: Human-readable confirmation message
            
    Example:
        >>> result = block_card(2, "High-value international transaction")
        >>> print(result['message'])
        Card for customer 2 has been blocked successfully.
    """
    db = SessionLocal()
    try:
        # Verify customer exists
        customer = db.query(models.Customer).filter(
            models.Customer.id == customer_id
        ).first()
        
        if not customer:
            return {
                "status": "error",
                "customer_id": customer_id,
                "message": f"Customer ID {customer_id} not found. Cannot block card."
            }
        
        # Simulate blocking the card
        result = {
            "status": "success",
            "customer_id": customer_id,
            "customer_name": customer.name,
            "action": "card_blocked",
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Card for customer {customer_id} ({customer.name}) has been blocked successfully. Reason: {reason}"
        }
        
        return result
        
    finally:
        db.close()


def initiate_refund(
    transaction_id: int,
    amount: float,
    reason: str = "Approved dispute"
) -> Dict[str, Any]:
    """
    Initiate a refund for a disputed transaction.
    
    This function initiates a refund and updates the customer's current account
    balance in real-time by adding the refund amount to their balance.
    
    Args:
        transaction_id (int): The unique identifier of the transaction to refund.
        amount (float): The amount to refund (can be partial or full).
        reason (str, optional): The reason for the refund.
            Defaults to "Approved dispute".
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status: "success" or "error"
            - transaction_id: Transaction ID
            - refund_amount: Amount being refunded
            - reason: Reason for refund
            - timestamp: When the refund was initiated
            - estimated_processing_days: Estimated days for refund to process
            - message: Human-readable confirmation message
            
    Example:
        >>> result = initiate_refund(2, 450.00, "Failed transaction with amount deducted")
        >>> print(result['message'])
        Refund of $450.00 initiated successfully for transaction 2.
    """
    db = SessionLocal()
    try:
        # Verify transaction exists
        transaction = db.query(models.Transaction).filter(
            models.Transaction.id == transaction_id
        ).first()
        
        if not transaction:
            return {
                "status": "error",
                "transaction_id": transaction_id,
                "message": f"Transaction ID {transaction_id} not found. Cannot initiate refund."
            }
        
        # CRITICAL SECURITY CHECK: Block refunds on credit/deposit transactions
        if getattr(transaction, "transaction_type", "debit") == "credit":
            return {
                "status": "error",
                "transaction_id": transaction_id,
                "message": f"CRITICAL ERROR: Cannot issue a refund for a credit/deposit transaction."
            }
        
        # Validate refund amount - prevent double-dipping
        transaction_amount = cast(float, transaction.amount)
        refunded_already = cast(float, getattr(transaction, "refunded_amount", 0.0))
        if amount + refunded_already > transaction_amount:
            return {
                "status": "error",
                "transaction_id": transaction_id,
                "message": f"Cannot refund ${amount:.2f}. Transaction of ${transaction_amount:.2f} already has ${refunded_already:.2f} refunded."
            }
        
        # Get the customer and update their balance
        customer = db.query(models.Customer).filter(
            models.Customer.id == transaction.customer_id
        ).first()
        
        if customer:
            # Add refund amount to customer's current account balance
            old_balance = cast(float, customer.current_account_balance)
            new_balance = old_balance + amount
            setattr(customer, "current_account_balance", new_balance)
            
            # Update the transaction's refunded amount
            setattr(transaction, "refunded_amount", refunded_already + amount)
            
            # Create refund ledger record
            refund_tx = models.Transaction(
                customer_id=transaction.customer_id,
                amount=amount,
                merchant_name=f"REFUND - {transaction.merchant_name}",
                status="success",
                is_international=False,
                refunded_amount=0.0,
                transaction_type="credit"
            )
            db.add(refund_tx)
            
            db.commit()
            db.refresh(customer)
            db.refresh(transaction)
        else:
            return {
                "status": "error",
                "transaction_id": transaction_id,
                "message": f"Customer not found for transaction {transaction_id}. Cannot update balance."
            }
        
        # Return success with updated balance information
        result = {
            "status": "success",
            "transaction_id": transaction_id,
            "customer_id": transaction.customer_id,
            "merchant_name": transaction.merchant_name,
            "original_amount": transaction_amount,
            "refund_amount": amount,
            "total_refunded": refunded_already + amount,
            "reason": reason,
            "old_balance": old_balance,
            "new_balance": new_balance,
            "timestamp": datetime.utcnow().isoformat(),
            "estimated_processing_days": 3,
            "message": f"Refund of ${amount:.2f} initiated successfully for transaction {transaction_id}. Customer balance updated from ${old_balance:.2f} to ${new_balance:.2f}. Total refunded: ${refunded_already + amount:.2f}. Estimated processing time: 3-5 business days."
        }
        
        return result
        
    finally:
        db.close()


def route_to_human(ticket_id: int, summary: str) -> Dict[str, Any]:
    """
    Route a dispute ticket to human review.
    
    This function updates the dispute ticket status to 'human_review_required'
    and saves a summary of why human intervention is needed. This is used
    when automated systems cannot confidently resolve a dispute.
    
    Args:
        ticket_id (int): The unique identifier of the dispute ticket.
        summary (str): A summary explaining why human review is required,
            including key findings and concerns.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - status: "success" or "error"
            - ticket_id: Dispute ticket ID
            - previous_status: Previous status of the ticket
            - new_status: Updated status (human_review_required)
            - summary: The summary that was saved
            - timestamp: When the ticket was routed
            - message: Human-readable confirmation message
            
    Example:
        >>> result = route_to_human(1, "High-value international transaction with no prior history")
        >>> print(result['message'])
        Ticket 1 has been routed to human review.
    """
    db = SessionLocal()
    try:
        # Find the dispute ticket
        ticket = db.query(models.DisputeTicket).filter(
            models.DisputeTicket.id == ticket_id
        ).first()
        
        if not ticket:
            return {
                "status": "error",
                "ticket_id": ticket_id,
                "message": f"Dispute ticket ID {ticket_id} not found."
            }
        
        # Save previous status
        previous_status = cast(str, ticket.status)
        
        # Update ticket status and resolution notes
        human_review_status = "human_review_required"
        setattr(ticket, "status", human_review_status)
        setattr(ticket, "resolution_notes", summary)
        setattr(ticket, "updated_at", datetime.utcnow())
        
        db.commit()
        db.refresh(ticket)
        
        result = {
            "status": "success",
            "ticket_id": ticket_id,
            "transaction_id": ticket.transaction_id,
            "customer_id": ticket.customer_id,
            "previous_status": previous_status,
            "new_status": human_review_status,
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Ticket {ticket_id} has been routed to human review. Previous status: {previous_status}"
        }
        
        return result
        
    finally:
        db.close()


def get_loan_details(customer_id: int) -> Dict[str, Any]:
    """
    Retrieve the customer's loan EMI schedule and outstanding balance.
    
    This function fetches loan account information for a customer, which is
    useful for handling loan/EMI related disputes such as incorrect EMI
    deductions, payment processing issues, or outstanding balance queries.
    
    Args:
        customer_id (int): The unique identifier of the customer.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - customer_id: Customer ID
            - customer_name: Name of the customer
            - loan_found: Boolean indicating if loan account exists
            - loan_details: Loan information (if found) with:
                - loan_id: Loan account ID
                - monthly_emi_amount: Monthly EMI payment amount
                - total_outstanding: Total outstanding loan balance
            - message: Human-readable message about the findings
            - error: Error message if customer not found
            
    Example:
        >>> loan_info = get_loan_details(1)
        >>> print(f"EMI: ${loan_info['loan_details']['monthly_emi_amount']}")
        EMI: $5000.0
    """
    db = SessionLocal()
    try:
        # Verify customer exists
        customer = db.query(models.Customer).filter(
            models.Customer.id == customer_id
        ).first()
        
        if not customer:
            return {
                "error": f"Customer ID {customer_id} not found",
                "customer_id": customer_id
            }
        
        # Get loan account
        loan = db.query(models.LoanAccount).filter(
            models.LoanAccount.customer_id == customer_id
        ).first()
        
        if not loan:
            return {
                "customer_id": customer_id,
                "customer_name": customer.name,
                "loan_found": False,
                "loan_details": None,
                "message": f"No loan account found for customer {customer_id} ({customer.name})"
            }
        
        result = {
            "customer_id": customer_id,
            "customer_name": customer.name,
            "loan_found": True,
            "loan_details": {
                "loan_id": loan.id,
                "monthly_emi_amount": loan.monthly_emi_amount,
                "total_outstanding": loan.total_outstanding
            },
            "message": f"Loan account found for {customer.name}. Monthly EMI: ${loan.monthly_emi_amount:.2f}, Outstanding: ${loan.total_outstanding:.2f}"
        }
        
        return result
        
    finally:
        db.close()


def check_merchant_refund_status(transaction_id: int) -> Dict[str, Any]:
    """
    Check the refund status with the merchant/payment gateway.
    
    This is a dummy function that simulates checking refund status with
    merchants or payment gateways. In a real system, this would integrate
    with payment gateway APIs to verify if a refund has been initiated
    by the merchant or is pending at the gateway level.
    
    Args:
        transaction_id (int): The unique identifier of the transaction.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - transaction_id: Transaction ID
            - refund_status: Status string ('Refund Pending at Gateway' or
                           'No Refund Initiated by Merchant')
            - message: Human-readable explanation of the status
            - timestamp: When the check was performed
            - recommendation: Suggested action based on status
            
    Example:
        >>> status = check_merchant_refund_status(3)
        >>> print(status['refund_status'])
        Refund Pending at Gateway
    """
    import random
    
    db = SessionLocal()
    try:
        # Verify transaction exists
        transaction = db.query(models.Transaction).filter(
            models.Transaction.id == transaction_id
        ).first()
        
        if not transaction:
            return {
                "error": f"Transaction ID {transaction_id} not found",
                "transaction_id": transaction_id
            }
        
        # Randomly determine refund status (simulating external API call)
        statuses = [
            "Refund Pending at Gateway",
            "No Refund Initiated by Merchant"
        ]
        refund_status = random.choice(statuses)
        
        # Generate appropriate message and recommendation
        if refund_status == "Refund Pending at Gateway":
            message = (f"Refund for transaction {transaction_id} is pending at the payment gateway. "
                      f"The merchant has initiated the refund, but it is still being processed.")
            recommendation = "Wait 3-5 business days for gateway processing. If not received, escalate to gateway support."
        else:
            message = (f"No refund has been initiated by merchant {transaction.merchant_name} "
                      f"for transaction {transaction_id}.")
            recommendation = "Contact merchant to initiate refund or consider chargeback if merchant is unresponsive."
        
        result = {
            "transaction_id": transaction_id,
            "merchant_name": transaction.merchant_name,
            "transaction_amount": transaction.amount,
            "refund_status": refund_status,
            "message": message,
            "recommendation": recommendation,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return result
        
    finally:
        db.close()


def verify_receipt_amount(transaction_id: int, claimed_amount: float) -> Dict[str, Any]:
    """
    Verify a customer-uploaded receipt amount against the ledger.
    
    This function simulates OCR checking of a customer-uploaded receipt
    against the transaction ledger. It's useful for handling 'Incorrect Amount'
    disputes where customers claim they were charged more than what appears
    on their receipt.
    
    Args:
        transaction_id (int): The unique identifier of the transaction.
        claimed_amount (float): The amount the customer claims they should have been charged.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - transaction_id: Transaction ID
            - billed_amount: The amount actually charged
            - claimed_amount: The amount customer claims
            - is_receipt_valid: Boolean indicating if receipt is valid
            - discrepancy_amount: Difference between billed and claimed amounts
            - message: Human-readable explanation
            - error: Error message if transaction not found
            
    Example:
        >>> result = verify_receipt_amount(1, 75.00)
        >>> print(result['message'])
        Receipt verified. Billed amount exceeds claimed amount.
    """
    # Simulates OCR checking a customer-uploaded receipt against the ledger
    db = SessionLocal()
    try:
        transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
        if not transaction:
            return {"error": "Transaction not found"}
        
        # Mock logic: Assume the claimed amount is correct if it's less than the billed amount
        transaction_amount = cast(float, transaction.amount)
        is_match = claimed_amount < transaction_amount
        difference = transaction_amount - claimed_amount
        return {
            "transaction_id": transaction_id,
            "billed_amount": transaction_amount,
            "claimed_amount": claimed_amount,
            "is_receipt_valid": is_match,
            "discrepancy_amount": difference if is_match else 0.0,
            "message": "Receipt verified. Billed amount exceeds claimed amount." if is_match else "Claimed amount invalid or higher than billed."
        }
    finally:
        db.close()


def initiate_chargeback(transaction_id: int, reason: str) -> Dict[str, Any]:
    """
    Initiate a chargeback with the card network (Visa/Mastercard).
    
    This function simulates filing a chargeback with the card network for
    merchant disputes. It's useful when merchants are unresponsive or when
    goods/services were not provided as promised.
    
    Args:
        transaction_id (int): The unique identifier of the transaction.
        reason (str): The reason for the chargeback (e.g., "goods_not_provided",
                     "merchant_unresponsive", "defective_merchandise").
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - transaction_id: Transaction ID
            - chargeback_status: Status of the chargeback ("initiated")
            - network_reason_code: Card network reason code
            - message: Human-readable confirmation message
            
    Example:
        >>> result = initiate_chargeback(5, "goods_not_provided")
        >>> print(result['message'])
        Chargeback initiated with card network for reason: goods_not_provided. Provisional credit may be applied.
    """
    # Simulates filing a chargeback with Visa/Mastercard network
    return {
        "transaction_id": transaction_id,
        "chargeback_status": "initiated",
        "network_reason_code": "goods_not_provided",
        "message": f"Chargeback initiated with card network for reason: {reason}. Provisional credit may be applied."
    }


async def analyze_receipt_evidence(receipt_base64: str, expected_merchant: str) -> str:
    """
    Analyzes a Base64 receipt image using GPT-4o Vision to extract the actual charged amount and merchant name.
    Use this tool whenever a customer uploads a receipt to verify 'incorrect_amount' or 'merchant_dispute' claims.
    
    Args:
        receipt_base64 (str): Base64-encoded receipt image data.
        expected_merchant (str): The merchant name from the transaction record for comparison.
        
    Returns:
        str: JSON string containing:
            - extracted_merchant: Merchant name extracted from receipt
            - extracted_amount: Amount extracted from receipt
            - receipt_legibility: Quality of the receipt image (High/Medium/Low)
            - fraud_indicators_found: Boolean indicating if fraud indicators were detected
            - note: Additional notes about the receipt analysis
            - error: Error message if receipt is invalid
            
    Example:
        >>> result = await analyze_receipt_evidence("base64_image_data...", "Coffee Shop")
        >>> parsed = json.loads(result)
        >>> print(parsed['extracted_merchant'])
        Coffee Shop
    """
    if not receipt_base64:
        return json.dumps({"error": "No receipt image provided."})
        
    try:
        # Format the string for OpenAI Vision API (ensure it has the data URI scheme)
        image_url = receipt_base64
        if not image_url.startswith("data:image"):
            image_url = f"data:image/jpeg;base64,{receipt_base64}"
            
        # Initialize GPT-4o with temperature 0 for strictly analytical extraction
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        
        prompt_text = f"""
        You are a forensic financial AI. Analyze this receipt image.
        The customer claims the transaction was with '{expected_merchant}'.
        
        Extract the actual merchant name printed on the receipt and the final total charged amount.
        Look for any signs of tampering or inconsistencies.
        
        You MUST return ONLY a valid JSON object (do not include markdown formatting or ```json wrappers).
        Use this exact JSON schema:
        {{
            "extracted_merchant": "string",
            "extracted_amount": "number or string",
            "receipt_legibility": "High" | "Medium" | "Low",
            "fraud_indicators_found": boolean,
            "note": "brief explanation of your findings, including if the amount matches or differs wildly"
        }}
        """
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        )
        
        # Execute the vision model call
        response = await llm.ainvoke([message])
        
        # Clean up potential markdown formatting from the response
        content_str = str(response.content) if not isinstance(response.content, str) else response.content
        cleaned_content = content_str.replace("```json", "").replace("```", "").strip()
        
        # Verify it's valid JSON before returning to the Investigator agent
        parsed_json = json.loads(cleaned_content)
        return json.dumps(parsed_json)
        
    except Exception as e:
        # Graceful fallback that forces a human review if the AI fails to read the image
        return json.dumps({
            "error": f"Vision analysis failed: {str(e)}",
            "fraud_indicators_found": True,
            "note": "Failed to process receipt image. Manual human review of the evidence is required."
        })


# Helper function to get all available tools for agent introspection
def get_available_tools() -> List[Dict[str, str]]:
    """
    Get a list of all available banking tools with their descriptions.
    
    This function returns metadata about all available tools, which can be
    used by AI agents to understand what actions they can take.
    
    Returns:
        List[Dict[str, str]]: A list of dictionaries containing:
            - name: Function name
            - description: Brief description of what the tool does
            
    Example:
        >>> tools = get_available_tools()
        >>> for tool in tools:
        ...     print(f"{tool['name']}: {tool['description']}")
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
            "name": "verify_receipt_amount",
            "description": "Verify customer-uploaded receipt amount against ledger for 'Incorrect Amount' disputes"
        },
        {
            "name": "initiate_chargeback",
            "description": "Initiate a chargeback with card network (Visa/Mastercard) for merchant disputes"
        },
        {
            "name": "analyze_receipt_evidence",
            "description": "Analyze a Base64 receipt image to extract charged amount and merchant name for 'incorrect_amount' disputes"
        }
    ]
    return tools
