"""
Decision Agent for Banking Dispute Management System

This module contains the decision agent that makes final decisions using
LLM-guided reasoning with hard business-rule validation and execution safety.
"""

from typing import Dict, Any, Tuple
from datetime import datetime
import json
from loguru import logger
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import sys
import os

try:
    from .. import mcp_client as banking_tools
    from .. import models
    from ..database import SessionLocal
    from .state import DisputeState
    from .config import (
        OPENAI_API_KEY,
        DECISION_MODEL,
        DECISION_TEMPERATURE,
        should_escalate_to_human,
        get_human_review_priority,
    )
except ImportError:
    import mcp_client as banking_tools
    import models
    from database import SessionLocal
    from agents.state import DisputeState
    from agents.config import (
        OPENAI_API_KEY,
        DECISION_MODEL,
        DECISION_TEMPERATURE,
        should_escalate_to_human,
        get_human_review_priority,
    )


def decision_node(state: DisputeState) -> Dict[str, Any]:
    """
    Decision Agent: Makes the final decision based on gathered evidence.
    """
    logger.info("[DECISION AGENT] Making final decision...")
    
    logger.info(
        f"[DECISION AGENT] start | ticket_id={state.get('ticket_id')} | "
        f"customer_id={state.get('customer_id')} | category={state.get('dispute_category')}"
    )

    category = state["dispute_category"]
    ticket_id = state["ticket_id"]
    customer_id = state["customer_id"]
    gathered_data = state["gathered_data"]
    audit_trail = list(state["audit_trail"])
    working_memory = dict(state.get("working_memory", {}))
    escalation_reasons = list(state.get("escalation_reasons", []))
    agent_memories = dict(state.get("agent_memories", {}))

    db = SessionLocal()
    try:
        trans_details = gathered_data.get("transaction_details", {})
        transaction_id = trans_details.get("transaction_id")
        amount = trans_details.get("amount", 0.0)
        customer_tier = trans_details.get("account_tier", "Basic")

        llm_reasoning = _generate_decision_reasoning(state)
        proposed_decision = llm_reasoning.get("decision", "human_review_required")
        llm_confidence = float(llm_reasoning.get("confidence", 0.5))

        final_decision, rule_reason = _validate_decision_against_rules(
            proposed_decision=proposed_decision,
            category=category,
            gathered_data=gathered_data,
            amount=float(amount),
            confidence=llm_confidence,
            customer_tier=str(customer_tier),
        )
        if rule_reason:
            escalation_reasons.append(rule_reason)

        justification = llm_reasoning.get("justification", "No justification provided.")
        analysis = llm_reasoning.get("analysis", "No analysis provided.")
        evidence_used = llm_reasoning.get("evidence_used", [])
        risk_factors = llm_reasoning.get("risk_factors", [])
        recommended_actions = llm_reasoning.get("recommended_actions", [])

        _execute_decision_actions(
            final_decision=final_decision,
            category=category,
            ticket_id=ticket_id,
            customer_id=customer_id,
            transaction_id=transaction_id,
            amount=float(amount),
            gathered_data=gathered_data,
            recommended_actions=recommended_actions,
            escalation_summary=justification,
        )

        human_review_priority = get_human_review_priority(
            category=category,
            amount=float(amount),
            customer_tier=str(customer_tier),
        )

        decision_entry = f"""Decision Agent ANALYSIS:
{analysis}

DECISION: {final_decision.upper()} (Confidence: {llm_confidence:.2f})

JUSTIFICATION:
{justification}

EVIDENCE USED:
{chr(10).join(f"- {e}" for e in evidence_used) if evidence_used else "- transaction_details"}

RISK FACTORS:
{chr(10).join(f"- {r}" for r in risk_factors) if risk_factors else "- none identified"}

RECOMMENDED ACTIONS:
{chr(10).join(f"- {a}" for a in recommended_actions) if recommended_actions else "- standard workflow"}

RULE VALIDATION:
{rule_reason or "No rule override required"}"""
        audit_trail.append(decision_entry)
        
        logger.success(f"[DECISION AGENT] Final decision: {final_decision.upper()} - {justification[:100]}...")
        
        logger.info(
            f"[DECISION AGENT] decision={final_decision.upper()} | proposed={proposed_decision} | "
            f"confidence={llm_confidence:.2f} | rule_reason={rule_reason or 'none'}"
        )

        ticket = db.query(models.DisputeTicket).filter(
            models.DisputeTicket.id == ticket_id
        ).first()

        if ticket:
            ticket.status = final_decision  # type: ignore[assignment]
            ticket.resolution_notes = justification  # type: ignore[assignment]
            ticket.updated_at = datetime.utcnow()  # type: ignore[assignment]
            db.commit()
            logger.success(f"[DECISION AGENT] ticket_updated | ticket_id={ticket_id} | status={ticket.status}")

        for entry in audit_trail:
            if "THOUGHT:" in entry or "Triage Agent" in entry or "Clarification Agent" in entry or "Orchestrator:" in entry:
                action_type = "thought"
                agent_name = "System"
            elif "ACTION:" in entry:
                action_type = "tool_call"
                agent_name = "InvestigatorAgent"
            elif "OBSERVATION:" in entry:
                action_type = "observation"
                agent_name = "InvestigatorAgent"
            elif "DECISION:" in entry or "Decision Agent ANALYSIS:" in entry:
                action_type = "decision"
                agent_name = "DecisionAgent"
            else:
                action_type = "thought"
                agent_name = "System"

            audit_log = models.AuditLog(
                ticket_id=ticket_id,
                agent_name=agent_name,
                action_type=action_type,
                description=entry,
                timestamp=datetime.utcnow()
            )
            db.add(audit_log)

        db.commit()
        logger.info(f"[DECISION AGENT] audit_logs_saved | count={len(audit_trail)}")

        decision_memory = agent_memories.get(
            "decision",
            {
                "agent_name": "decision",
                "past_actions": [],
                "learned_patterns": {},
                "confidence_history": [],
            }
        )
        decision_memory["past_actions"].append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "category": category,
                "proposed_decision": proposed_decision,
                "final_decision": final_decision,
                "rule_reason": rule_reason,
            }
        )
        decision_memory["confidence_history"].append(llm_confidence)
        agent_memories["decision"] = decision_memory

        working_memory["last_decision"] = final_decision
        working_memory["last_decision_timestamp"] = datetime.utcnow().isoformat()

        logger.success(f"[DECISION AGENT] complete | final_decision={final_decision.upper()}")

        return {
            "final_decision": final_decision,
            "audit_trail": audit_trail,
            "decision_confidence": llm_confidence,
            "decision_reasoning": llm_reasoning,
            "working_memory": working_memory,
            "escalation_reasons": escalation_reasons,
            "human_review_priority": human_review_priority,
            "decision_quality_score": llm_confidence,
            "agent_memories": agent_memories,
        }

    except Exception as e:
        logger.exception(f"Error during decision making: {str(e)}")
        audit_entry = f"Decision Agent ERROR: {str(e)}"
        audit_trail.append(audit_entry)
        return {
            "final_decision": "human_review_required",
            "audit_trail": audit_trail,
            "decision_confidence": 0.2,
            "escalation_reasons": escalation_reasons + [f"Decision failure: {str(e)}"],
            "human_review_priority": "high",
        }
    finally:
        db.close()


def _build_compliance_query(state: DisputeState) -> str:
    category = state["dispute_category"]
    gathered_data = state["gathered_data"]
    query = state["customer_query"]
    trans_details = gathered_data.get("transaction_details", {})

    compliance_context = [
        f"Category: {category}",
        f"Customer query: {query}",
    ]

    if trans_details:
        compliance_context.extend(
            [
                f"Transaction status: {trans_details.get('status', 'unknown')}",
                f"Amount: {trans_details.get('amount', 'unknown')}",
                f"Account tier: {trans_details.get('account_tier', 'unknown')}",
                f"International: {trans_details.get('is_international', False)}",
            ]
        )

    if category == "duplicate":
        duplicate_check = gathered_data.get("duplicate_check", {})
        compliance_context.append(
            f"Duplicate check: {json.dumps(duplicate_check, default=str)}"
        )
    elif category == "atm_failure":
        atm_logs = gathered_data.get("atm_logs", {})
        compliance_context.append(f"ATM logs: {json.dumps(atm_logs, default=str)}")
    elif category == "loan_dispute":
        loan_details = gathered_data.get("loan_details", {})
        compliance_context.append(f"Loan details: {json.dumps(loan_details, default=str)}")

    return " | ".join(compliance_context)


def _fetch_compliance_policy_text(state: DisputeState) -> str:
    compliance_query = _build_compliance_query(state)
    compliance_result = banking_tools.query_compliance_policy(compliance_query)

    if compliance_result.get("matched"):
        policy_text = compliance_result.get("policy_text", "").strip()
        if policy_text:
            logger.info("[DECISION AGENT] compliance_policy_lookup | matched=true")
            return policy_text

    logger.warning("[DECISION AGENT] compliance_policy_lookup | matched=false_using_fallback")
    return (
        "No directly matching compliance policy found. Escalate to human review when "
        "policy guidance is unclear."
    )


def _generate_decision_reasoning(state: DisputeState) -> Dict[str, Any]:
    """
    Generate LLM-powered decision reasoning with comprehensive analysis.
    
    This function uses an LLM to deeply analyze all gathered evidence and make
    an informed decision with detailed justification. The LLM considers:
    - All gathered evidence
    - Business rules and compliance requirements
    - Risk factors and patterns
    - Customer context and history
    
    Returns a structured decision with reasoning, confidence, and recommendations.
    """
    category = state["dispute_category"]
    gathered_data = state["gathered_data"]
    query = state["customer_query"]
    summary = state.get("investigation_summary", "")
    triage_confidence = state.get("triage_confidence", 0.0)
    investigation_confidence = state.get("investigation_confidence", 0.0)

    compliance_policy_text = _fetch_compliance_policy_text(state)
    fallback = _rule_based_reasoning(state, compliance_policy_text)
    if not OPENAI_API_KEY:
        logger.info("No OpenAI API key, using rule-based decision")
        return fallback

    try:
        # Initialize LLM with custom http_client to avoid proxies parameter issue
        import httpx
        http_client = httpx.Client()
        llm = ChatOpenAI(
            model=DECISION_MODEL,
            temperature=DECISION_TEMPERATURE,
            api_key=SecretStr(OPENAI_API_KEY),
            http_client=http_client
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a senior banking dispute resolution specialist with 15+ years of experience in fraud detection, compliance, and customer service.

Your task is to analyze all evidence and make a well-reasoned decision that balances customer satisfaction, risk management, and regulatory compliance.

You must use the exact compliance policy text provided in the context below as authoritative policy guidance. Do not invent additional bank policy text beyond what is supplied. If the supplied policy text is unclear or insufficient, reflect that uncertainty and prefer human review where appropriate.

DECISION FRAMEWORK:
1. ANALYZE: Review all gathered evidence systematically
2. CROSS-REFERENCE: Check evidence against the supplied compliance policy text
3. ASSESS RISK: Identify potential fraud indicators or red flags
4. WEIGH FACTORS: Balance customer impact vs bank risk
5. DECIDE: Choose the most appropriate decision
6. JUSTIFY: Provide clear reasoning with evidence references and the supplied policy text
7. RECOMMEND: Suggest specific actions to execute

CONFIDENCE CALIBRATION:
- 0.95-1.0: Extremely clear case with strong evidence
- 0.85-0.94: Strong case with good evidence
- 0.70-0.84: Moderate confidence, some ambiguity
- 0.50-0.69: Low confidence, significant uncertainty
- Below 0.50: Very uncertain, definitely needs human review

Return ONLY valid JSON in this exact format:
{{
  "analysis": "Comprehensive analysis of all evidence, patterns observed, and key findings",
  "decision": "auto_approved|auto_rejected|human_review_required",
  "confidence": 0.0-1.0,
  "justification": "Clear explanation of why this decision was made, referencing specific evidence and the supplied policy text",
  "evidence_used": ["evidence_key1", "evidence_key2", "evidence_key3"],
  "evidence_summary": {{
    "transaction_details": "summary of transaction evidence",
    "customer_history": "summary of customer pattern",
    "specific_findings": "key findings from investigation"
  }},
  "risk_factors": ["risk1", "risk2"],
  "risk_assessment": "Overall risk level: low|medium|high",
  "recommended_actions": ["action1", "action2"],
  "alternative_decisions_considered": ["decision1: reason", "decision2: reason"],
  "compliance_notes": "Any compliance or regulatory considerations from the supplied policy text"
}}"""),
            ("user", """Analyze this banking dispute and make a decision:

DISPUTE INFORMATION:
- Category: {category}
- Customer Query: "{query}"
- Triage Confidence: {triage_confidence}
- Investigation Confidence: {investigation_confidence}

INVESTIGATION SUMMARY:
{summary}

COMPLIANCE POLICY TEXT:
{compliance_policy_text}

GATHERED EVIDENCE:
{evidence}

Provide your comprehensive analysis and decision:""")
        ])

        logger.debug(f"[DECISION AGENT] action=invoke_llm_reasoner | model={DECISION_MODEL}")
        response = llm.invoke(prompt.format_messages(
            category=category,
            query=query,
            triage_confidence=triage_confidence,
            investigation_confidence=investigation_confidence,
            summary=summary if summary else "No summary provided",
            compliance_policy_text=compliance_policy_text,
            evidence=json.dumps(gathered_data, indent=2, default=str),
        ))

        content = response.content if isinstance(response.content, str) else json.dumps(response.content)
        content = content.strip()
        
        # Extract JSON from markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        parsed = json.loads(content)
        
        # Validate decision value
        decision = parsed.get("decision", "human_review_required")
        if decision not in {"auto_approved", "auto_rejected", "human_review_required"}:
            logger.warning(f"Invalid decision '{decision}' from LLM, using fallback")
            return fallback
        
        # Ensure all required fields exist
        parsed.setdefault("analysis", "No analysis provided")
        parsed.setdefault("confidence", 0.5)
        parsed.setdefault("justification", "No justification provided")
        parsed.setdefault("evidence_used", list(gathered_data.keys()))
        parsed.setdefault("risk_factors", [])
        parsed.setdefault("recommended_actions", [])
        
        logger.info(
            f"[DECISION AGENT] llm_result | decision={decision} | "
            f"confidence={parsed.get('confidence', 0.5):.2f} | "
            f"risk_factors={len(parsed.get('risk_factors', []))}"
        )
        
        return parsed

    except json.JSONDecodeError as e:
        logger.exception(f"Failed to parse LLM decision response: {str(e)}")
        return fallback
    except Exception as e:
        logger.exception(f"LLM decision reasoning failed: {str(e)}")
        return fallback


def _rule_based_reasoning(state: DisputeState, compliance_policy_text: str = "") -> Dict[str, Any]:
    category = state["dispute_category"]
    gathered_data = state["gathered_data"]
    trans_details = gathered_data.get("transaction_details", {})
    amount = trans_details.get("amount", 0.0)

    if category == "atm_failure" and gathered_data.get("atm_logs", {}).get("has_hardware_fault", False):
        return {
            "analysis": "ATM logs show a hardware fault linked to the transaction.",
            "decision": "auto_approved",
            "confidence": 0.95,
            "justification": (
                f"ATM hardware fault confirmed. Approving refund of ${amount}. "
                f"Relevant policy: {compliance_policy_text}"
            ),
            "evidence_used": ["transaction_details", "atm_logs"],
            "risk_factors": [],
            "recommended_actions": ["initiate_refund"],
        }

    if category == "loan_dispute":
        return {
            "analysis": "Loan disputes are governed by compliance rules and must be reviewed by humans.",
            "decision": "human_review_required",
            "confidence": 0.98,
            "justification": (
                "Loan dispute requires human review due to compliance constraints. "
                f"Relevant policy: {compliance_policy_text}"
            ),
            "evidence_used": list(gathered_data.keys()),
            "risk_factors": ["compliance_sensitive"],
            "recommended_actions": ["route_to_human"],
        }

    if category == "failed_transaction" and trans_details.get("status") == "failed":
        return {
            "analysis": "Transaction status is failed while the customer reports deduction.",
            "decision": "auto_approved",
            "confidence": 0.9,
            "justification": (
                f"Failed transaction supported by status evidence. Approving refund of ${amount}. "
                f"Relevant policy: {compliance_policy_text}"
            ),
            "evidence_used": ["transaction_details"],
            "risk_factors": [],
            "recommended_actions": ["initiate_refund"],
        }

    return {
        "analysis": "Available evidence is mixed or incomplete.",
        "decision": "human_review_required",
        "confidence": 0.65,
        "justification": (
            "Routing to human review because evidence is incomplete or requires judgment. "
            f"Relevant policy: {compliance_policy_text}"
        ),
        "evidence_used": list(gathered_data.keys()),
        "risk_factors": ["insufficient_evidence"],
        "recommended_actions": ["route_to_human"],
    }


def _validate_decision_against_rules(
    proposed_decision: str,
    category: str,
    gathered_data: Dict[str, Any],
    amount: float,
    confidence: float,
    customer_tier: str,
) -> Tuple[str, str]:
    should_escalate, reason = should_escalate_to_human(
        category=category,
        amount=amount,
        confidence=confidence,
        customer_tier=customer_tier,
    )
    if should_escalate:
        return "human_review_required", reason

    if category == "atm_failure":
        atm_logs = gathered_data.get("atm_logs", {})
        if atm_logs.get("has_hardware_fault", False):
            return "auto_approved", "ATM hardware fault rule triggered"
        if not atm_logs:
            return "human_review_required", "ATM evidence missing"

    if category == "duplicate":
        dup_check = gathered_data.get("duplicate_check", {})
        transactions = dup_check.get("transactions", [])
        if dup_check.get("duplicates_found", False) and len(transactions) >= 2:
            time_diff = transactions[1].get("time_difference_minutes", 999)
            if time_diff < 5:
                return "auto_approved", "Duplicate charge within 5 minutes rule triggered"
        if not dup_check.get("duplicates_found", False):
            return "auto_rejected", "No duplicate evidence found"

    if category == "fraud":
        trans_details = gathered_data.get("transaction_details", {})
        if trans_details.get("is_international", False):
            return "auto_approved", "International fraud anomaly rule triggered"

    if category == "failed_transaction":
        trans_details = gathered_data.get("transaction_details", {})
        if trans_details.get("status") == "failed":
            return "auto_approved", "Failed transaction rule triggered"

    if proposed_decision not in {"auto_approved", "auto_rejected", "human_review_required"}:
        return "human_review_required", "Invalid proposed decision"

    return proposed_decision, ""


def _execute_decision_actions(
    final_decision: str,
    category: str,
    ticket_id: int,
    customer_id: int,
    transaction_id: Any,
    amount: float,
    gathered_data: Dict[str, Any],
    recommended_actions: list,
    escalation_summary: str,
) -> None:
    if final_decision == "auto_approved" and transaction_id is not None:
        if category == "fraud":
            banking_tools.block_card(customer_id, f"Suspected fraud for disputed transaction {transaction_id}")
            banking_tools.initiate_refund(transaction_id, amount, "Fraud dispute approved")
        elif category in {"atm_failure", "duplicate", "failed_transaction"}:
            banking_tools.initiate_refund(transaction_id, amount, f"{category} dispute approved")
    elif final_decision == "human_review_required":
        banking_tools.route_to_human(ticket_id, escalation_summary)


# Made with Bob
