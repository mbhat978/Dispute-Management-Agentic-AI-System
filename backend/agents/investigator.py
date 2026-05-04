"""
Investigator Agent for Banking Dispute Management System

This module contains the investigator agent that gathers evidence using a
dynamic ReAct-style tool plan with optional LLM guidance and rule-based fallback.
"""

from typing import Dict, Any, List, Tuple, Optional
import json
from loguru import logger
from datetime import datetime
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from .. import mcp_client as banking_tools
    from .. import models
    from ..database import SessionLocal
    from .state import DisputeState
    from .config import OPENAI_API_KEY, INVESTIGATOR_MODEL, INVESTIGATOR_TEMPERATURE
except ImportError:
    import mcp_client as banking_tools
    import models
    from database import SessionLocal
    from agents.state import DisputeState
    from agents.config import OPENAI_API_KEY, INVESTIGATOR_MODEL, INVESTIGATOR_TEMPERATURE


def investigator_node(state: DisputeState) -> Dict[str, Any]:
    """
    Supervisor Agent: Dynamically plans the execution path for worker agents.
    
    This lightweight supervisor analyzes the dispute and determines which specialist
    agents (workers) need to be activated based on the dispute category and context.
    """
    from loguru import logger
    
    category = state.get("dispute_category", "unknown")
    working_memory = state.get("working_memory", {})
    receipt_image = state.get("receipt_image_base64")
    
    logger.info(f"[SUPERVISOR AGENT] Analyzing ticket {state.get('ticket_id')} for dynamic routing...")
    
    # Start with an empty plan - data_retrieval is handled separately in the graph
    plan = []
    
    # Conditionally wake up the Fraud Analyst
    if category in ["fraud", "fraudulent_transaction", "unauthorized_transaction"]:
        logger.info("[SUPERVISOR AGENT] Fraud detected. Waking up Fraud Analyst.")
        plan.append("fraud_analyst")
        
    # Conditionally wake up the Vision Expert
    if receipt_image or working_memory.get("has_receipt_evidence"):
        logger.info("[SUPERVISOR AGENT] Image evidence detected. Waking up Vision Forensics.")
        plan.append("vision_expert")
        
    logger.info(f"[SUPERVISOR AGENT] Final Routing Plan: {plan}")
    
    return {"routing_plan": plan}


def _build_investigation_plan(
    category: str,
    customer_id: int,
    transaction_id: int,
    customer_query: str,
    working_memory: Dict[str, Any],
    prior_gathered_data: Dict[str, Any],
    receipt_image_base64: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Build a dynamic investigation plan using LLM-powered reasoning.
    
    This function uses an LLM to intelligently plan which tools to use based on:
    - Dispute category and customer query
    - Previously gathered data
    - Working memory context
    
    The LLM provides reasoning for each tool selection, creating a true ReAct
    investigation strategy that adapts to the specific case.
    """
    fallback_plan = _rule_based_plan(category, customer_id, transaction_id, prior_gathered_data)

    if not OPENAI_API_KEY:
        logger.info("No OpenAI API key, using rule-based planning")
        return fallback_plan, "rule_based_fallback"

    try:
        # Initialize LLM with custom http_client to avoid proxies parameter issue
        import httpx
        http_client = httpx.Client()
        llm = ChatOpenAI(
            model=INVESTIGATOR_MODEL,
            temperature=INVESTIGATOR_TEMPERATURE,
            api_key=SecretStr(OPENAI_API_KEY),
            http_client=http_client
        )
        
        # Enhanced prompt with reasoning requirements
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert banking dispute investigator with deep knowledge of fraud detection, transaction analysis, and evidence gathering.

Your task is to create an intelligent investigation plan by reasoning about which tools to use and why.

AVAILABLE TOOLS:
1. get_transaction_details - Retrieves full transaction info (amount, merchant, date, status, international flag)
   Use when: Need basic transaction information (ALWAYS use first if not already gathered)
   
2. get_customer_history - Gets last 5 transactions for pattern analysis
   Use when: Fraud suspected, need to verify spending patterns, check for anomalies
   
3. **calculate_fraud_risk_score** - **CRITICAL FOR FRAUD DISPUTES** - Calculates 0-100 fraud risk score using 5-factor analysis
   Use when: Category is 'fraud' or 'fraudulent_transaction' (MANDATORY - MUST ALWAYS USE)
   Analyzes: velocity, amount anomaly, geographic risk, time risk, merchant risk
   Input: {{"transaction_id": <id>, "customer_id": <id>}}
   
4. **detect_dispute_fraud** - **CRITICAL FOR FRAUD DISPUTES** - Detects "friendly fraud" patterns
   Use when: Category is 'fraud' or 'fraudulent_transaction' (MANDATORY - MUST ALWAYS USE)
   Checks: excessive disputes, rapid succession, pattern matching, customer propensity score
   Input: {{"customer_id": <id>}}
   
5. check_atm_logs - Queries ATM machine logs for hardware faults
   Use when: ATM dispute, need to verify if cash was dispensed or hardware fault occurred
   
6. check_duplicate_transactions - Searches for duplicate charges in time window
   Use when: Duplicate charge suspected, need to find matching transactions
   
7. get_loan_details - Retrieves loan EMI schedule and outstanding balance
   Use when: Loan/EMI dispute, need loan account information
   
8. check_merchant_refund_status - Checks if merchant initiated refund
   Use when: Refund not received, need to verify merchant/gateway status
   
9. verify_receipt_amount - Verifies customer claimed receipt amount against the ledger
   Use when: 'incorrect_amount' dispute. You MUST extract the customer's claimed/expected amount from their query and pass it as a float in 'claimed_amount' in the input.
   
11. analyze_receipt_evidence - Analyzes a Base64 receipt image using Vision OCR to extract merchant name and charged amount
    Use when: Customer claims 'incorrect_amount' AND a receipt image is available (receipt_image_base64 exists in state).
    CRITICAL: If the customer claims an incorrect amount and the state contains receipt_image_base64, you MUST use this tool to extract the printed amount and compare it against the ledger amount before making a recommendation.
    Input: {{"receipt_base64": "<base64_string>", "expected_merchant": "<merchant_name>"}}

12. get_delivery_tracking_status - Retrieves delivery status from carrier (e.g., FedEx, UPS)
    Use when: 'merchant_dispute' (Item not delivered, lost in transit).
    Input: {{"transaction_id": <id>}}
    
13. check_subscription_status - Checks if a customer has an active subscription with a merchant
    Use when: Unrecognized charge from a known subscription service (e.g., Netflix, Spotify).
    Input: {{"customer_id": <id>, "merchant_name": "<merchant>"}}
    
14. verify_subscription_cancellation - Checks if a customer previously cancelled a subscription
    Use when: Customer claims they cancelled a subscription but were still charged.
    Input: {{"customer_id": <id>, "merchant_name": "<merchant>", "cancellation_date": "YYYY-MM-DD"}}
    Note: Extract cancellation_date from customer query if mentioned, otherwise system will use a default.
    
15. get_refund_timeline - Retrieves the expected timeline for a merchant refund
    Use when: 'refund_not_received' (Customer expects a refund that hasn't posted yet).
    Input: {{"transaction_id": <id>}}
    
16. check_merchant_reputation_score - Retrieves a trust score (0-100) for a merchant
    Use when: 'merchant_dispute' to verify if the merchant is generally trustworthy or suspicious.
    Input: {{"merchant_name": "<merchant>"}}
    
17. get_merchant_dispute_history - Checks how many recent disputes a merchant has had
    Use when: 'merchant_dispute' to see if there is a pattern of similar complaints against them.
    Input: {{"merchant_name": "<merchant>"}}

18. calculate_timeline_from_evidence - Calculates refund timeline from uploaded receipt/email evidence
    Use when: 'refund_not_received' AND customer uploaded evidence (receipt_image_base64 exists in state).
    Input: {{"evidence_base64": "<base64_string>", "transaction_id": <id>}}

INVESTIGATION STRATEGY:
- Start with transaction_details if not already available
- **MANDATORY FOR FRAUD**: If category is 'fraud' or 'fraudulent_transaction', you MUST include both calculate_fraud_risk_score AND detect_dispute_fraud in your plan
- Choose tools that directly address the dispute category
- Consider customer query for additional context clues
- Avoid redundant tool calls (check prior_data_keys)
- Plan 2-5 tools maximum for efficiency
- IMPORTANT: If receipt_image_base64 is present in the state and the dispute is about incorrect_amount, you MUST include analyze_receipt_evidence in your plan

PLANNING RULES:
    - IF CATEGORY IS 'refund_not_received':
      MANDATORY: Use `get_transaction_details` and `check_merchant_refund_status`.
      IF the customer uploaded evidence (receipt/email): Use `calculate_timeline_from_evidence`.
      ELSE: Use `get_refund_timeline`.

Return ONLY valid JSON:
{{
  "reasoning": "Step-by-step explanation of your investigation strategy and why each tool is needed",
  "steps": [
    {{
      "tool": "tool_name",
      "data_key": "storage_key",
      "input": {{"key": "value"}},
      "rationale": "Why this specific tool is needed for this case"
    }}
  ],
  "expected_evidence": ["evidence1", "evidence2"],
  "confidence": 0.0-1.0
}}"""),
            ("user", """Analyze this dispute and create an investigation plan:

DISPUTE DETAILS:
- Category: {category}
- Customer Query: "{query}"
- Customer ID: {customer_id}
- Transaction ID: {transaction_id}

CONTEXT:
- Already Gathered Data: {prior_keys}
- Working Memory: {working_memory}
- Receipt Image Available: {receipt_available}

Create an intelligent investigation plan with reasoning:""")
        ])

        logger.debug(f"[INVESTIGATOR AGENT] action=invoke_llm_planner | model={INVESTIGATOR_MODEL}")
        response = llm.invoke(prompt.format_messages(
            category=category,
            customer_id=customer_id,
            transaction_id=transaction_id,
            query=customer_query,
            working_memory=json.dumps(working_memory, default=str),
            prior_keys=list(prior_gathered_data.keys()) if prior_gathered_data else ["none"],
            receipt_available="Yes" if receipt_image_base64 else "No",
        ))

        content = response.content if isinstance(response.content, str) else json.dumps(response.content)
        content = content.strip()
        
        # Extract JSON from markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        parsed = json.loads(content)
        steps = parsed.get("steps", [])
        reasoning = parsed.get("reasoning", "No reasoning provided")
        expected_evidence = parsed.get("expected_evidence", [])
        plan_confidence = parsed.get("confidence", 0.8)
        
        logger.info(f"[INVESTIGATOR AGENT] llm_plan_reasoning={reasoning[:100]}...")
        logger.info(f"[INVESTIGATOR AGENT] llm_planned_steps={len(steps)}")
        
        # Sanitize and validate the plan
        sanitized = _sanitize_plan(steps, customer_id, transaction_id, prior_gathered_data, receipt_image_base64)
        
        if sanitized:
            logger.info(f"Using LLM investigation plan with {len(sanitized)} steps")
            return sanitized, "llm_planner"
        else:
            logger.warning("LLM plan validation failed, using fallback")
            return fallback_plan, "llm_planner_failed_validation"

    except json.JSONDecodeError as e:
        logger.exception(f"Failed to parse LLM response: {str(e)}")
        return fallback_plan, "llm_planner_json_error"
    except Exception as e:
        logger.exception(f"LLM planning failed: {str(e)}")
        return fallback_plan, "llm_planner_error"


def _rule_based_plan(
    category: str,
    customer_id: int,
    transaction_id: int,
    prior_gathered_data: Dict[str, Any],
) -> List[Dict[str, Any]]:
    plan: List[Dict[str, Any]] = []

    if "transaction_details" not in prior_gathered_data:
        plan.append({
            "tool": "get_transaction_details",
            "data_key": "transaction_details",
            "input": {"transaction_id": transaction_id},
        })

    if category == "fraud" or category == "fraudulent_transaction":
        # MANDATORY: Fraud scorer for quantitative risk assessment
        plan.append({
            "tool": "calculate_fraud_risk_score",
            "data_key": "fraud_risk_score",
            "input": {"transaction_id": transaction_id, "customer_id": customer_id},
        })
        # MANDATORY: Dispute fraud detector to check for friendly fraud
        plan.append({
            "tool": "detect_dispute_fraud",
            "data_key": "dispute_fraud_analysis",
            "input": {"customer_id": customer_id},
        })
        # Customer history for context
        plan.append({
            "tool": "get_customer_history",
            "data_key": "customer_history",
            "input": {"customer_id": customer_id, "limit": 5},
        })
    elif category == "duplicate":
        plan.append({
            "tool": "check_duplicate_transactions",
            "data_key": "duplicate_check",
            "input": {"customer_id": customer_id},
        })
    elif category == "atm_failure":
        plan.append({
            "tool": "check_atm_logs",
            "data_key": "atm_logs",
            "input": {"transaction_id": transaction_id},
        })
    elif category == "loan_dispute":
        plan.append({
            "tool": "get_loan_details",
            "data_key": "loan_details",
            "input": {"customer_id": customer_id},
        })
    elif category == "refund_not_received":
        plan.append({
            "tool": "check_merchant_refund_status",
            "data_key": "refund_status",
            "input": {"transaction_id": transaction_id},
        })
    elif category == "incorrect_amount":
        plan.append({
            "tool": "verify_receipt_amount",
            "data_key": "receipt_verification",
            "input": {"transaction_id": transaction_id, "claimed_amount": 0.0},
        })
    return plan


def _sanitize_plan(
    steps: List[Dict[str, Any]],
    customer_id: int,
    transaction_id: int,
    prior_gathered_data: Dict[str, Any],
    receipt_image_base64: Optional[str] = None,
) -> List[Dict[str, Any]]:
    allowed = {
        "get_transaction_details": "transaction_details",
        "get_customer_history": "customer_history",
        "check_atm_logs": "atm_logs",
        "check_duplicate_transactions": "duplicate_check",
        "get_loan_details": "loan_details",
        "check_merchant_refund_status": "refund_status",
        "verify_receipt_amount": "receipt_verification",
        "analyze_receipt_evidence": "receipt_analysis",
        "calculate_fraud_risk_score": "fraud_risk_score",
        "detect_dispute_fraud": "dispute_fraud_analysis",
        "get_delivery_tracking_status": "delivery_status",
        "check_subscription_status": "subscription_status",
        "verify_subscription_cancellation": "cancellation_status",
        "get_refund_timeline": "refund_timeline",
        "check_merchant_reputation_score": "merchant_reputation",
        "get_merchant_dispute_history": "merchant_dispute_history",
        "calculate_timeline_from_evidence": "timeline_from_evidence",
    }

    sanitized: List[Dict[str, Any]] = []
    for step in steps:
        tool_name = step.get("tool")
        if tool_name not in allowed:
            continue

        data_key = allowed[tool_name]  # Force strict internal keys, ignore LLM
        tool_input = step.get("input", {})

        if tool_name == "get_transaction_details":
            tool_input = {"transaction_id": transaction_id}
        elif tool_name == "get_customer_history":
            tool_input = {"customer_id": customer_id, "limit": tool_input.get("limit", 5)}
        elif tool_name == "check_atm_logs":
            tool_input = {"transaction_id": transaction_id}
        elif tool_name == "get_loan_details":
            tool_input = {"customer_id": customer_id}
        elif tool_name == "check_merchant_refund_status":
            tool_input = {"transaction_id": transaction_id}
        elif tool_name == "check_duplicate_transactions":
            tool_input = {"customer_id": customer_id, "transaction_id": transaction_id}
        elif tool_name == "verify_receipt_amount":
            tool_input = {"transaction_id": transaction_id, "claimed_amount": tool_input.get("claimed_amount", 0.0)}
        elif tool_name == "calculate_fraud_risk_score":
            tool_input = {"transaction_id": transaction_id, "customer_id": customer_id}
        elif tool_name == "detect_dispute_fraud":
            tool_input = {"customer_id": customer_id}
        elif tool_name == "analyze_receipt_evidence":
            # Merchant name will be injected during sequential execution
            tool_input = {
                "receipt_base64": receipt_image_base64 or tool_input.get("receipt_base64", ""),
                "expected_merchant": tool_input.get("expected_merchant", "")
            }
        elif tool_name == "calculate_timeline_from_evidence":
            evidence_data = receipt_image_base64 or tool_input.get("evidence_base64", "")
            tool_input = {
                "evidence_base64": evidence_data,
                "transaction_id": transaction_id
            }
        elif tool_name == "get_delivery_tracking_status":
            tool_input = {"transaction_id": transaction_id}
        elif tool_name == "check_subscription_status":
            tool_input = {"customer_id": customer_id, "merchant_name": ""}
        elif tool_name == "verify_subscription_cancellation":
            cancellation_date = tool_input.get("cancellation_date", "")
            if not cancellation_date:
                from datetime import datetime, timedelta
                cancellation_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
            tool_input = {
                "customer_id": customer_id,
                "merchant_name": "",
                "cancellation_date": cancellation_date
            }
        elif tool_name == "get_refund_timeline":
            tool_input = {"transaction_id": transaction_id}
        elif tool_name == "check_merchant_reputation_score":
            tool_input = {"merchant_name": ""}
        elif tool_name == "get_merchant_dispute_history":
            tool_input = {"merchant_name": ""}

        if data_key == "transaction_details" and "transaction_details" in prior_gathered_data:
            continue

        sanitized.append({
            "tool": tool_name,
            "data_key": data_key,
            "input": tool_input,
        })

    if not sanitized and "transaction_details" not in prior_gathered_data:
        sanitized.append({
            "tool": "get_transaction_details",
            "data_key": "transaction_details",
            "input": {"transaction_id": transaction_id},
        })

    return sanitized


def _execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    # Intercept Vision tool to avoid massive Base64 payloads over SSE crashing the TaskGroup
    if tool_name == "calculate_timeline_from_evidence":
        try:
            import json
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage
            from datetime import datetime
            
            evidence_base64 = tool_input.get("evidence_base64", "")
            if not evidence_base64:
                return {"error": "No return receipt evidence provided."}
                
            image_url = evidence_base64
            if not image_url.startswith("data:image"):
                image_url = f"data:image/jpeg;base64,{evidence_base64}"
                
            llm = ChatOpenAI(model="gpt-4o", temperature=0)
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
            
            # Run synchronously since we are inside the normal execution flow
            response = llm.invoke([message])
            content_str = str(response.content) if not isinstance(response.content, str) else response.content
            cleaned_content = content_str.replace("```json", "").replace("```", "").strip()
            parsed_json = json.loads(cleaned_content)
            
            return_date_str = parsed_json.get("extracted_return_date")
            is_valid = parsed_json.get("is_valid_proof", False)
            
            current_time = datetime.now()
            days_elapsed = 0
            
            if return_date_str and is_valid:
                try:
                    return_date = datetime.strptime(return_date_str, "%Y-%m-%d")
                    days_elapsed = (current_time - return_date).days
                except ValueError:
                    pass
                    
            if days_elapsed <= 3:
                stage = "merchant_review"
            elif days_elapsed <= 7:
                stage = "merchant_escalation"
            elif days_elapsed <= 14:
                stage = "bank_investigation"
            else:
                stage = "provisional_credit"
                
            return {
                "transaction_id": tool_input.get("transaction_id"),
                "return_date_extracted": return_date_str,
                "is_valid_proof": is_valid,
                "days_elapsed": days_elapsed,
                "refund_stage": stage,
                "vision_notes": parsed_json.get("note", "")
            }
        except Exception as e:
            return {"error": f"Vision analysis failed: {str(e)}"}
            
    # Existing execution logic continues below...
    if tool_name == "get_transaction_details":
        return banking_tools.get_transaction_details(tool_input["transaction_id"])
    if tool_name == "get_customer_history":
        return banking_tools.get_customer_history(tool_input["customer_id"], tool_input.get("limit", 5))
    if tool_name == "check_atm_logs":
        return banking_tools.check_atm_logs(tool_input["transaction_id"])
    if tool_name == "get_loan_details":
        return banking_tools.get_loan_details(tool_input["customer_id"])
    if tool_name == "check_merchant_refund_status":
        return banking_tools.check_merchant_refund_status(tool_input["transaction_id"])
    if tool_name == "check_duplicate_transactions":
        trans_details = banking_tools.get_transaction_details(tool_input.get("transaction_id", 0))
        if not trans_details:
            trans_details = {}
        return banking_tools.check_duplicate_transactions(
            customer_id=tool_input["customer_id"],
            merchant_name=trans_details.get("merchant_name", ""),
            amount=trans_details.get("amount", 0),
            date=trans_details.get("transaction_date", ""),
            time_window_hours=24
        )
    if tool_name == "verify_receipt_amount":
        return banking_tools.verify_receipt_amount(tool_input["transaction_id"], tool_input.get("claimed_amount", 0.0))
    if tool_name == "analyze_receipt_evidence":
        result_str = banking_tools.analyze_receipt_evidence(
            tool_input.get("receipt_base64", ""),
            tool_input.get("expected_merchant", "")
        )
        # Parse the JSON string returned by analyze_receipt_evidence
        import json
        return json.loads(result_str)
    if tool_name == "calculate_fraud_risk_score":
        # Import the tool wrapper which handles data fetching and fraud scoring
        from agents.tools_wrapper import calculate_fraud_risk_score_tool
        return calculate_fraud_risk_score_tool.invoke(tool_input)
    if tool_name == "detect_dispute_fraud":
        # Import the tool wrapper which handles dispute fraud detection
        from agents.tools_wrapper import detect_dispute_fraud_tool
        return detect_dispute_fraud_tool.invoke(tool_input)
    if tool_name == "get_delivery_tracking_status":
        return banking_tools.get_delivery_tracking_status(tool_input["transaction_id"])
    if tool_name == "check_subscription_status":
        return banking_tools.check_subscription_status(tool_input["customer_id"], tool_input.get("merchant_name", ""))
    if tool_name == "verify_subscription_cancellation":
        return banking_tools.verify_subscription_cancellation(
            tool_input["customer_id"],
            tool_input.get("merchant_name", ""),
            tool_input.get("cancellation_date", "")
        )
    if tool_name == "get_refund_timeline":
        return banking_tools.get_refund_timeline(tool_input["transaction_id"])
    if tool_name == "check_merchant_reputation_score":
        return banking_tools.check_merchant_reputation_score(tool_input.get("merchant_name", ""))
    if tool_name == "get_merchant_dispute_history":
        return banking_tools.get_merchant_dispute_history(tool_input.get("merchant_name", ""))
    if tool_name == "calculate_timeline_from_evidence":
        return banking_tools.calculate_timeline_from_evidence(
            evidence_base64=tool_input.get("evidence_base64", ""),
            transaction_id=tool_input["transaction_id"]
        )
    return {"error": f"Unsupported tool: {tool_name}"}


def _assess_evidence(
    category: str,
    gathered_data: Dict[str, Any],
    planner_mode: str,
    iteration_count: int,
    clarification_needed: bool,
) -> Tuple[float, float, str]:
    evidence_keys = set(gathered_data.keys())
    base_quality = min(1.0, len(evidence_keys) / 4)

    category_requirements = {
        "fraud": {"transaction_details", "customer_history", "fraud_risk_score", "dispute_fraud_analysis"},
        "fraudulent_transaction": {"transaction_details", "customer_history", "fraud_risk_score", "dispute_fraud_analysis"},
        "duplicate": {"transaction_details", "duplicate_check"},
        "atm_failure": {"transaction_details", "atm_logs"},
        "loan_dispute": {"transaction_details", "loan_details"},
        "refund_not_received": {"transaction_details", "refund_status"},
        "failed_transaction": {"transaction_details"},
        "incorrect_amount": {"transaction_details", "receipt_verification"},
        "merchant_dispute": {"transaction_details", "delivery_status"},
        "unknown": {"transaction_details"},
    }

    required = category_requirements.get(category, {"transaction_details"})
    matched = len(required.intersection(evidence_keys))
    evidence_quality = max(base_quality, matched / max(len(required), 1))

    if clarification_needed and category == "unknown":
        evidence_quality = min(evidence_quality, 0.5)

    confidence = evidence_quality
    if planner_mode == "llm_planner":
        confidence = min(1.0, confidence + 0.1)
    if iteration_count > 0:
        confidence = min(1.0, confidence + 0.05)

    if evidence_quality < 0.6:
        summary = (
            f"Investigation gathered limited evidence for category '{category}'. "
            "Insufficient evidence; may need more information or another investigation pass."
        )
    else:
        summary = (
            f"Investigation gathered sufficient evidence for category '{category}' "
            f"using data points: {sorted(evidence_keys)}."
        )

    return round(confidence, 2), round(evidence_quality, 2), summary


# Made with Bob
