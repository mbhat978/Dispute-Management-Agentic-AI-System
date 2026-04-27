"""
Evidence Quality Scoring System for Dispute Resolution

This module assesses the quality and completeness of evidence gathered
during dispute investigation to ensure reliable decision-making.
"""

from typing import Dict, Any, List, Tuple
from loguru import logger


def calculate_evidence_quality_score(
    category: str,
    gathered_data: Dict[str, Any],
    investigation_summary: str = ""
) -> Tuple[float, List[str], str]:
    """
    Calculate evidence quality score (0.0-1.0) based on completeness and relevance
    
    Args:
        category: Dispute category
        gathered_data: Evidence collected during investigation
        investigation_summary: Summary from investigator agent
        
    Returns:
        Tuple of (quality_score, quality_factors, recommendation)
    """
    logger.info(
        "[EVIDENCE SCORER] Calculating evidence quality",
        category=category,
        evidence_count=len(gathered_data)
    )
    
    # Define required evidence for each category
    evidence_requirements = {
        "fraud": {
            "required": ["transaction_details", "customer_history"],
            "optional": ["fraud_risk_score", "device_analysis"],
            "weight": 1.0
        },
        "duplicate": {
            "required": ["transaction_details", "duplicate_check"],
            "optional": ["customer_history"],
            "weight": 1.0
        },
        "atm_failure": {
            "required": ["transaction_details", "atm_logs"],
            "optional": ["customer_history"],
            "weight": 1.0
        },
        "merchant_dispute": {
            "required": ["transaction_details"],
            "optional": ["delivery_status", "merchant_history", "merchant_reputation", "refund_status"],
            "weight": 0.9  # Harder to get complete evidence
        },
        "loan_dispute": {
            "required": ["transaction_details", "loan_details"],
            "optional": ["customer_history"],
            "weight": 0.95
        },
        "refund_not_received": {
            "required": ["transaction_details", "refund_status"],
            "optional": ["refund_timeline", "merchant_history"],
            "weight": 1.0
        },
        "failed_transaction": {
            "required": ["transaction_details"],
            "optional": ["customer_history"],
            "weight": 1.0
        },
        "incorrect_amount": {
            "required": ["transaction_details"],
            "optional": ["receipt_verification", "receipt_analysis"],
            "weight": 1.0
        },
        "subscription_cancellation": {
            "required": ["transaction_details", "subscription_status"],
            "optional": ["cancellation_verification"],
            "weight": 0.95
        },
        "unknown": {
            "required": ["transaction_details"],
            "optional": [],
            "weight": 0.7
        }
    }
    
    requirements = evidence_requirements.get(category, evidence_requirements["unknown"])
    required_evidence = requirements["required"]
    optional_evidence = requirements["optional"]
    category_weight = requirements["weight"]
    
    # Calculate completeness score
    evidence_keys = set(gathered_data.keys())
    required_keys = set(required_evidence)
    optional_keys = set(optional_evidence)
    
    # Required evidence score (70% weight)
    required_found = required_keys.intersection(evidence_keys)
    required_score = len(required_found) / len(required_keys) if required_keys else 1.0
    
    # Optional evidence score (30% weight)
    optional_found = optional_keys.intersection(evidence_keys)
    optional_score = len(optional_found) / len(optional_keys) if optional_keys else 0.5
    
    # Weighted completeness
    completeness_score = (required_score * 0.7) + (optional_score * 0.3)
    
    # Quality factors
    quality_factors = []
    
    # Check required evidence
    if required_score == 1.0:
        quality_factors.append(f"✓ All required evidence collected ({len(required_found)}/{len(required_keys)})")
    elif required_score >= 0.5:
        missing = required_keys - required_found
        quality_factors.append(f"⚠ Partial required evidence ({len(required_found)}/{len(required_keys)}) - Missing: {', '.join(missing)}")
    else:
        missing = required_keys - required_found
        quality_factors.append(f"❌ Insufficient required evidence ({len(required_found)}/{len(required_keys)}) - Missing: {', '.join(missing)}")
    
    # Check optional evidence
    if optional_score > 0.7:
        quality_factors.append(f"✓ Strong optional evidence ({len(optional_found)}/{len(optional_keys)})")
    elif optional_score > 0.3:
        quality_factors.append(f"✓ Some optional evidence ({len(optional_found)}/{len(optional_keys)})")
    else:
        quality_factors.append(f"⚠ Limited optional evidence ({len(optional_found)}/{len(optional_keys)})")
    
    # Assess evidence content quality
    content_quality_score, content_factors = _assess_evidence_content_quality(gathered_data)
    quality_factors.extend(content_factors)
    
    # Check investigation summary quality
    summary_quality = _assess_summary_quality(investigation_summary)
    if summary_quality >= 0.8:
        quality_factors.append("✓ Comprehensive investigation summary")
    elif summary_quality >= 0.5:
        quality_factors.append("✓ Adequate investigation summary")
    else:
        quality_factors.append("⚠ Limited investigation summary")
    
    # Calculate final quality score
    final_score = (
        (completeness_score * 0.5) +  # 50% weight on completeness
        (content_quality_score * 0.3) +  # 30% weight on content quality
        (summary_quality * 0.2)  # 20% weight on summary
    ) * category_weight
    
    final_score = min(1.0, max(0.0, final_score))
    
    # Generate recommendation
    if final_score >= 0.8:
        recommendation = "High quality evidence - proceed with confidence"
    elif final_score >= 0.6:
        recommendation = "Adequate evidence quality - acceptable for decision"
    elif final_score >= 0.4:
        recommendation = "Moderate evidence quality - consider additional investigation"
    else:
        recommendation = "Low evidence quality - re-investigation strongly recommended"
    
    logger.info(
        "[EVIDENCE SCORER] Quality assessment complete",
        category=category,
        quality_score=final_score,
        completeness=completeness_score,
        content_quality=content_quality_score,
        summary_quality=summary_quality
    )
    
    return round(final_score, 2), quality_factors, recommendation


def _assess_evidence_content_quality(gathered_data: Dict[str, Any]) -> Tuple[float, List[str]]:
    """
    Assess the quality of evidence content (not just presence)
    
    Returns:
        Tuple of (quality_score, quality_factors)
    """
    quality_score = 0.0
    quality_factors = []
    evidence_count = len(gathered_data)
    
    if evidence_count == 0:
        return 0.0, ["❌ No evidence collected"]
    
    # Check for errors in evidence
    error_count = sum(1 for v in gathered_data.values() if isinstance(v, dict) and v.get("error"))
    if error_count > 0:
        quality_factors.append(f"⚠ {error_count} evidence collection errors")
        quality_score -= 0.2
    
    # Check for empty/null evidence
    empty_count = sum(1 for v in gathered_data.values() if not v or v == {})
    if empty_count > 0:
        quality_factors.append(f"⚠ {empty_count} empty evidence items")
        quality_score -= 0.1
    
    # Check for rich evidence (nested data structures)
    rich_count = sum(
        1 for v in gathered_data.values()
        if isinstance(v, dict) and len(v) > 3 and not v.get("error")
    )
    if rich_count >= evidence_count * 0.7:
        quality_factors.append(f"✓ Rich evidence content ({rich_count}/{evidence_count} items)")
        quality_score += 0.3
    
    # Check for specific high-value evidence
    if "fraud_risk_score" in gathered_data:
        fraud_data = gathered_data["fraud_risk_score"]
        if isinstance(fraud_data, dict) and fraud_data.get("fraud_risk_score", 0) > 0:
            quality_factors.append("✓ Fraud risk analysis available")
            quality_score += 0.2
    
    if "receipt_analysis" in gathered_data:
        receipt_data = gathered_data["receipt_analysis"]
        if isinstance(receipt_data, dict) and receipt_data.get("extracted_amount"):
            quality_factors.append("✓ Receipt OCR analysis available")
            quality_score += 0.2
    
    if "delivery_status" in gathered_data:
        delivery_data = gathered_data["delivery_status"]
        if isinstance(delivery_data, dict) and delivery_data.get("tracking_number"):
            quality_factors.append("✓ Delivery tracking available")
            quality_score += 0.2
    
    # Base quality from evidence count
    base_quality = min(1.0, evidence_count / 4)  # 4+ evidence items = full base score
    quality_score += base_quality * 0.5
    
    # Normalize to 0-1
    quality_score = min(1.0, max(0.0, quality_score))
    
    return quality_score, quality_factors


def _assess_summary_quality(summary: str) -> float:
    """
    Assess the quality of investigation summary
    
    Returns:
        Quality score (0.0-1.0)
    """
    if not summary:
        return 0.0
    
    # Length check (good summaries are detailed)
    length_score = min(1.0, len(summary) / 200)  # 200+ chars = full score
    
    # Keyword check (good summaries mention key concepts)
    quality_keywords = [
        "evidence", "investigation", "gathered", "found", "verified",
        "confirmed", "analyzed", "reviewed", "checked", "sufficient"
    ]
    keyword_count = sum(1 for keyword in quality_keywords if keyword.lower() in summary.lower())
    keyword_score = min(1.0, keyword_count / 5)  # 5+ keywords = full score
    
    # Combine scores
    quality = (length_score * 0.6) + (keyword_score * 0.4)
    
    return quality


def identify_missing_evidence(
    category: str,
    gathered_data: Dict[str, Any]
) -> List[str]:
    """
    Identify what evidence is missing for a dispute category
    
    Args:
        category: Dispute category
        gathered_data: Evidence collected so far
        
    Returns:
        List of missing evidence items
    """
    evidence_requirements = {
        "fraud": ["transaction_details", "customer_history", "fraud_risk_score"],
        "duplicate": ["transaction_details", "duplicate_check"],
        "atm_failure": ["transaction_details", "atm_logs"],
        "merchant_dispute": ["transaction_details", "delivery_status", "merchant_history"],
        "loan_dispute": ["transaction_details", "loan_details"],
        "refund_not_received": ["transaction_details", "refund_status", "refund_timeline"],
        "subscription_cancellation": ["transaction_details", "subscription_status", "cancellation_verification"],
        "incorrect_amount": ["transaction_details", "receipt_verification"],
    }
    
    required = evidence_requirements.get(category, ["transaction_details"])
    evidence_keys = set(gathered_data.keys())
    missing = [item for item in required if item not in evidence_keys]
    
    logger.info(
        "[EVIDENCE SCORER] Missing evidence identified",
        category=category,
        missing_count=len(missing),
        missing_items=missing
    )
    
    return missing


def should_reinvestigate(
    evidence_quality_score: float,
    investigation_confidence: float,
    iteration_count: int,
    max_iterations: int = 3
) -> Tuple[bool, str]:
    """
    Determine if re-investigation is needed based on evidence quality
    
    Args:
        evidence_quality_score: Current evidence quality (0.0-1.0)
        investigation_confidence: Investigator's confidence (0.0-1.0)
        iteration_count: Current iteration number
        max_iterations: Maximum allowed iterations
        
    Returns:
        Tuple of (should_reinvestigate, reason)
    """
    if iteration_count >= max_iterations:
        return False, f"Maximum iterations ({max_iterations}) reached"
    
    if evidence_quality_score < 0.4:
        return True, f"Low evidence quality ({evidence_quality_score:.0%}) requires additional investigation"
    
    if investigation_confidence < 0.5 and evidence_quality_score < 0.6:
        return True, f"Low confidence ({investigation_confidence:.0%}) with moderate evidence quality ({evidence_quality_score:.0%})"
    
    if evidence_quality_score < 0.6 and iteration_count == 0:
        return True, f"Moderate evidence quality ({evidence_quality_score:.0%}) on first pass - one more iteration recommended"
    
    return False, "Evidence quality sufficient"


# Made with Bob - Evidence Quality Scoring System