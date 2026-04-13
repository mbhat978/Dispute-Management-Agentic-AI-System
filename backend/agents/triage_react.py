"""
ReAct-Powered Triage Agent for Banking Dispute Management System

This module contains the LLM-powered triage agent that uses reasoning
to analyze customer queries and categorize disputes intelligently.
"""

from typing import Dict, Any
import json
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
    print("\n[TRIAGE AGENT - REACT] Analyzing customer query with LLM...")
    
    customer_query = state["customer_query"]
    
    # Check if OpenAI API key is available
    if not OPENAI_API_KEY:
        print("  [WARNING] No OpenAI API key found. Falling back to rule-based triage.")
        from .triage import triage_node
        return triage_node(state)
    
    try:
        # Initialize LLM
        llm = ChatOpenAI(
            model=TRIAGE_MODEL,
            temperature=TRIAGE_TEMPERATURE,
            api_key=SecretStr(OPENAI_API_KEY)
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
        print(f"  [LLM] Calling {TRIAGE_MODEL} for classification...")
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
            print(f"  [WARNING] Invalid category '{category}' from LLM, defaulting to 'unknown'")
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
        
        print(f"  [OK] Category: {category} (confidence: {confidence:.2f})")
        print(f"  [OK] Key indicators: {', '.join(result.get('key_indicators', []))}")
        
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
        print(f"  [ERROR] LLM triage failed: {str(e)}")
        print(f"  [FALLBACK] Using rule-based triage...")
        
        # Fallback to rule-based triage
        from .triage import triage_node
        result = triage_node(state)
        
        # Add low confidence since we fell back
        result["triage_confidence"] = 0.5
        result["audit_trail"] = result.get("audit_trail", state["audit_trail"]) + [
            f"Triage Agent: LLM failed ({str(e)}), used rule-based fallback with confidence 0.5"
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