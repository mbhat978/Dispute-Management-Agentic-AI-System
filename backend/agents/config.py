"""
Configuration for ReAct-driven Multi-Agent System

This module contains configuration settings for LLM models, API keys,
and agent behavior parameters.
"""

import os
from typing import Literal, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# LLM CONFIGURATION
# ============================================================================

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Model selection based on task complexity
MODEL_GPT4 = "gpt-4o" #"gpt-4"
MODEL_GPT35 = "gpt-3.5-turbo" #"gpt-3.5-turbo"
MODEL_GPT4_TURBO: Any = "gpt-4o" #"gpt-4-turbo-preview"

# Default models for each agent
TRIAGE_MODEL = MODEL_GPT35  # Simple classification task
INVESTIGATOR_MODEL = MODEL_GPT4  # Complex reasoning and tool selection
DECISION_MODEL = MODEL_GPT4  # Critical decision making
ORCHESTRATOR_MODEL = MODEL_GPT35  # Simple routing decisions

# Temperature settings (0 = deterministic, 1 = creative)
TEMPERATURE_DETERMINISTIC = 0.0
TEMPERATURE_BALANCED = 0.3
TEMPERATURE_CREATIVE = 0.7

# Default temperature for agents
TRIAGE_TEMPERATURE = TEMPERATURE_DETERMINISTIC
INVESTIGATOR_TEMPERATURE = TEMPERATURE_BALANCED
DECISION_TEMPERATURE = TEMPERATURE_DETERMINISTIC

# ============================================================================
# AGENT BEHAVIOR CONFIGURATION
# ============================================================================

# Maximum iterations for ReAct loops
MAX_INVESTIGATION_ITERATIONS = 10
MAX_WORKFLOW_ITERATIONS = 3

# Confidence thresholds for routing decisions
CONFIDENCE_THRESHOLD_HIGH = 0.8
CONFIDENCE_THRESHOLD_MEDIUM = 0.6
CONFIDENCE_THRESHOLD_LOW = 0.4

# Escalation thresholds
ESCALATION_AMOUNT_THRESHOLD = 5000.0  # High-value disputes
ESCALATION_CONFIDENCE_THRESHOLD = 0.7  # Low confidence requires human review

# ============================================================================
# COST OPTIMIZATION
# ============================================================================

# Enable caching for repeated queries
ENABLE_CACHING = True
CACHE_TTL_SECONDS = 3600  # 1 hour

# Use cheaper models for simple cases
ENABLE_DYNAMIC_MODEL_SELECTION = True

# Amount thresholds for model selection
SIMPLE_CASE_AMOUNT_THRESHOLD = 1000.0  # Use GPT-3.5 for < $1000
COMPLEX_CASE_AMOUNT_THRESHOLD = 5000.0  # Use GPT-4 for > $5000

# ============================================================================
# DISPUTE CATEGORIES
# ============================================================================

DISPUTE_CATEGORIES = {
    "fraud": "Fraudulent or unauthorized transaction",
    "duplicate": "Duplicate charge or multiple identical transactions",
    "atm_failure": "ATM did not dispense cash but amount was debited",
    "merchant_dispute": "Dispute with merchant about goods/services",
    "failed_transaction": "Transaction failed but amount was deducted",
    "loan_dispute": "Dispute related to loan account or EMI",
    "refund_not_received": "Refund not received from merchant",
    "unknown": "Category not yet determined"
}

# ============================================================================
# BUSINESS RULES (Non-negotiable compliance rules)
# ============================================================================

# Categories that MUST go to human review (compliance requirement)
MANDATORY_HUMAN_REVIEW_CATEGORIES = ["loan_dispute"]

# Amount threshold for mandatory human review
MANDATORY_HUMAN_REVIEW_AMOUNT = 10000.0

# VIP customer tiers requiring higher scrutiny
VIP_TIERS = ["Gold", "Platinum"]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def select_model_by_complexity(
    category: str,
    amount: float,
    customer_tier: str = "Basic",
    agent_type: str = "general"
) -> str:
    """
    Select appropriate LLM model based on case complexity and agent type.
    
    This function implements intelligent cost optimization by choosing the right
    model for the right task. Uses GPT-4 for complex/high-value cases and
    GPT-3.5-turbo for simpler cases.
    
    Args:
        category: Dispute category
        amount: Transaction amount
        customer_tier: Customer account tier
        agent_type: Type of agent (triage, investigator, decision)
        
    Returns:
        Model name to use
        
    Cost Optimization Strategy:
    - Triage: Always GPT-3.5 (simple classification)
    - Investigator: GPT-4 for complex, GPT-3.5 for simple
    - Decision: GPT-4 for high-stakes, GPT-3.5 for clear cases
    """
    if not ENABLE_DYNAMIC_MODEL_SELECTION:
        return MODEL_GPT4
    
    # Triage agent: Always use GPT-3.5 (simple classification task)
    if agent_type == "triage":
        return MODEL_GPT35
    
    # High-value disputes (>$5000) → GPT-4 for all agents
    if amount > COMPLEX_CASE_AMOUNT_THRESHOLD:
        return MODEL_GPT4
    
    # VIP customers → GPT-4 for quality service
    if customer_tier in VIP_TIERS:
        return MODEL_GPT4
    
    # Complex categories → GPT-4 for investigator and decision
    if category in ["fraud", "loan_dispute"] and agent_type in ["investigator", "decision"]:
        return MODEL_GPT4
    
    # Simple cases (<$1000) → GPT-3.5 for cost efficiency
    if amount < SIMPLE_CASE_AMOUNT_THRESHOLD:
        return MODEL_GPT35
    
    # Medium complexity cases
    if agent_type == "investigator":
        # Investigator needs reasoning power
        return MODEL_GPT4
    elif agent_type == "decision":
        # Decision agent needs accuracy
        return MODEL_GPT4
    
    # Default to GPT-3.5 for cost efficiency
    return MODEL_GPT35


def estimate_processing_cost(
    category: str,
    amount: float,
    customer_tier: str = "Basic"
) -> Dict[str, Any]:
    """
    Estimate the LLM API cost for processing a dispute.
    
    Args:
        category: Dispute category
        amount: Transaction amount
        customer_tier: Customer account tier
        
    Returns:
        Dict with cost estimates and model selections
    """
    triage_model = select_model_by_complexity(category, amount, customer_tier, "triage")
    investigator_model = select_model_by_complexity(category, amount, customer_tier, "investigator")
    decision_model = select_model_by_complexity(category, amount, customer_tier, "decision")
    
    # Approximate costs per 1K tokens (as of 2024)
    costs = {
        MODEL_GPT35: 0.002,  # $0.002 per 1K tokens
        MODEL_GPT4: 0.03,    # $0.03 per 1K tokens
    }
    
    # Estimate tokens per agent (rough averages)
    triage_tokens = 500
    investigator_tokens = 1500
    decision_tokens = 1000
    
    triage_cost = (triage_tokens / 1000) * costs.get(triage_model, 0.002)
    investigator_cost = (investigator_tokens / 1000) * costs.get(investigator_model, 0.03)
    decision_cost = (decision_tokens / 1000) * costs.get(decision_model, 0.03)
    
    total_cost = triage_cost + investigator_cost + decision_cost
    
    return {
        "models": {
            "triage": triage_model,
            "investigator": investigator_model,
            "decision": decision_model
        },
        "estimated_costs": {
            "triage": round(triage_cost, 4),
            "investigator": round(investigator_cost, 4),
            "decision": round(decision_cost, 4),
            "total": round(total_cost, 4)
        },
        "cost_category": "low" if total_cost < 0.05 else "medium" if total_cost < 0.15 else "high"
    }


def should_escalate_to_human(
    category: str,
    amount: float,
    confidence: float,
    customer_tier: str = "Basic"
) -> tuple[bool, str]:
    """
    Determine if case should be escalated to human review.
    
    Args:
        category: Dispute category
        amount: Transaction amount
        confidence: Decision confidence score
        customer_tier: Customer account tier
        
    Returns:
        Tuple of (should_escalate, reason)
    """
    # Mandatory escalation for compliance
    if category in MANDATORY_HUMAN_REVIEW_CATEGORIES:
        return True, f"Compliance requirement: {category} must be reviewed by human"
    
    # High-value disputes
    if amount > MANDATORY_HUMAN_REVIEW_AMOUNT:
        return True, f"High-value dispute (${amount:,.2f}) requires human review"
    
    # Low confidence
    if confidence < ESCALATION_CONFIDENCE_THRESHOLD:
        return True, f"Low confidence ({confidence:.2f}) requires human verification"
    
    # VIP customers with medium confidence
    if customer_tier in VIP_TIERS and confidence < CONFIDENCE_THRESHOLD_HIGH:
        return True, f"VIP customer ({customer_tier}) requires higher confidence threshold"
    
    return False, ""


def get_human_review_priority(
    category: str,
    amount: float,
    customer_tier: str = "Basic"
) -> Literal["low", "medium", "high", "urgent"]:
    """
    Determine priority level for human review queue.
    
    Args:
        category: Dispute category
        amount: Transaction amount
        customer_tier: Customer account tier
        
    Returns:
        Priority level
    """
    # Urgent: High-value VIP customers
    if amount > 20000 and customer_tier in VIP_TIERS:
        return "urgent"
    
    # High: High-value or VIP
    if amount > MANDATORY_HUMAN_REVIEW_AMOUNT or customer_tier in VIP_TIERS:
        return "high"
    
    # Medium: Moderate value or complex category
    if amount > 5000 or category in ["fraud", "loan_dispute"]:
        return "medium"
    
    # Low: Everything else
    return "low"


# Made with Bob - ReAct Configuration