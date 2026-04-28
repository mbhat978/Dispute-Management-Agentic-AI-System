"""
Fraud Risk Scoring System for Banking Dispute Management

This module provides comprehensive fraud risk assessment using multiple
factors including velocity, amount anomaly, geographic patterns, and more.
"""

from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
from loguru import logger


def calculate_fraud_risk_score(
    transaction: Dict[str, Any],
    customer_history: List[Dict[str, Any]],
    customer_profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate comprehensive fraud risk score (0-100)
    
    Args:
        transaction: Current disputed transaction details
        customer_history: List of customer's recent transactions
        customer_profile: Customer account information
        
    Returns:
        Dict containing:
        - fraud_risk_score: 0-100 score
        - risk_level: low|medium|high|critical
        - risk_factors: List of identified risk factors
        - recommendation: auto_approve|investigate|auto_reject
    """
    risk_score = 0
    risk_factors = []
    
    logger.info(
        "[FRAUD SCORER] Calculating fraud risk",
        transaction_id=transaction.get("transaction_id"),
        customer_id=transaction.get("customer_id")
    )
    
    # 1. Velocity Check (90 points max)
    velocity_score, velocity_factors = check_transaction_velocity(
        transaction, customer_history
    )
    risk_score += velocity_score
    risk_factors.extend(velocity_factors)
    
    # 2. Amount Anomaly (25 points max)
    amount_score, amount_factors = check_amount_anomaly(
        transaction, customer_history
    )
    risk_score += amount_score
    risk_factors.extend(amount_factors)
    
    # 3. Geographic Anomaly (25 points max)
    geo_score, geo_factors = check_geographic_anomaly(
        transaction, customer_history, customer_profile
    )
    risk_score += geo_score
    risk_factors.extend(geo_factors)
    
    # 4. Time Anomaly (10 points max)
    time_score, time_factors = check_time_anomaly(
        transaction, customer_history
    )
    risk_score += time_score
    risk_factors.extend(time_factors)
    
    # 5. Merchant Category Risk (10 points max)
    merchant_score, merchant_factors = check_merchant_risk(transaction)
    risk_score += merchant_score
    risk_factors.extend(merchant_factors)
    
    # Cap at 100
    risk_score = min(risk_score, 100)
    
    # Determine risk level and recommendation
    if risk_score >= 80:
        risk_level = "critical"
        recommendation = "auto_approve"
    elif risk_score >= 60:
        risk_level = "high"
        recommendation = "auto_approve"
    elif risk_score >= 40:
        risk_level = "medium"
        recommendation = "investigate"
    else:
        risk_level = "low"
        recommendation = "auto_reject"
    
    logger.info(
        "[FRAUD SCORER] Risk assessment complete",
        risk_score=risk_score,
        risk_level=risk_level,
        recommendation=recommendation,
        factors_count=len(risk_factors)
    )
    
    return {
        "fraud_risk_score": risk_score,
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "recommendation": recommendation,
        "scoring_breakdown": {
            "velocity": velocity_score,
            "amount_anomaly": amount_score,
            "geographic": geo_score,
            "time": time_score,
            "merchant": merchant_score
        }
    }


def check_transaction_velocity(
    transaction: Dict[str, Any],
    customer_history: List[Dict[str, Any]]
) -> Tuple[int, List[str]]:
    """
    Check for suspicious transaction velocity patterns
    
    Returns:
        Tuple of (score, risk_factors)
    """
    score = 0
    factors = []
    
    if not customer_history:
        return score, factors
    
    trans_date = transaction.get("transaction_date")
    if isinstance(trans_date, str):
        trans_date = datetime.fromisoformat(trans_date.replace('Z', '+00:00'))
    elif not isinstance(trans_date, datetime):
        return score, factors
    
    # Count transactions in last hour
    one_hour_ago = trans_date - timedelta(hours=1)
    recent_count = sum(
        1 for t in customer_history
        if _parse_date(t.get("transaction_date")) > one_hour_ago
    )
    
    if recent_count > 5:
        score += 65  # Mathematically guarantees a HIGH risk level (>=60)
        factors.append(f"CRITICAL: {recent_count} transactions in last hour")
    elif recent_count > 3:
        score += 45
        factors.append(f"HIGH: {recent_count} transactions in last hour")
    elif recent_count > 2:
        score += 20
        factors.append(f"MEDIUM: {recent_count} transactions in last hour")
    
    # Count transactions in last 24 hours
    one_day_ago = trans_date - timedelta(days=1)
    daily_count = sum(
        1 for t in customer_history
        if _parse_date(t.get("transaction_date")) > one_day_ago
    )
    
    if daily_count > 20:
        score += 25
        factors.append(f"Unusual velocity: {daily_count} transactions in 24 hours")
    elif daily_count > 10:
        score += 15
        factors.append(f"High velocity: {daily_count} transactions in 24 hours")
    
    return score, factors


def check_amount_anomaly(
    transaction: Dict[str, Any],
    customer_history: List[Dict[str, Any]]
) -> Tuple[int, List[str]]:
    """
    Check if transaction amount is anomalous compared to customer's pattern
    
    Returns:
        Tuple of (score, risk_factors)
    """
    score = 0
    factors = []
    
    if not customer_history:
        return score, factors
    
    current_amount = float(transaction.get("amount", 0))
    
    # Calculate average and max from history
    amounts = [float(t.get("amount", 0)) for t in customer_history if t.get("amount")]
    if not amounts:
        return score, factors
    
    avg_amount = sum(amounts) / len(amounts)
    max_amount = max(amounts)
    
    # Check if current amount is significantly higher
    if current_amount > avg_amount * 5:
        score += 25
        factors.append(
            f"CRITICAL: Amount ${current_amount:.2f} is 5x average ${avg_amount:.2f}"
        )
    elif current_amount > avg_amount * 3:
        score += 20
        factors.append(
            f"HIGH: Amount ${current_amount:.2f} is 3x average ${avg_amount:.2f}"
        )
    elif current_amount > avg_amount * 2:
        score += 10
        factors.append(
            f"MEDIUM: Amount ${current_amount:.2f} is 2x average ${avg_amount:.2f}"
        )
    
    # Check if it's the highest transaction ever
    if current_amount > max_amount * 1.5:
        score += 10
        factors.append(
            f"Highest transaction ever: ${current_amount:.2f} vs previous max ${max_amount:.2f}"
        )
    
    return score, factors


def check_geographic_anomaly(
    transaction: Dict[str, Any],
    customer_history: List[Dict[str, Any]],
    customer_profile: Dict[str, Any]
) -> Tuple[int, List[str]]:
    """
    Check for geographic anomalies (international transactions, location changes)
    
    Returns:
        Tuple of (score, risk_factors)
    """
    score = 0
    factors = []
    
    is_international = transaction.get("is_international", False)
    
    if not customer_history:
        if is_international:
            score += 20
            factors.append("First transaction is international")
        return score, factors
    
    # Check if customer has history of international transactions
    has_intl_history = any(
        t.get("is_international", False) for t in customer_history
    )
    
    if is_international and not has_intl_history:
        score += 25
        factors.append("First international transaction - no prior international history")
    elif is_international and has_intl_history:
        # Check frequency of international transactions
        intl_count = sum(1 for t in customer_history if t.get("is_international", False))
        intl_rate = intl_count / len(customer_history)
        
        if intl_rate < 0.1:  # Less than 10% are international
            score += 15
            factors.append(
                f"Rare international transaction (only {intl_rate*100:.0f}% of history)"
            )
    
    return score, factors


def check_time_anomaly(
    transaction: Dict[str, Any],
    customer_history: List[Dict[str, Any]]
) -> Tuple[int, List[str]]:
    """
    Check if transaction time is unusual for this customer
    
    Returns:
        Tuple of (score, risk_factors)
    """
    score = 0
    factors = []
    
    trans_date = transaction.get("transaction_date")
    if isinstance(trans_date, str):
        trans_date = datetime.fromisoformat(trans_date.replace('Z', '+00:00'))
    elif not isinstance(trans_date, datetime):
        return score, factors
    
    hour = trans_date.hour
    
    # Check for unusual hours (2am - 6am)
    if 2 <= hour < 6:
        score += 10
        factors.append(f"Unusual transaction time: {hour:02d}:00 (late night)")
    
    # Check customer's typical transaction hours
    if customer_history:
        history_hours = []
        for t in customer_history:
            t_date = _parse_date(t.get("transaction_date"))
            if t_date:
                history_hours.append(t_date.hour)
        
        if history_hours:
            # Check if current hour is outside typical range
            typical_hours = set(history_hours)
            if hour not in typical_hours and len(typical_hours) > 5:
                score += 5
                factors.append(
                    f"Transaction at {hour:02d}:00 is outside typical hours"
                )
    
    return score, factors


def check_merchant_risk(transaction: Dict[str, Any]) -> Tuple[int, List[str]]:
    """
    Check if merchant category is high-risk
    
    Returns:
        Tuple of (score, risk_factors)
    """
    score = 0
    factors = []
    
    merchant_name = transaction.get("merchant_name", "").lower()
    
    # High-risk merchant categories
    high_risk_keywords = [
        "crypto", "cryptocurrency", "bitcoin", "gambling", "casino",
        "forex", "trading", "gift card", "prepaid", "money transfer",
        "wire transfer", "western union", "moneygram"
    ]
    
    for keyword in high_risk_keywords:
        if keyword in merchant_name:
            score += 10
            factors.append(f"High-risk merchant category: {keyword}")
            break
    
    # Check for generic/suspicious merchant names
    suspicious_patterns = ["temp", "test", "unknown", "merchant", "store"]
    for pattern in suspicious_patterns:
        if pattern in merchant_name and len(merchant_name) < 15:
            score += 5
            factors.append(f"Suspicious merchant name: {merchant_name}")
            break
    
    return score, factors


def _parse_date(date_value: Any) -> datetime:
    """Helper to parse date from various formats"""
    if isinstance(date_value, datetime):
        return date_value
    elif isinstance(date_value, str):
        try:
            return datetime.fromisoformat(date_value.replace('Z', '+00:00'))
        except:
            return datetime.min
    return datetime.min


# Made with Bob - Fraud Risk Scoring System