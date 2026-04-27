"""
Confidence Calibration System for Multi-Agent Dispute Resolution

This module provides confidence aggregation and calibration across all agents
to produce a reliable overall confidence score for dispute decisions.
"""

from typing import Dict, Any, List, Tuple
from loguru import logger


def calculate_overall_confidence(state: Dict[str, Any]) -> float:
    """
    Aggregate confidence scores from all agents with weighted averaging
    
    Weights:
    - Triage: 20% (initial categorization)
    - Investigation: 40% (evidence quality)
    - Decision: 40% (final reasoning)
    
    Args:
        state: DisputeState dictionary
        
    Returns:
        Overall confidence score (0.0-1.0)
    """
    triage_conf = state.get("triage_confidence", 0.0)
    investigation_conf = state.get("investigation_confidence", 0.0)
    decision_conf = state.get("decision_confidence", 0.0)
    
    # Weighted average
    overall = (triage_conf * 0.2) + (investigation_conf * 0.4) + (decision_conf * 0.4)
    
    # Apply penalties for low evidence quality
    evidence_quality = state.get("evidence_quality_score", 0.0)
    if evidence_quality < 0.5:
        penalty = 0.8  # 20% penalty
        overall *= penalty
        logger.info(
            "[CONFIDENCE CALIBRATOR] Low evidence quality penalty applied",
            evidence_quality=evidence_quality,
            penalty_factor=penalty
        )
    
    # Apply penalties for clarification needed
    working_memory = state.get("working_memory", {})
    if working_memory.get("clarification_needed", False):
        penalty = 0.9  # 10% penalty
        overall *= penalty
        logger.info(
            "[CONFIDENCE CALIBRATOR] Clarification needed penalty applied",
            penalty_factor=penalty
        )
    
    # Apply bonus for high iteration count (more thorough investigation)
    iteration_count = state.get("iteration_count", 0)
    if iteration_count > 1:
        bonus = min(1.0, 1.0 + (iteration_count * 0.05))  # 5% bonus per iteration, max 1.0
        overall = min(1.0, overall * bonus)
        logger.info(
            "[CONFIDENCE CALIBRATOR] Multiple iteration bonus applied",
            iteration_count=iteration_count,
            bonus_factor=bonus
        )
    
    # Cap at 1.0
    overall = min(1.0, max(0.0, overall))
    
    logger.info(
        "[CONFIDENCE CALIBRATOR] Overall confidence calculated",
        triage=triage_conf,
        investigation=investigation_conf,
        decision=decision_conf,
        overall=overall
    )
    
    return round(overall, 2)


def calibrate_confidence_by_category(
    confidence: float,
    category: str,
    gathered_data: Dict[str, Any]
) -> float:
    """
    Calibrate confidence based on dispute category and available evidence
    
    Different categories have different evidence requirements and
    typical confidence levels.
    
    Args:
        confidence: Raw confidence score
        category: Dispute category
        gathered_data: Evidence gathered
        
    Returns:
        Calibrated confidence score
    """
    # Category-specific confidence adjustments
    category_adjustments = {
        "fraud": 1.0,  # Fraud detection is typically high confidence
        "atm_failure": 1.1,  # ATM logs provide strong evidence
        "duplicate": 1.05,  # Duplicate detection is reliable
        "failed_transaction": 1.0,  # Transaction status is definitive
        "merchant_dispute": 0.9,  # Requires more subjective judgment
        "loan_dispute": 0.85,  # Complex calculations, lower confidence
        "refund_not_received": 0.95,  # Depends on merchant response
        "incorrect_amount": 1.0,  # Receipt verification is reliable
        "subscription_cancellation": 0.95,  # Depends on cancellation proof
        "unknown": 0.7,  # Unknown category has inherent uncertainty
    }
    
    adjustment = category_adjustments.get(category, 0.9)
    calibrated = confidence * adjustment
    
    # Evidence completeness bonus
    evidence_count = len(gathered_data)
    if evidence_count >= 4:
        calibrated *= 1.05  # 5% bonus for comprehensive evidence
    elif evidence_count <= 1:
        calibrated *= 0.9  # 10% penalty for sparse evidence
    
    calibrated = min(1.0, max(0.0, calibrated))
    
    logger.info(
        "[CONFIDENCE CALIBRATOR] Category-based calibration",
        category=category,
        raw_confidence=confidence,
        adjustment=adjustment,
        evidence_count=evidence_count,
        calibrated=calibrated
    )
    
    return round(calibrated, 2)


def assess_confidence_reliability(
    confidence: float,
    agent_memories: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Assess how reliable the confidence score is based on agent history
    
    Args:
        confidence: Current confidence score
        agent_memories: Historical agent performance data
        
    Returns:
        Dict with reliability assessment
    """
    # Get historical confidence scores
    triage_history = agent_memories.get("triage", {}).get("confidence_history", [])
    investigator_history = agent_memories.get("investigator", {}).get("confidence_history", [])
    decision_history = agent_memories.get("decision", {}).get("confidence_history", [])
    
    # Calculate average historical confidence
    all_history = triage_history + investigator_history + decision_history
    if all_history:
        avg_historical = sum(all_history) / len(all_history)
        std_dev = _calculate_std_dev(all_history, avg_historical)
        
        # Check if current confidence is within normal range
        deviation = abs(confidence - avg_historical)
        is_outlier = deviation > (2 * std_dev)  # More than 2 standard deviations
        
        reliability_score = 1.0 - min(1.0, deviation / 0.5)  # Penalize large deviations
        
        result = {
            "reliability_score": round(reliability_score, 2),
            "is_outlier": is_outlier,
            "historical_average": round(avg_historical, 2),
            "deviation": round(deviation, 2),
            "confidence_trend": _calculate_trend(all_history),
            "recommendation": (
                "High reliability - confidence aligns with historical performance"
                if reliability_score > 0.8
                else "Moderate reliability - some deviation from historical performance"
                if reliability_score > 0.6
                else "Low reliability - significant deviation, review carefully"
            )
        }
    else:
        # No historical data
        result = {
            "reliability_score": 0.5,  # Neutral
            "is_outlier": False,
            "historical_average": None,
            "deviation": None,
            "confidence_trend": "insufficient_data",
            "recommendation": "No historical data - treat confidence with caution"
        }
    
    logger.info(
        "[CONFIDENCE CALIBRATOR] Reliability assessment",
        confidence=confidence,
        reliability=result["reliability_score"],
        is_outlier=result["is_outlier"]
    )
    
    return result


def get_confidence_explanation(state: Dict[str, Any]) -> List[str]:
    """
    Generate human-readable explanation of confidence score
    
    Args:
        state: DisputeState dictionary
        
    Returns:
        List of explanation strings
    """
    explanations = []
    
    triage_conf = state.get("triage_confidence", 0.0)
    investigation_conf = state.get("investigation_confidence", 0.0)
    decision_conf = state.get("decision_confidence", 0.0)
    overall_conf = calculate_overall_confidence(state)
    
    # Triage confidence explanation
    if triage_conf >= 0.9:
        explanations.append(f"✓ Very high triage confidence ({triage_conf:.0%}) - dispute category clearly identified")
    elif triage_conf >= 0.7:
        explanations.append(f"✓ Good triage confidence ({triage_conf:.0%}) - dispute category identified with reasonable certainty")
    elif triage_conf >= 0.5:
        explanations.append(f"⚠ Moderate triage confidence ({triage_conf:.0%}) - some ambiguity in dispute category")
    else:
        explanations.append(f"⚠ Low triage confidence ({triage_conf:.0%}) - dispute category uncertain")
    
    # Investigation confidence explanation
    evidence_quality = state.get("evidence_quality_score", 0.0)
    if investigation_conf >= 0.8 and evidence_quality >= 0.8:
        explanations.append(f"✓ Strong investigation ({investigation_conf:.0%}) with high-quality evidence ({evidence_quality:.0%})")
    elif investigation_conf >= 0.6:
        explanations.append(f"✓ Adequate investigation ({investigation_conf:.0%}) with moderate evidence quality ({evidence_quality:.0%})")
    else:
        explanations.append(f"⚠ Weak investigation ({investigation_conf:.0%}) - evidence quality insufficient ({evidence_quality:.0%})")
    
    # Decision confidence explanation
    if decision_conf >= 0.9:
        explanations.append(f"✓ Very high decision confidence ({decision_conf:.0%}) - clear resolution path")
    elif decision_conf >= 0.7:
        explanations.append(f"✓ Good decision confidence ({decision_conf:.0%}) - reasonable certainty in outcome")
    elif decision_conf >= 0.5:
        explanations.append(f"⚠ Moderate decision confidence ({decision_conf:.0%}) - some uncertainty remains")
    else:
        explanations.append(f"⚠ Low decision confidence ({decision_conf:.0%}) - significant uncertainty")
    
    # Overall assessment
    if overall_conf >= 0.85:
        explanations.append(f"✅ OVERALL: High confidence ({overall_conf:.0%}) - reliable automated decision")
    elif overall_conf >= 0.70:
        explanations.append(f"✓ OVERALL: Good confidence ({overall_conf:.0%}) - acceptable for automated processing")
    elif overall_conf >= 0.50:
        explanations.append(f"⚠ OVERALL: Moderate confidence ({overall_conf:.0%}) - consider human review")
    else:
        explanations.append(f"❌ OVERALL: Low confidence ({overall_conf:.0%}) - human review recommended")
    
    return explanations


def _calculate_std_dev(values: List[float], mean: float) -> float:
    """Calculate standard deviation"""
    if not values:
        return 0.0
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return variance ** 0.5


def _calculate_trend(values: List[float]) -> str:
    """Calculate trend direction from historical values"""
    if len(values) < 3:
        return "insufficient_data"
    
    recent = values[-3:]
    if all(recent[i] < recent[i+1] for i in range(len(recent)-1)):
        return "improving"
    elif all(recent[i] > recent[i+1] for i in range(len(recent)-1)):
        return "declining"
    else:
        return "stable"


# Made with Bob - Confidence Calibration System