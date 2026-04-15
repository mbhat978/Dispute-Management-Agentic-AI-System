"""
ReAct-Powered Triage Agent for Banking Dispute Management System

This module contains the LLM-powered triage agent that uses reasoning
to analyze customer queries and categorize disputes intelligently.
Includes a rule-based fallback for when LLM is unavailable.
"""

from typing import Dict, Any
import json
import logging
from datetime import datetime
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from .state import DisputeState
from .config import (
    DISPUTE_CATEGORIES,
    TRIAGE_MODEL,
    TRIAGE_TEMPERATURE,
    OPENAI_API_KEY,
)


logger = logging.getLogger("dispute_management.agents.triage")


def _rule_based_triage_fallback(state: DisputeState) -> Dict[str, Any]:
    """
    Rule-based triage fallback when LLM is unavailable.
    
    This function uses keyword matching to categorize disputes.
    Used as a fallback when OpenAI API is unavailable or fails.
    
    Args:
        state (DisputeState): Current dispute state
        
    Returns:
        Dict with updated dispute_category and audit_trail
    """
    logger.info(
        "[TRIAGE AGENT - RULE BASED FALLBACK] start | ticket_id=%s | customer_id=%s",
        state.get("ticket_id"),
        state.get("customer_id"),
    )
    
    customer_query = state["customer_query"]
    query_lower = customer_query.lower()
    
    # Rule-based categorization using keyword matching
    if any(term in query_lower for term in ["loan", "emi", "interest", "principal", "tenure", "loan account"]):
        category = "loan_dispute"
    elif any(term in query_lower for term in ["refund not received", "refund pending", "refund status", "waiting for refund", "refund delayed"]):
        category = "refund_not_received"
    elif any(term in query_lower for term in ["atm", "cash", "dispense", "debited", "debit"]):
        category = "atm_failure"
    elif any(term in query_lower for term in ["fraud", "unauthorized", "unknown transaction", "didn't make", "did not make", "stolen"]):
        category = "fraud"
    elif any(term in query_lower for term in ["duplicate", "charged twice", "double charge", "multiple charge"]):
        category = "duplicate"
    elif any(term in query_lower for term in ["merchant", "service", "product", "goods", "refund"]):
        category = "merchant_dispute"
    elif any(term in query_lower for term in ["failed", "declined", "error", "not completed", "deducted"]):
        category = "failed_transaction"
    else:
        category = "unknown"
    
    audit_entry = f"Triage Agent (Rule-Based Fallback): Categorized dispute as '{category}' - {DISPUTE_CATEGORIES.get(category, 'Unknown category')}"
    
    logger.info(
        "[TRIAGE AGENT - RULE BASED FALLBACK] result | category=%s",
        category,
    )
    
    return {
        "dispute_category": category,
        "triage_confidence": 0.5,  # Lower confidence for rule-based
        "audit_trail": state["audit_trail"] + [audit_entry]
    }


def triage_node_react(state: DisputeState) -> Dict[str, Any]:
    """
    LLM-Powered Triage Agent: Analyzes customer query with reasoning.
    
    This agent uses an LLM to understand the customer's complaint and
    classify it into one of the predefined dispute categories with
    confidence scoring and detailed reasoning.
    
    Args:
        state (DisputeState): Current dispute state
        
    Returns:
        Dict with updated dispute_category, triage_confidence, and audit_trail
    """
    print(f"\n[TRIAGE AGENT] Analyzing customer query...")
    logger.info(
        "[TRIAGE AGENT - REACT] start | ticket_id=%s | customer_id=%s | query=%s",
        state.get("ticket_id"),
        state.get("customer_id"),
        state.get("customer_query"),
    )
    
    customer_query = state["customer_query"]
    
    # Check if OpenAI API key is available
    if not OPENAI_API_KEY:
        logger.warning("No OpenAI API key found. Falling back to rule-based triage.")
        return _rule_based_triage_fallback(state)
    
    try:
        # Initialize LLM with custom http_client to avoid proxies parameter issue
        import httpx
        http_client = httpx.Client()
        llm = ChatOpenAI(
            model=TRIAGE_MODEL,
            temperature=TRIAGE_TEMPERATURE,
            api_key=SecretStr(OPENAI_API_KEY),
            http_client=http_client
        )
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert banking dispute triage specialist with years of experience in financial services.

Your task is to analyze customer dispute queries and classify them into the correct category.

Available Categories:
{category_descriptions}

Instructions:
1. THINK: Carefully analyze the customer's query, identifying key indicators and patterns
2. REASON: Consider which category best fits based on the evidence in the query
3. CLASSIFY: Select the most appropriate category
4. ASSESS: Evaluate your confidence in this classification (0.0 to 1.0)
5. EXPLAIN: Provide clear reasoning for your decision

Respond ONLY with valid JSON in this exact format:
{{
    "reasoning": "Step-by-step analysis of the query and why you chose this category",
    "category": "selected_category_key",
    "confidence": 0.95,
    "key_indicators": ["indicator1", "indicator2", "indicator3"],
    "alternative_categories": ["category2", "category3"],
    "requires_clarification": false,
    "clarification_questions": []
}}

Important:
- confidence must be a number between 0.0 and 1.0
- category must be one of: {category_keys}
- Be honest about uncertainty - low confidence is better than wrong classification
- If query is ambiguous, set requires_clarification to true and suggest questions"""),
            ("user", "Customer Query: {query}")
        ])
        
        # Format category information
        category_descriptions = "\n".join([
            f"- {key}: {desc}" 
            for key, desc in DISPUTE_CATEGORIES.items()
        ])
        category_keys = ", ".join(DISPUTE_CATEGORIES.keys())
        
        # Invoke LLM
        logger.info("[TRIAGE AGENT - REACT] action=invoke_llm | model=%s", TRIAGE_MODEL)
        response = llm.invoke(prompt.format_messages(
            category_descriptions=category_descriptions,
            category_keys=category_keys,
            query=customer_query
        ))
        
        # Parse response
        try:
            content = response.content if isinstance(response.content, str) else json.dumps(response.content)
            result = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            content = response.content if isinstance(response.content, str) else json.dumps(response.content)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            result = json.loads(content)
        
        # Validate category
        category = result.get("category", "unknown")
        if category not in DISPUTE_CATEGORIES:
            logger.warning("Invalid category '%s' from LLM, defaulting to 'unknown'", category)
            category = "unknown"
            result["confidence"] = 0.3
        
        confidence = float(result.get("confidence", 0.5))
        
        # Build comprehensive audit entry
        audit_entry = f"""Triage Agent (ReAct) - LLM Analysis:

REASONING:
{result.get('reasoning', 'No reasoning provided')}

CLASSIFICATION: {category} ({DISPUTE_CATEGORIES.get(category, 'Unknown')})
CONFIDENCE: {confidence:.2f} ({_confidence_label(confidence)})

KEY INDICATORS:
{chr(10).join(f"  • {ind}" for ind in result.get('key_indicators', []))}

ALTERNATIVE CATEGORIES CONSIDERED:
{chr(10).join(f"  • {alt}" for alt in result.get('alternative_categories', [])) if result.get('alternative_categories') else '  None'}

REQUIRES CLARIFICATION: {result.get('requires_clarification', False)}
{_format_clarification_questions(result.get('clarification_questions', []))}

Model: {TRIAGE_MODEL}
Timestamp: {datetime.utcnow().isoformat()}"""
        
        logger.info(
            "[TRIAGE AGENT - REACT] result | category=%s | confidence=%.2f | indicators=%s",
            category,
            confidence,
            ", ".join(result.get("key_indicators", [])),
        )
        
        print(f"  [SUCCESS] Categorized as: {category.upper()} (Confidence: {confidence:.2f})")
        
        updated_working_memory = dict(state.get("working_memory", {}))
        updated_working_memory.update({
            "triage_reasoning": result.get("reasoning", ""),
            "requires_clarification": result.get("requires_clarification", False),
            "clarification_questions": result.get("clarification_questions", [])
        })

        return {
            "dispute_category": category,
            "triage_confidence": confidence,
            "audit_trail": state["audit_trail"] + [audit_entry],
            "working_memory": updated_working_memory
        }
        
    except Exception as e:
        logger.error("LLM triage failed: %s", str(e), exc_info=True)
        logger.info("[TRIAGE AGENT - REACT] fallback=rule_based")
        
        # Fallback to rule-based triage
        result = _rule_based_triage_fallback(state)
        
        # Add additional context about the fallback
        result["audit_trail"] = result.get("audit_trail", state["audit_trail"]) + [
            f"Note: LLM triage failed ({str(e)}), used rule-based fallback"
        ]

        fallback_working_memory = dict(state.get("working_memory", {}))
        fallback_working_memory.update({
            "triage_reasoning": f"Fallback triage used because LLM failed: {str(e)}",
            "requires_clarification": result.get("dispute_category", "unknown") == "unknown",
            "clarification_questions": []
        })
        result["working_memory"] = fallback_working_memory

        return result


def _confidence_label(confidence: float) -> str:
    """Convert confidence score to human-readable label."""
    if confidence >= 0.9:
        return "Very High"
    elif confidence >= 0.75:
        return "High"
    elif confidence >= 0.6:
        return "Medium"
    elif confidence >= 0.4:
        return "Low"
    else:
        return "Very Low"


def _format_clarification_questions(questions: list) -> str:
    """Format clarification questions for audit trail."""
    if not questions:
        return ""
    
    return "\nCLARIFICATION QUESTIONS:\n" + "\n".join(
        f"  {i+1}. {q}" for i, q in enumerate(questions)
    )


# Made with Bob - ReAct Triage Agent