"""
Vision Expert Agent for Banking Dispute Management System

This specialist agent analyzes visual evidence (receipts, emails, screenshots)
using GPT-4o Vision when evidence_base64 is available in the state.
"""

from typing import Dict, Any, Optional
from loguru import logger
from datetime import datetime
import json

try:
    from .state import DisputeState
    from .config import OPENAI_API_KEY
except ImportError:
    from agents.state import DisputeState
    from agents.config import OPENAI_API_KEY

from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage


def vision_node(state: DisputeState) -> Dict[str, Any]:
    """
    Vision Expert Agent: Analyzes visual evidence using GPT-4o Vision.
    
    This agent checks for evidence_base64 in additional_context or receipt_image_base64
    in the state. If found, it uses GPT-4o Vision to:
    - Extract timeline information from refund receipts/emails
    - Analyze receipt amounts for incorrect_amount disputes
    - Extract merchant information and transaction details
    
    Args:
        state: The current dispute state
        
    Returns:
        Dict with vision_analysis results and updated audit_trail
    """
    ticket_id = state["ticket_id"]
    category = state["dispute_category"]
    audit_trail = list(state["audit_trail"])
    vision_analysis: Dict[str, Any] = {}
    
    logger.info(
        f"[VISION EXPERT AGENT] start | ticket_id={ticket_id} | category={category}"
    )
    
    # Check for visual evidence
    receipt_image_base64 = state.get("receipt_image_base64")
    additional_context = state.get("working_memory", {}).get("additional_context", {})
    evidence_base64 = additional_context.get("evidence_base64") if additional_context else None
    
    # Determine which evidence to use
    visual_evidence = receipt_image_base64 or evidence_base64
    
    if not visual_evidence:
        logger.info("[VISION EXPERT AGENT] No visual evidence found - skipping analysis")
        audit_trail.append(
            "Vision Expert Agent: No visual evidence available for analysis"
        )
        return {
            "vision_analysis": vision_analysis,
            "audit_trail": audit_trail
        }
    
    audit_trail.append(
        f"Vision Expert Agent THOUGHT: Visual evidence detected for category '{category}'. "
        "Will analyze using GPT-4o Vision."
    )
    
    try:
        # Determine analysis type based on category
        if category == "refund_not_received":
            logger.info("[VISION EXPERT AGENT] Action: Analyzing refund timeline from evidence")
            audit_trail.append(
                "Vision Expert Agent ACTION: Analyzing refund timeline using GPT-4o Vision"
            )
            
            result = _analyze_refund_timeline(visual_evidence, state)
            vision_analysis["refund_timeline_analysis"] = result
            
            logger.info(
                f"[VISION EXPERT AGENT] Observation: Timeline extracted - "
                f"return_date={result.get('return_date_extracted', 'N/A')}, "
                f"days_elapsed={result.get('days_elapsed', 'N/A')}"
            )
            audit_trail.append(
                f"Vision Expert Agent OBSERVATION: analyze_refund_timeline output: {str(result)}"
            )
            
        elif category == "incorrect_amount":
            logger.info("[VISION EXPERT AGENT] Action: Analyzing receipt for amount verification")
            audit_trail.append(
                "Vision Expert Agent ACTION: Analyzing receipt amount using GPT-4o Vision"
            )
            
            result = _analyze_receipt_amount(visual_evidence, state)
            vision_analysis["receipt_analysis"] = result
            
            logger.info(
                f"[VISION EXPERT AGENT] Observation: Receipt analyzed - "
                f"extracted_amount={result.get('extracted_amount', 'N/A')}, "
                f"merchant={result.get('extracted_merchant', 'N/A')}"
            )
            audit_trail.append(
                f"Vision Expert Agent OBSERVATION: analyze_receipt_amount output: {str(result)}"
            )
            
        else:
            # Generic visual evidence analysis
            logger.info("[VISION EXPERT AGENT] Action: Performing generic visual analysis")
            audit_trail.append(
                "Vision Expert Agent ACTION: Analyzing visual evidence using GPT-4o Vision"
            )
            
            result = _analyze_generic_evidence(visual_evidence, category)
            vision_analysis["generic_analysis"] = result
            
            logger.info(
                f"[VISION EXPERT AGENT] Observation: Evidence analyzed - "
                f"type={result.get('evidence_type', 'N/A')}"
            )
            audit_trail.append(
                f"Vision Expert Agent OBSERVATION: analyze_generic_evidence output: {str(result)}"
            )
        
        vision_analysis["timestamp"] = datetime.utcnow().isoformat()
        vision_analysis["evidence_source"] = "receipt_image_base64" if receipt_image_base64 else "additional_context"
        
        logger.success(
            f"[VISION EXPERT AGENT] complete | analysis_type="
            f"{list(vision_analysis.keys())[0] if vision_analysis else 'none'}"
        )
        
        return {
            "vision_analysis": vision_analysis,
            "audit_trail": audit_trail
        }
        
    except Exception as e:
        logger.exception(f"Error during vision analysis: {str(e)}")
        audit_trail.append(f"Vision Expert Agent ERROR: {str(e)}")
        return {
            "vision_analysis": {"error": str(e)},
            "audit_trail": audit_trail
        }


def _analyze_refund_timeline(
    evidence_base64: str,
    state: DisputeState
) -> Dict[str, Any]:
    """
    Analyze refund timeline from return receipt or email evidence.
    
    Args:
        evidence_base64: Base64-encoded image
        state: Current dispute state
        
    Returns:
        Timeline analysis result
    """
    try:
        # Prepare image URL
        image_url = evidence_base64
        if not image_url.startswith("data:image"):
            image_url = f"data:image/jpeg;base64,{evidence_base64}"
        
        # Initialize GPT-4o Vision
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            api_key=SecretStr(OPENAI_API_KEY) if OPENAI_API_KEY else None
        )
        
        prompt_text = """
        You are a forensic financial AI. Analyze this return receipt, cancellation email, or support ticket screenshot.
        Extract the exact DATE when the customer returned the item or cancelled the service.
        
        You MUST return ONLY a valid JSON object.
        Use this exact JSON schema:
        {
            "extracted_return_date": "YYYY-MM-DD",
            "is_valid_proof": boolean,
            "note": "brief explanation of what you found"
        }
        """
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        )
        
        response = llm.invoke([message])
        content_str = str(response.content) if not isinstance(response.content, str) else response.content
        cleaned_content = content_str.replace("```json", "").replace("```", "").strip()
        parsed_json = json.loads(cleaned_content)
        
        return_date_str = parsed_json.get("extracted_return_date")
        is_valid = parsed_json.get("is_valid_proof", False)
        
        # Calculate days elapsed
        current_time = datetime.now()
        days_elapsed = 0
        
        if return_date_str and is_valid:
            try:
                return_date = datetime.strptime(return_date_str, "%Y-%m-%d")
                days_elapsed = (current_time - return_date).days
            except ValueError:
                pass
        
        # Determine refund stage
        if days_elapsed <= 3:
            stage = "merchant_review"
        elif days_elapsed <= 7:
            stage = "merchant_escalation"
        elif days_elapsed <= 14:
            stage = "bank_investigation"
        else:
            stage = "provisional_credit"
        
        transaction_details = state.get("gathered_data", {}).get("transaction_details", {})
        
        return {
            "transaction_id": transaction_details.get("transaction_id"),
            "return_date_extracted": return_date_str,
            "is_valid_proof": is_valid,
            "days_elapsed": days_elapsed,
            "refund_stage": stage,
            "vision_notes": parsed_json.get("note", "")
        }
        
    except Exception as e:
        logger.error(f"[VISION EXPERT AGENT] Timeline analysis failed: {str(e)}")
        return {
            "error": f"Timeline analysis failed: {str(e)}",
            "is_valid_proof": False
        }


def _analyze_receipt_amount(
    receipt_base64: str,
    state: DisputeState
) -> Dict[str, Any]:
    """
    Analyze receipt to extract and verify transaction amount.
    
    Args:
        receipt_base64: Base64-encoded receipt image
        state: Current dispute state
        
    Returns:
        Receipt analysis result
    """
    try:
        # Prepare image URL
        image_url = receipt_base64
        if not image_url.startswith("data:image"):
            image_url = f"data:image/jpeg;base64,{receipt_base64}"
        
        # Get expected merchant from transaction details
        transaction_details = state.get("gathered_data", {}).get("transaction_details", {})
        expected_merchant = transaction_details.get("merchant_name", "")
        ledger_amount = transaction_details.get("amount", 0)
        
        # Initialize GPT-4o Vision
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            api_key=SecretStr(OPENAI_API_KEY) if OPENAI_API_KEY else None
        )
        
        prompt_text = f"""
        You are a forensic financial AI. Analyze this receipt image.
        Extract the merchant name and the total charged amount.
        
        Expected merchant: {expected_merchant}
        Ledger amount: ${ledger_amount}
        
        You MUST return ONLY a valid JSON object.
        Use this exact JSON schema:
        {{
            "extracted_merchant": "merchant name from receipt",
            "extracted_amount": float (numeric value only),
            "merchant_matches": boolean,
            "amount_matches": boolean,
            "note": "brief explanation"
        }}
        """
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        )
        
        response = llm.invoke([message])
        content_str = str(response.content) if not isinstance(response.content, str) else response.content
        cleaned_content = content_str.replace("```json", "").replace("```", "").strip()
        parsed_json = json.loads(cleaned_content)
        
        return {
            "transaction_id": transaction_details.get("transaction_id"),
            "expected_merchant": expected_merchant,
            "ledger_amount": ledger_amount,
            "extracted_merchant": parsed_json.get("extracted_merchant", ""),
            "extracted_amount": parsed_json.get("extracted_amount", 0),
            "merchant_matches": parsed_json.get("merchant_matches", False),
            "amount_matches": parsed_json.get("amount_matches", False),
            "vision_notes": parsed_json.get("note", "")
        }
        
    except Exception as e:
        logger.error(f"[VISION EXPERT AGENT] Receipt analysis failed: {str(e)}")
        return {
            "error": f"Receipt analysis failed: {str(e)}",
            "amount_matches": False
        }


def _analyze_generic_evidence(
    evidence_base64: str,
    category: str
) -> Dict[str, Any]:
    """
    Perform generic visual evidence analysis.
    
    Args:
        evidence_base64: Base64-encoded image
        category: Dispute category
        
    Returns:
        Generic analysis result
    """
    try:
        # Prepare image URL
        image_url = evidence_base64
        if not image_url.startswith("data:image"):
            image_url = f"data:image/jpeg;base64,{evidence_base64}"
        
        # Initialize GPT-4o Vision
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            api_key=SecretStr(OPENAI_API_KEY) if OPENAI_API_KEY else None
        )
        
        prompt_text = f"""
        You are a forensic financial AI. Analyze this evidence image for a {category} dispute.
        Extract any relevant information that could help resolve the dispute.
        
        You MUST return ONLY a valid JSON object.
        Use this exact JSON schema:
        {{
            "evidence_type": "receipt/email/screenshot/other",
            "key_findings": ["finding1", "finding2"],
            "supports_customer_claim": boolean,
            "note": "detailed explanation"
        }}
        """
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        )
        
        response = llm.invoke([message])
        content_str = str(response.content) if not isinstance(response.content, str) else response.content
        cleaned_content = content_str.replace("```json", "").replace("```", "").strip()
        parsed_json = json.loads(cleaned_content)
        
        return {
            "category": category,
            "evidence_type": parsed_json.get("evidence_type", "unknown"),
            "key_findings": parsed_json.get("key_findings", []),
            "supports_customer_claim": parsed_json.get("supports_customer_claim", False),
            "vision_notes": parsed_json.get("note", "")
        }
        
    except Exception as e:
        logger.error(f"[VISION EXPERT AGENT] Generic analysis failed: {str(e)}")
        return {
            "error": f"Generic analysis failed: {str(e)}",
            "evidence_type": "unknown"
        }


# Made with Bob