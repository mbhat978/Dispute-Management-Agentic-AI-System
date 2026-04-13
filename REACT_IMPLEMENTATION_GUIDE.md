# ReAct Implementation Guide - Step-by-Step

This guide provides a practical, step-by-step approach to implementing the ReAct improvements in your Banking Dispute Management System.

## Phase 1: Setup and Configuration (Day 1)

### Step 1.1: Update Environment Variables

Add to your `.env` file:
```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Model Selection
TRIAGE_MODEL=gpt-3.5-turbo
INVESTIGATOR_MODEL=gpt-4
DECISION_MODEL=gpt-4

# Feature Flags
ENABLE_REACT_TRIAGE=true
ENABLE_REACT_INVESTIGATOR=true
ENABLE_REACT_DECISION=true
ENABLE_FALLBACK=true  # Fallback to rule-based if LLM fails
```

### Step 1.2: Install Additional Dependencies

Update `backend/requirements.txt`:
```txt
# Existing dependencies...

# Enhanced LangChain for ReAct
langchain>=0.1.0
langchain-openai>=0.0.5
langchain-core>=0.1.0
langgraph>=0.0.20

# For structured output parsing
pydantic>=2.0.0
```

Install:
```bash
cd backend
pip install -r requirements.txt
```

## Phase 2: Implement LLM-Powered Triage (Day 2-3)

### Step 2.1: Create Enhanced Triage Agent

The file `backend/agents/triage_react.py` has been created with:
- LLM-powered classification
- Confidence scoring
- Detailed reasoning
- Fallback to rule-based system

### Step 2.2: Update Main to Use ReAct Triage

In `backend/main.py`, modify the dispute processing:

```python
# Add at top of file
from agents.triage_react import triage_node_react
from agents.config import ENABLE_REACT_TRIAGE

# In process_dispute endpoint, replace:
triage_result = triage_node(initial_state)

# With:
if os.getenv("ENABLE_REACT_TRIAGE", "false").lower() == "true":
    triage_result = triage_node_react(initial_state)
else:
    triage_result = triage_node(initial_state)
```

### Step 2.3: Test Triage Agent

```bash
# Test with a sample dispute
curl -X POST http://localhost:8000/api/disputes/process \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": 1,
    "customer_id": 1,
    "customer_query": "I did not authorize this international transaction of $8500"
  }'
```

Check the audit trail for LLM reasoning.

## Phase 3: Implement ReAct Investigator (Day 4-6)

### Step 3.1: Create ReAct Investigator

Create `backend/agents/investigator_react.py`:

```python
"""
ReAct Investigator Agent with Dynamic Tool Selection
"""

from typing import Dict, Any
from langchain.agents import create_react_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from .state import DisputeState
from .tools_wrapper import ALL_TOOLS
from .config import INVESTIGATOR_MODEL, INVESTIGATOR_TEMPERATURE, OPENAI_API_KEY

def investigator_node_react(state: DisputeState) -> Dict[str, Any]:
    """
    ReAct Investigator: Dynamically selects and uses tools based on context.
    """
    print("\n[INVESTIGATOR AGENT - REACT] Starting dynamic investigation...")
    
    if not OPENAI_API_KEY:
        print("  [WARNING] No API key, falling back to rule-based investigator")
        from .investigator import investigator_node
        return investigator_node(state)
    
    try:
        llm = ChatOpenAI(
            model=INVESTIGATOR_MODEL,
            temperature=INVESTIGATOR_TEMPERATURE
        )
        
        # ReAct prompt
        react_prompt = PromptTemplate.from_template("""
You are an expert banking dispute investigator. Your goal is to gather sufficient evidence to make a decision.

Dispute Information:
- Category: {category}
- Customer Query: {query}
- Transaction ID: {transaction_id}
- Customer ID: {customer_id}

Available Tools:
{tools}

Tool Names: {tool_names}

Use this format:

Thought: I need to understand what information is required for this type of dispute
Action: tool_name
Action Input: {{"param1": "value1", "param2": "value2"}}
Observation: [tool result will appear here]
... (repeat Thought/Action/Observation as needed)
Thought: I now have sufficient evidence to make a recommendation
Final Answer: Comprehensive summary of findings with recommendation

Guidelines:
1. Start with get_transaction_details_tool to understand the transaction
2. Based on category, select appropriate tools
3. Gather evidence systematically
4. Stop when you have sufficient information
5. Provide clear summary of findings

Begin!

{agent_scratchpad}
""")
        
        # Create agent
        agent = create_react_agent(llm, ALL_TOOLS, react_prompt)
        agent_executor = AgentExecutor(
            agent=agent,
            tools=ALL_TOOLS,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )
        
        # Execute
        result = agent_executor.invoke({
            "category": state["dispute_category"],
            "query": state["customer_query"],
            "transaction_id": state["ticket_id"],
            "customer_id": state["customer_id"],
            "tools": "\n".join([f"- {t.name}: {t.description}" for t in ALL_TOOLS]),
            "tool_names": ", ".join([t.name for t in ALL_TOOLS])
        })
        
        # Extract audit trail from intermediate steps
        audit_entries = []
        gathered_data = {}
        
        for step in result["intermediate_steps"]:
            action, observation = step
            audit_entries.append(f"THOUGHT: {action.log}")
            audit_entries.append(f"ACTION: {action.tool}({action.tool_input})")
            audit_entries.append(f"OBSERVATION: {observation}")
            
            # Store tool results
            gathered_data[action.tool] = observation
        
        return {
            "gathered_data": gathered_data,
            "investigation_summary": result["output"],
            "investigation_confidence": 0.8,  # Can be calculated based on evidence
            "audit_trail": state["audit_trail"] + audit_entries
        }
        
    except Exception as e:
        print(f"  [ERROR] ReAct investigator failed: {str(e)}")
        from .investigator import investigator_node
        return investigator_node(state)
```

### Step 3.2: Update Main to Use ReAct Investigator

```python
from agents.investigator_react import investigator_node_react

# In process_dispute:
if os.getenv("ENABLE_REACT_INVESTIGATOR", "false").lower() == "true":
    investigator_result = investigator_node_react(triage_state)
else:
    investigator_result = investigator_node(triage_state)
```

## Phase 4: Implement LLM-Powered Decision Agent (Day 7-8)

### Step 4.1: Create Decision Agent with LLM

Create `backend/agents/decision_react.py`:

```python
"""
LLM-Powered Decision Agent with Business Rule Validation
"""

from typing import Dict, Any
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from .state import DisputeState
from .config import (
    DECISION_MODEL,
    DECISION_TEMPERATURE,
    MANDATORY_HUMAN_REVIEW_CATEGORIES,
    OPENAI_API_KEY
)
import banking_tools
from database import SessionLocal
import models
from datetime import datetime

def decision_node_react(state: DisputeState) -> Dict[str, Any]:
    """
    LLM-Powered Decision Agent with rule validation.
    """
    print("\n[DECISION AGENT - REACT] Making decision with LLM...")
    
    if not OPENAI_API_KEY:
        print("  [WARNING] No API key, using rule-based decision")
        from .decision import decision_node
        return decision_node(state)
    
    try:
        llm = ChatOpenAI(
            model=DECISION_MODEL,
            temperature=DECISION_TEMPERATURE
        )
        
        # Decision prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a senior banking dispute resolution specialist making final decisions.

Business Rules (MUST FOLLOW):
1. ATM hardware fault confirmed → Auto-approve refund
2. Duplicate charge within 5 min → Auto-approve refund
3. Fraud on international transaction → Auto-approve, block card
4. Loan disputes → ALWAYS route to human (compliance)
5. Amount > $10,000 → Route to human review
6. Unclear evidence → Route to human review

Your task:
1. ANALYZE: Review all gathered evidence thoroughly
2. APPLY RULES: Check if any mandatory rules apply
3. REASON: Use judgment for cases not covered by rules
4. DECIDE: Choose auto_approved, auto_rejected, or human_review_required
5. JUSTIFY: Provide clear explanation with evidence

Respond in JSON:
{{
    "analysis": "detailed analysis of all evidence",
    "decision": "auto_approved|auto_rejected|human_review_required",
    "confidence": 0.95,
    "justification": "clear explanation referencing evidence",
    "evidence_used": ["evidence1", "evidence2"],
    "risk_factors": ["risk1", "risk2"],
    "recommended_actions": ["action1", "action2"]
}}"""),
            ("user", """
Category: {category}
Customer Query: {query}

Gathered Evidence:
{evidence}

Investigation Summary:
{summary}

Make your decision:""")
        ])
        
        response = llm.invoke(prompt.format_messages(
            category=state["dispute_category"],
            query=state["customer_query"],
            evidence=json.dumps(state["gathered_data"], indent=2),
            summary=state.get("investigation_summary", "")
        ))
        
        # Parse response
        try:
            llm_decision = json.loads(response.content)
        except:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            llm_decision = json.loads(content)
        
        # Validate against hard rules
        final_decision = validate_decision_against_rules(
            llm_decision["decision"],
            state["dispute_category"],
            state["gathered_data"]
        )
        
        # Execute actions
        execute_decision_actions(state, final_decision, llm_decision)
        
        # Build audit entry
        audit_entry = f"""Decision Agent (ReAct) - LLM Analysis:

ANALYSIS:
{llm_decision['analysis']}

DECISION: {final_decision}
CONFIDENCE: {llm_decision['confidence']:.2f}

JUSTIFICATION:
{llm_decision['justification']}

EVIDENCE USED:
{chr(10).join(f"  • {e}" for e in llm_decision['evidence_used'])}

RISK FACTORS:
{chr(10).join(f"  • {r}" for r in llm_decision.get('risk_factors', []))}

ACTIONS TAKEN:
{chr(10).join(f"  • {a}" for a in llm_decision.get('recommended_actions', []))}

Model: {DECISION_MODEL}"""
        
        return {
            "final_decision": final_decision,
            "decision_confidence": llm_decision["confidence"],
            "decision_reasoning": llm_decision,
            "audit_trail": state["audit_trail"] + [audit_entry]
        }
        
    except Exception as e:
        print(f"  [ERROR] LLM decision failed: {str(e)}")
        from .decision import decision_node
        return decision_node(state)


def validate_decision_against_rules(
    llm_decision: str,
    category: str,
    evidence: Dict[str, Any]
) -> str:
    """Validate LLM decision against mandatory business rules."""
    
    # Rule 1: Loan disputes MUST go to human
    if category in MANDATORY_HUMAN_REVIEW_CATEGORIES:
        return "human_review_required"
    
    # Rule 2: High-value disputes
    trans_details = evidence.get("transaction_details", {})
    amount = trans_details.get("amount", 0)
    if amount > 10000:
        return "human_review_required"
    
    # Otherwise, trust LLM decision
    return llm_decision


def execute_decision_actions(
    state: DisputeState,
    decision: str,
    reasoning: Dict[str, Any]
):
    """Execute actions based on decision."""
    
    trans_details = state["gathered_data"].get("transaction_details", {})
    transaction_id = trans_details.get("transaction_id")
    amount = trans_details.get("amount", 0)
    
    if decision == "auto_approved":
        # Initiate refund
        if transaction_id:
            banking_tools.initiate_refund(
                transaction_id,
                amount,
                reasoning.get("justification", "Approved by AI")
            )
        
        # Block card if fraud
        if state["dispute_category"] == "fraud":
            banking_tools.block_card(
                state["customer_id"],
                "Fraud detected - card blocked for security"
            )
    
    elif decision == "human_review_required":
        # Route to human
        banking_tools.route_to_human(
            state["ticket_id"],
            reasoning.get("justification", "Requires human review")
        )
```

## Phase 5: Testing and Validation (Day 9-10)

### Step 5.1: Create Test Suite

Create `backend/test_react_agents.py`:

```python
"""
Test suite for ReAct agents
"""

import requests
import json

BASE_URL = "http://localhost:8000"

test_cases = [
    {
        "name": "Fraud - International Transaction",
        "data": {
            "transaction_id": 1,
            "customer_id": 2,
            "customer_query": "I did not authorize this $8500 international transaction"
        },
        "expected_category": "fraud",
        "expected_decision": "auto_approved"
    },
    {
        "name": "ATM Failure",
        "data": {
            "transaction_id": 6,
            "customer_id": 3,
            "customer_query": "ATM did not dispense cash but debited $200"
        },
        "expected_category": "atm_failure",
        "expected_decision": "auto_approved"
    },
    {
        "name": "Duplicate Charge",
        "data": {
            "transaction_id": 7,
            "customer_id": 4,
            "customer_query": "I was charged twice for the same purchase"
        },
        "expected_category": "duplicate",
        "expected_decision": "auto_approved"
    },
    {
        "name": "Loan Dispute - Must Route to Human",
        "data": {
            "transaction_id": 10,
            "customer_id": 1,
            "customer_query": "My EMI amount is incorrect"
        },
        "expected_category": "loan_dispute",
        "expected_decision": "human_review_required"
    }
]

def run_tests():
    """Run all test cases."""
    print("="*80)
    print("TESTING REACT AGENTS")
    print("="*80)
    
    results = []
    
    for test in test_cases:
        print(f"\n[TEST] {test['name']}")
        print(f"Query: {test['data']['customer_query']}")
        
        response = requests.post(
            f"{BASE_URL}/api/disputes/process",
            json=test['data']
        )
        
        if response.status_code == 200:
            result = response.json()
            
            category_match = result['dispute_category'] == test['expected_category']
            decision_match = result['final_decision'] == test['expected_decision']
            
            print(f"  Category: {result['dispute_category']} {'✓' if category_match else '✗'}")
            print(f"  Decision: {result['final_decision']} {'✓' if decision_match else '✗'}")
            print(f"  Confidence: Triage={result.get('triage_confidence', 'N/A')}")
            
            results.append({
                "test": test['name'],
                "passed": category_match and decision_match,
                "category_match": category_match,
                "decision_match": decision_match
            })
        else:
            print(f"  ERROR: {response.status_code}")
            results.append({
                "test": test['name'],
                "passed": False,
                "error": response.text
            })
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    passed = sum(1 for r in results if r['passed'])
    total = len(results)
    print(f"Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    
    for r in results:
        status = "✓ PASS" if r['passed'] else "✗ FAIL"
        print(f"  {status}: {r['test']}")

if __name__ == "__main__":
    run_tests()
```

Run tests:
```bash
python backend/test_react_agents.py
```

## Phase 6: Monitoring and Optimization (Ongoing)

### Step 6.1: Add Logging

Create `backend/agents/monitoring.py`:

```python
"""
Monitoring and logging for ReAct agents
"""

import time
from functools import wraps
from typing import Callable, Any
import json

def monitor_agent(agent_name: str):
    """Decorator to monitor agent performance."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(state: Any) -> Any:
            start_time = time.time()
            
            print(f"\n[MONITOR] {agent_name} started")
            
            try:
                result = func(state)
                duration = time.time() - start_time
                
                print(f"[MONITOR] {agent_name} completed in {duration:.2f}s")
                
                # Log metrics
                log_agent_metrics(agent_name, duration, "success", result)
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                print(f"[MONITOR] {agent_name} failed after {duration:.2f}s: {str(e)}")
                
                log_agent_metrics(agent_name, duration, "error", {"error": str(e)})
                raise
        
        return wrapper
    return decorator


def log_agent_metrics(agent_name: str, duration: float, status: str, result: Any):
    """Log agent metrics for analysis."""
    metrics = {
        "agent": agent_name,
        "duration_seconds": duration,
        "status": status,
        "timestamp": time.time(),
        "confidence": result.get("triage_confidence") or result.get("investigation_confidence") or result.get("decision_confidence")
    }
    
    # In production, send to monitoring service
    # For now, just log to file
    with open("agent_metrics.jsonl", "a") as f:
        f.write(json.dumps(metrics) + "\n")
```

### Step 6.2: Cost Tracking

Add to `backend/agents/config.py`:

```python
# Cost per 1K tokens (approximate)
COST_GPT4_INPUT = 0.03
COST_GPT4_OUTPUT = 0.06
COST_GPT35_INPUT = 0.0015
COST_GPT35_OUTPUT = 0.002

def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate API cost for a request."""
    if "gpt-4" in model:
        return (input_tokens / 1000 * COST_GPT4_INPUT + 
                output_tokens / 1000 * COST_GPT4_OUTPUT)
    else:
        return (input_tokens / 1000 * COST_GPT35_INPUT + 
                output_tokens / 1000 * COST_GPT35_OUTPUT)
```

## Summary

This implementation guide provides:

1. ✅ **Configuration** - Environment setup and feature flags
2. ✅ **LLM-Powered Triage** - Intelligent classification with reasoning
3. ✅ **ReAct Investigator** - Dynamic tool selection
4. ✅ **LLM Decision Agent** - Nuanced decision-making with rule validation
5. ✅ **Testing** - Comprehensive test suite
6. ✅ **Monitoring** - Performance tracking and cost estimation

## Next Steps

1. Set up OpenAI API key in `.env`
2. Enable one agent at a time (start with triage)
3. Test thoroughly before enabling next agent
4. Monitor costs and performance
5. Iterate based on results

## Rollback Plan

If issues occur:
1. Set `ENABLE_REACT_*=false` in `.env`
2. System falls back to rule-based agents
3. No data loss or system downtime

---

**Made with Bob - ReAct Implementation Guide**