"""
Fraud Analyst Agent for Banking Dispute Management System

This specialist agent analyzes fraud-related disputes using quantitative
fraud detection tools. It executes fraud risk scoring and dispute fraud
detection without requiring LLM planning.
"""

from typing import Dict, Any
from loguru import logger
from datetime import datetime

try:
    from .. import mcp_client as banking_tools
    from .state import DisputeState
    from .fraud_scorer import calculate_fraud_risk_score
    from ..utils.dispute_fraud_detector import detect_dispute_fraud
except ImportError:
    import mcp_client as banking_tools
    from agents.state import DisputeState
    from agents.fraud_scorer import calculate_fraud_risk_score
    from utils.dispute_fraud_detector import detect_dispute_fraud


def fraud_node(state: DisputeState) -> Dict[str, Any]:
    """
    Fraud Analyst Agent: Performs fraud analysis on disputes.
    
    This agent executes fraud detection tools when the category implies fraud:
    - calculate_fraud_risk_score: 5-factor quantitative fraud assessment
    - detect_dispute_fraud: Detects "friendly fraud" patterns
    
    Args:
        state: The current dispute state
        
    Returns:
        Dict with fraud_analysis results and updated audit_trail
    """
    ticket_id = state["ticket_id"]
    customer_id = state["customer_id"]
    category = state["dispute_category"]
    gathered_data = dict(state["gathered_data"])
    audit_trail = list(state["audit_trail"])
    fraud_analysis: Dict[str, Any] = {}
    
    logger.info(
        f"[FRAUD ANALYST AGENT] start | ticket_id={ticket_id} | "
        f"customer_id={customer_id} | category={category}"
    )
    
    # Only perform fraud analysis if category implies fraud
    if category not in ["fraud", "fraudulent_transaction"]:
        logger.info(f"[FRAUD ANALYST AGENT] Skipping - category '{category}' is not fraud-related")
        audit_trail.append(
            f"Fraud Analyst Agent: Skipping analysis - category '{category}' is not fraud-related"
        )
        return {
            "fraud_analysis": fraud_analysis,
            "audit_trail": audit_trail
        }
    
    audit_trail.append(
        f"Fraud Analyst Agent THOUGHT: Category '{category}' requires fraud analysis. "
        "Planned steps: ['calculate_fraud_risk_score', 'detect_dispute_fraud']"
    )
    
    try:
        # Get transaction_id from gathered_data
        transaction_details = gathered_data.get("transaction_details", {})
        transaction_id = transaction_details.get("transaction_id")
        
        if not transaction_id:
            logger.warning("[FRAUD ANALYST AGENT] No transaction_id found in gathered_data")
            audit_trail.append(
                "Fraud Analyst Agent ERROR: No transaction details available for fraud analysis"
            )
            return {
                "fraud_analysis": {"error": "No transaction details available"},
                "audit_trail": audit_trail
            }
        
        # Execute fraud risk score calculation
        logger.info("[FRAUD ANALYST AGENT] Action: Calculating fraud risk score")
        audit_trail.append(
            f"Fraud Analyst Agent ACTION: calling calculate_fraud_risk_score with input {{'transaction_id': {transaction_id}, 'customer_id': {customer_id}}}"
        )
        
        fraud_risk_result = _calculate_fraud_risk(
            transaction_id=transaction_id,
            customer_id=customer_id,
            gathered_data=gathered_data
        )
        
        fraud_analysis["fraud_risk_score"] = fraud_risk_result
        logger.info(
            f"[FRAUD ANALYST AGENT] Observation: Fraud risk score = "
            f"{fraud_risk_result.get('fraud_risk_score', 'N/A')}, "
            f"risk_level = {fraud_risk_result.get('risk_level', 'N/A')}"
        )
        audit_trail.append(
            f"Fraud Analyst Agent OBSERVATION: calculate_fraud_risk_score output: {str(fraud_risk_result)}"
        )
        
        # Execute dispute fraud detection
        logger.info("[FRAUD ANALYST AGENT] Action: Detecting dispute fraud patterns")
        audit_trail.append(
            f"Fraud Analyst Agent ACTION: calling detect_dispute_fraud with input {{'customer_id': {customer_id}}}"
        )
        
        dispute_fraud_result = _detect_dispute_fraud(customer_id)
        
        fraud_analysis["dispute_fraud_analysis"] = dispute_fraud_result
        logger.info(
            f"[FRAUD ANALYST AGENT] Observation: Dispute fraud detected = "
            f"{dispute_fraud_result.get('fraud_detected', False)}, "
            f"propensity_score = {dispute_fraud_result.get('customer_propensity_score', 'N/A')}"
        )
        audit_trail.append(
            f"Fraud Analyst Agent OBSERVATION: detect_dispute_fraud output: {str(dispute_fraud_result)}"
        )
        
        # Generate summary
        fraud_analysis["summary"] = _generate_fraud_summary(fraud_risk_result, dispute_fraud_result)
        fraud_analysis["timestamp"] = datetime.utcnow().isoformat()
        
        logger.success(
            f"[FRAUD ANALYST AGENT] complete | fraud_risk_score="
            f"{fraud_risk_result.get('fraud_risk_score', 'N/A')} | "
            f"dispute_fraud_detected={dispute_fraud_result.get('fraud_detected', False)}"
        )
        
        return {
            "fraud_analysis": fraud_analysis,
            "audit_trail": audit_trail
        }
        
    except Exception as e:
        logger.exception(f"Error during fraud analysis: {str(e)}")
        audit_trail.append(f"Fraud Analyst Agent ERROR: {str(e)}")
        return {
            "fraud_analysis": {"error": str(e)},
            "audit_trail": audit_trail
        }


def _calculate_fraud_risk(
    transaction_id: int,
    customer_id: int,
    gathered_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate fraud risk score using the fraud_scorer module.
    
    Args:
        transaction_id: The transaction ID
        customer_id: The customer ID
        gathered_data: Previously gathered data
        
    Returns:
        Fraud risk score result dictionary
    """
    try:
        # Get transaction details
        transaction_details = gathered_data.get("transaction_details", {})
        customer_history_data = gathered_data.get("customer_history", {})
        
        # Prepare transaction data
        transaction = {
            "transaction_id": transaction_id,
            "customer_id": customer_id,
            "amount": transaction_details.get("amount", 0),
            "merchant_name": transaction_details.get("merchant_name", ""),
            "is_international": transaction_details.get("is_international", False),
            "transaction_date": transaction_details.get("transaction_date", ""),
            "status": transaction_details.get("status", "")
        }
        
        # Prepare customer history (exclude disputed transaction)
        all_transactions = customer_history_data.get("transactions", [])
        customer_history = [
            t for t in all_transactions
            if t.get("transaction_id") != transaction_id
        ]
        
        # Prepare customer profile
        customer_profile = {
            "customer_id": customer_id,
            "customer_name": customer_history_data.get("customer_name", ""),
            "account_tier": customer_history_data.get("account_tier", ""),
            "current_account_balance": customer_history_data.get("current_account_balance", 0)
        }
        
        # Calculate fraud risk score
        return calculate_fraud_risk_score(transaction, customer_history, customer_profile)
        
    except Exception as e:
        logger.error(f"[FRAUD ANALYST AGENT] Fraud risk calculation failed: {str(e)}")
        return {
            "error": f"Fraud risk calculation failed: {str(e)}",
            "fraud_risk_score": 0,
            "risk_level": "UNKNOWN"
        }


def _detect_dispute_fraud(customer_id: int) -> Dict[str, Any]:
    """
    Detect dispute fraud patterns using the dispute_fraud_detector module.
    
    Args:
        customer_id: The customer ID
        
    Returns:
        Dispute fraud detection result dictionary
    """
    try:
        is_suspicious, reason, details = detect_dispute_fraud(customer_id)
        
        return {
            "fraud_detected": is_suspicious,
            "reason": reason,
            "customer_propensity_score": details.get("propensity_score", 0),
            "patterns_found": details.get("patterns", []),
            "recommendation": details.get("recommendation", ""),
            "details": details
        }
        
    except Exception as e:
        logger.error(f"[FRAUD ANALYST AGENT] Dispute fraud detection failed: {str(e)}")
        return {
            "error": f"Dispute fraud detection failed: {str(e)}",
            "fraud_detected": False,
            "customer_propensity_score": 0
        }


def _generate_fraud_summary(
    fraud_risk_result: Dict[str, Any],
    dispute_fraud_result: Dict[str, Any]
) -> str:
    """
    Generate a human-readable summary of fraud analysis.
    
    Args:
        fraud_risk_result: Result from fraud risk scoring
        dispute_fraud_result: Result from dispute fraud detection
        
    Returns:
        Summary string
    """
    fraud_score = fraud_risk_result.get("fraud_risk_score", 0)
    risk_level = fraud_risk_result.get("risk_level", "UNKNOWN")
    fraud_detected = dispute_fraud_result.get("fraud_detected", False)
    propensity_score = dispute_fraud_result.get("customer_propensity_score", 0)
    
    summary_parts = []
    
    # Fraud risk assessment
    summary_parts.append(
        f"Transaction fraud risk: {fraud_score}/100 ({risk_level} risk)"
    )
    
    # Dispute fraud assessment
    if fraud_detected:
        summary_parts.append(
            f"Customer dispute fraud patterns detected (propensity score: {propensity_score}/100)"
        )
    else:
        summary_parts.append(
            f"No dispute fraud patterns detected (propensity score: {propensity_score}/100)"
        )
    
    # Overall recommendation
    if fraud_score >= 70 or propensity_score >= 70:
        summary_parts.append("HIGH FRAUD RISK - Recommend approval with card block")
    elif fraud_score >= 30 or propensity_score >= 30:
        summary_parts.append("MEDIUM FRAUD RISK - Recommend further investigation")
    else:
        summary_parts.append("LOW FRAUD RISK - Standard processing recommended")
    
    return ". ".join(summary_parts)


# Made with Bob