"""
Investigator Agent for Banking Dispute Management System

This module contains the investigator agent that gathers evidence using a
dynamic ReAct-style tool plan with optional LLM guidance and rule-based fallback.
"""

from typing import Dict, Any, List, Tuple
import json
from loguru import logger
from datetime import datetime
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import banking_tools
import models
from database import SessionLocal
from .state import DisputeState
from .config import OPENAI_API_KEY, INVESTIGATOR_MODEL, INVESTIGATOR_TEMPERATURE


def investigator_node(state: DisputeState) -> Dict[str, Any]:
    """
    Investigator Agent: Gathers evidence using dynamic tool selection.
    """
    category = state["dispute_category"]
    logger.info(f"[INVESTIGATOR AGENT] Gathering evidence for {category}...")
    
    logger.info(
        f"[INVESTIGATOR AGENT] start | ticket_id={state.get('ticket_id')} | "
        f"customer_id={state.get('customer_id')} | category={state.get('dispute_category')} | "
        f"iteration={state.get('iteration_count', 0)}"
    )

    ticket_id = state["ticket_id"]
    customer_id = state["customer_id"]
    gathered_data = dict(state["gathered_data"])
    audit_trail = list(state["audit_trail"])
    working_memory = dict(state.get("working_memory", {}))
    agent_memories = dict(state.get("agent_memories", {}))
    iteration_count = state.get("iteration_count", 0)

    db = SessionLocal()
    try:
        ticket = db.query(models.DisputeTicket).filter(
            models.DisputeTicket.id == ticket_id
        ).first()

        if not ticket:
            audit_trail.append("Investigator Agent: ERROR - Ticket not found")
            return {
                "gathered_data": gathered_data,
                "audit_trail": audit_trail,
                "investigation_confidence": 0.0,
                "evidence_quality_score": 0.0,
                "investigation_summary": "Ticket not found"
            }

        transaction_id: int = ticket.transaction_id  # type: ignore[assignment]

        plan, planner_mode = _build_investigation_plan(
            category=category,
            customer_id=customer_id,
            transaction_id=transaction_id,
            customer_query=state["customer_query"],
            working_memory=working_memory,
            prior_gathered_data=gathered_data,
        )

        logger.info(
            f"[INVESTIGATOR AGENT] plan_created | planner_mode={planner_mode} | "
            f"steps={[step['tool'] for step in plan]}"
        )
        audit_trail.append(
            f"Investigator Agent THOUGHT: Built investigation plan using {planner_mode}. "
            f"Planned steps: {[step['tool'] for step in plan]}"
        )

        executed_steps: List[str] = []
        for step in plan:
            tool_name = step["tool"]
            tool_input = step["input"]
            data_key = step["data_key"]

            logger.info(f"[INVESTIGATOR AGENT] Thought: need to use {tool_name}")
            
            logger.debug(
                f"[INVESTIGATOR AGENT] action=tool_call | tool={tool_name} | "
                f"input={json.dumps(tool_input, default=str)}"
            )
            
            logger.info(f"[INVESTIGATOR AGENT] Action: calling {tool_name} with {tool_input}")
            
            audit_trail.append(
                f"Investigator Agent ACTION: Calling {tool_name} with input {json.dumps(tool_input, default=str)}"
            )

            observation = _execute_tool(tool_name, tool_input)
            gathered_data[data_key] = observation
            executed_steps.append(tool_name)

            logger.info(f"[INVESTIGATOR AGENT] Observation: {tool_name} returned data")
            
            logger.info(
                f"[INVESTIGATOR AGENT] observation | tool={tool_name} | "
                f"output={json.dumps(observation, default=str)}"
            )
            audit_trail.append(
                f"Investigator Agent OBSERVATION: {tool_name} returned {json.dumps(observation, default=str)}"
            )

        investigation_confidence, evidence_quality_score, summary = _assess_evidence(
            category=category,
            gathered_data=gathered_data,
            planner_mode=planner_mode,
            iteration_count=iteration_count,
            clarification_needed=working_memory.get("clarification_needed", False),
        )

        working_memory["last_investigation_plan"] = plan
        working_memory["last_investigation_timestamp"] = datetime.utcnow().isoformat()

        investigator_memory = agent_memories.get(
            "investigator",
            {
                "agent_name": "investigator",
                "past_actions": [],
                "learned_patterns": {},
                "confidence_history": [],
            }
        )
        investigator_memory["past_actions"].append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "category": category,
                "executed_tools": executed_steps,
                "planner_mode": planner_mode,
                "summary": summary,
            }
        )
        investigator_memory["confidence_history"].append(investigation_confidence)
        agent_memories["investigator"] = investigator_memory

        logger.success(
            f"[INVESTIGATOR AGENT] complete | gathered_data_points={len(gathered_data)} | "
            f"confidence={investigation_confidence:.2f} | quality={evidence_quality_score:.2f}"
        )

        return {
            "gathered_data": gathered_data,
            "audit_trail": audit_trail,
            "investigation_confidence": investigation_confidence,
            "evidence_quality_score": evidence_quality_score,
            "investigation_summary": summary,
            "working_memory": working_memory,
            "agent_memories": agent_memories,
        }

    except Exception as e:
        logger.exception(f"Error during investigation: {str(e)}")
        audit_trail.append(f"Investigator Agent ERROR: {str(e)}")
        return {
            "gathered_data": gathered_data,
            "audit_trail": audit_trail,
            "investigation_confidence": 0.2,
            "evidence_quality_score": 0.2,
            "investigation_summary": f"Investigation failed: {str(e)}",
        }
    finally:
        db.close()


def _build_investigation_plan(
    category: str,
    customer_id: int,
    transaction_id: int,
    customer_query: str,
    working_memory: Dict[str, Any],
    prior_gathered_data: Dict[str, Any],
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
   
3. check_atm_logs - Queries ATM machine logs for hardware faults
   Use when: ATM dispute, need to verify if cash was dispensed or hardware fault occurred
   
4. check_duplicate_transactions - Searches for duplicate charges in time window
   Use when: Duplicate charge suspected, need to find matching transactions
   
5. get_loan_details - Retrieves loan EMI schedule and outstanding balance
   Use when: Loan/EMI dispute, need loan account information
   
6. check_merchant_refund_status - Checks if merchant initiated refund
   Use when: Refund not received, need to verify merchant/gateway status

INVESTIGATION STRATEGY:
- Start with transaction_details if not already available
- Choose tools that directly address the dispute category
- Consider customer query for additional context clues
- Avoid redundant tool calls (check prior_data_keys)
- Plan 2-4 tools maximum for efficiency

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
        sanitized = _sanitize_plan(steps, customer_id, transaction_id, prior_gathered_data)
        
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

    if category == "fraud":
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

    return plan


def _sanitize_plan(
    steps: List[Dict[str, Any]],
    customer_id: int,
    transaction_id: int,
    prior_gathered_data: Dict[str, Any],
) -> List[Dict[str, Any]]:
    allowed = {
        "get_transaction_details": "transaction_details",
        "get_customer_history": "customer_history",
        "check_atm_logs": "atm_logs",
        "check_duplicate_transactions": "duplicate_check",
        "get_loan_details": "loan_details",
        "check_merchant_refund_status": "refund_status",
    }

    sanitized: List[Dict[str, Any]] = []
    for step in steps:
        tool_name = step.get("tool")
        if tool_name not in allowed:
            continue

        data_key = step.get("data_key") or allowed[tool_name]
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
        "fraud": {"transaction_details", "customer_history"},
        "duplicate": {"transaction_details", "duplicate_check"},
        "atm_failure": {"transaction_details", "atm_logs"},
        "loan_dispute": {"transaction_details", "loan_details"},
        "refund_not_received": {"transaction_details", "refund_status"},
        "failed_transaction": {"transaction_details"},
        "merchant_dispute": {"transaction_details"},
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
