# Banking Tools Documentation

## Overview

The `banking_tools.py` module provides a comprehensive set of tools for AI agents to interact with the banking dispute management system. Each function is designed to return structured data that agents can use for decision-making in the ReAct framework.

## ✅ All Functions Tested and Working

### Test Results Summary

All 7 banking tools have been successfully tested with the seeded database:

1. ✅ **get_transaction_details()** - Retrieves complete transaction information
2. ✅ **get_customer_history()** - Returns transaction history for context
3. ✅ **check_atm_logs()** - Verifies ATM hardware status
4. ✅ **check_duplicate_transactions()** - Detects duplicate charges
5. ✅ **block_card()** - Simulates card blocking for fraud prevention
6. ✅ **initiate_refund()** - Simulates refund processing
7. ✅ **route_to_human()** - Routes tickets to human review

---

## Function Reference

### 1. get_transaction_details(transaction_id: int)

**Purpose:** Retrieve complete details for a specific transaction.

**When to Use:**
- At the start of investigating any dispute
- To understand the transaction context
- To verify transaction status and type

**Parameters:**
- `transaction_id` (int): The unique identifier of the transaction

**Returns:**
```python
{
    "transaction_id": 1,
    "customer_id": 2,
    "customer_name": "Sarah Johnson",
    "account_tier": "Gold",
    "amount": 8500.0,
    "merchant_name": "Luxury Watches International",
    "transaction_date": "2026-04-06T06:04:43.433069",
    "status": "success",
    "is_international": true
}
```

**Error Handling:** Returns `{"error": "Transaction ID X not found"}` if not found.

---

### 2. get_customer_history(customer_id: int, limit: int = 5)

**Purpose:** Retrieve transaction history for understanding spending patterns.

**When to Use:**
- To detect unusual spending patterns
- To check if international transactions are typical for the customer
- To identify potential fraud patterns
- To understand customer's typical merchant preferences

**Parameters:**
- `customer_id` (int): The unique identifier of the customer
- `limit` (int, optional): Number of transactions to retrieve (default: 5)

**Returns:**
```python
{
    "customer_id": 4,
    "customer_name": "Emily Rodriguez",
    "account_tier": "Premium",
    "average_monthly_balance": 22000.0,
    "transaction_count": 2,
    "transactions": [
        {
            "transaction_id": 5,
            "amount": 89.99,
            "merchant_name": "Coffee Shop Downtown",
            "transaction_date": "2026-04-09T18:37:43.433069",
            "status": "success",
            "is_international": false
        }
    ]
}
```

**Use Case Examples:**
- **Fraud Detection:** Check if international transactions are unusual
- **Duplicate Detection:** Verify typical merchant patterns
- **Risk Assessment:** Analyze spending behavior vs account tier

---

### 3. check_atm_logs(transaction_id: int)

**Purpose:** Query ATM logs to verify hardware status and cash dispensing.

**When to Use:**
- For ANY ATM-related dispute
- When transaction status is "failed" for ATM withdrawal
- To verify if cash was actually dispensed

**Parameters:**
- `transaction_id` (int): The unique identifier of the transaction

**Returns:**
```python
{
    "transaction_id": 6,
    "atm_log_found": true,
    "atm_logs": [
        {
            "log_id": 1,
            "atm_id": "ATM_NYC_5TH_AVE_001",
            "status_code": "500_HARDWARE_FAULT"
        }
    ],
    "has_hardware_fault": true,
    "has_successful_dispense": false,
    "message": "ATM hardware fault detected. Cash was likely not dispensed."
}
```

**Decision Logic:**
- If `has_hardware_fault = true` → **Auto-approve refund**
- If `has_successful_dispense = true` → **Investigate further or deny**
- If `atm_log_found = false` → **Route to human review**

---

### 4. check_duplicate_transactions(customer_id, merchant_name, amount, date, time_window_hours=24)

**Purpose:** Detect duplicate charges within a time window.

**When to Use:**
- When customer reports duplicate charges
- For any transaction where timing seems suspicious
- To verify if multiple identical transactions exist

**Parameters:**
- `customer_id` (int): Customer identifier
- `merchant_name` (str): Merchant name to search for
- `amount` (float): Transaction amount to match
- `date` (datetime): Reference date for search window
- `time_window_hours` (int, optional): Hours to search (default: 24)

**Returns:**
```python
{
    "customer_id": 4,
    "merchant_name": "Coffee Shop Downtown",
    "amount": 89.99,
    "duplicates_found": true,
    "duplicate_count": 2,
    "transactions": [
        {
            "transaction_id": 4,
            "amount": 89.99,
            "transaction_date": "2026-04-09T18:34:43",
            "time_difference_minutes": 3.0
        }
    ],
    "message": "Found 2 transactions to Coffee Shop Downtown for $89.99 within 3.0 minutes. Likely duplicate charge."
}
```

**Decision Logic:**
- If duplicates within < 5 minutes → **High confidence duplicate, approve refund for one**
- If duplicates within < 1 hour → **Medium confidence, investigate merchant**
- If duplicates spread over hours → **May be legitimate multiple purchases**

---

### 5. block_card(customer_id: int, reason: str = "Suspected fraud")

**Purpose:** Block a customer's card for security (dummy function).

**When to Use:**
- When fraud is highly suspected
- For high-value unauthorized international transactions
- When multiple suspicious transactions are detected
- Before escalating to human review for security

**Parameters:**
- `customer_id` (int): Customer whose card should be blocked
- `reason` (str, optional): Reason for blocking

**Returns:**
```python
{
    "status": "success",
    "customer_id": 2,
    "customer_name": "Sarah Johnson",
    "action": "card_blocked",
    "reason": "High-value international transaction without travel notice",
    "timestamp": "2026-04-13T04:10:00.483209",
    "message": "Card for customer 2 (Sarah Johnson) has been blocked successfully."
}
```

**Important:** This is a protective action. Always block card before approving refund for suspected fraud.

---

### 6. initiate_refund(transaction_id: int, amount: float, reason: str = "Approved dispute")

**Purpose:** Initiate a refund for a disputed transaction (dummy function).

**When to Use:**
- When evidence clearly supports customer claim
- After ATM hardware fault is confirmed
- For confirmed duplicate charges
- After blocking card for fraud (if applicable)

**Parameters:**
- `transaction_id` (int): Transaction to refund
- `amount` (float): Amount to refund (can be partial)
- `reason` (str, optional): Reason for refund

**Returns:**
```python
{
    "status": "success",
    "transaction_id": 2,
    "customer_id": 3,
    "merchant_name": "Electronics Store",
    "original_amount": 450.0,
    "refund_amount": 450.0,
    "reason": "Failed transaction with amount deducted",
    "timestamp": "2026-04-13T04:10:00.490672",
    "estimated_processing_days": 3,
    "message": "Refund of $450.00 initiated successfully for transaction 2..."
}
```

**Validation:** Function automatically validates that refund amount doesn't exceed transaction amount.

---

### 7. route_to_human(ticket_id: int, summary: str)

**Purpose:** Route a dispute ticket to human review.

**When to Use:**
- When automated decision confidence is low
- For complex cases requiring judgment
- When policy exceptions might apply
- For high-value disputes with unclear evidence
- When customer is VIP/Gold tier with significant history

**Parameters:**
- `ticket_id` (int): Dispute ticket identifier
- `summary` (str): Explanation of why human review is needed

**Returns:**
```python
{
    "status": "success",
    "ticket_id": 1,
    "transaction_id": 1,
    "customer_id": 2,
    "previous_status": "open",
    "new_status": "human_review_required",
    "summary": "High-value international transaction ($8,500)...",
    "timestamp": "2026-04-13T04:10:00.525287",
    "message": "Ticket 1 has been routed to human review. Previous status: open"
}
```

**Best Practices:** 
- Provide detailed summary including key findings
- Mention specific concerns or ambiguities
- Include customer tier and risk factors
- Note any protective actions already taken (e.g., card blocked)

---

## ReAct Agent Usage Patterns

### Pattern 1: ATM Dispute Resolution

```
Thought: Customer claims ATM didn't dispense cash. Need to verify ATM logs.
Action: check_atm_logs(transaction_id=6)
Observation: ATM log shows 500_HARDWARE_FAULT. Cash was not dispensed.
Thought: Hardware fault confirms customer's claim. Refund is justified.
Action: initiate_refund(transaction_id=6, amount=200.00, reason="ATM hardware fault confirmed")
Decision: Auto-approve refund
```

### Pattern 2: Duplicate Charge Detection

```
Thought: Customer reports duplicate charge. Need to verify.
Action: get_transaction_details(transaction_id=5)
Observation: Transaction at Coffee Shop Downtown for $89.99
Action: check_duplicate_transactions(customer_id=4, merchant="Coffee Shop Downtown", amount=89.99, date=trans_date)
Observation: Found 2 identical transactions 3 minutes apart
Thought: Clear duplicate charge. Refund second transaction.
Action: initiate_refund(transaction_id=5, amount=89.99, reason="Duplicate charge detected")
Decision: Auto-approve refund
```

### Pattern 3: Fraud Investigation

```
Thought: High-value international transaction. Need to check customer patterns.
Action: get_transaction_details(transaction_id=1)
Observation: $8,500 international transaction to Luxury Watches International
Action: get_customer_history(customer_id=2)
Observation: No prior international transactions in recent history
Thought: Unusual pattern. Customer claims unauthorized. Low confidence.
Action: block_card(customer_id=2, reason="Suspected fraud - unusual international transaction")
Action: route_to_human(ticket_id=1, summary="High-value international with no prior history...")
Decision: Human review required
```

### Pattern 4: Failed Transaction Analysis

```
Thought: Transaction shows failed but amount deducted. Check transaction details.
Action: get_transaction_details(transaction_id=2)
Observation: Status=failed, amount=$450 to Electronics Store
Thought: Failed transaction should not deduct funds. Customer entitled to refund.
Action: initiate_refund(transaction_id=2, amount=450.00, reason="Failed transaction with amount deducted")
Decision: Auto-approve refund
```

---

## Error Handling

All functions include error handling for:
- ❌ Non-existent IDs (transactions, customers, tickets)
- ❌ Invalid amounts (refunds exceeding transaction amount)
- ❌ Database connection issues (automatic cleanup)

Agents should check for `"error"` key in responses and handle accordingly.

---

## Testing

Run the comprehensive test suite:
```bash
python test_banking_tools.py
```

This tests all functions with the seeded data and verifies:
- ✅ Successful operations
- ✅ Error handling
- ✅ Data validation
- ✅ Edge cases

---

## Next Steps for AI Agent Development

1. **Create ReAct Agent Framework**
   - Implement Thought-Action-Observation loop
   - Integrate with LLM (OpenAI GPT-4, Anthropic Claude, etc.)
   - Add tool selection logic

2. **Create Specialized Agents**
   - FraudDetectionAgent
   - ATMDisputeAgent
   - DuplicateChargeAgent
   - MerchantDisputeAgent
   - OrchestratorAgent

3. **Add Audit Logging**
   - Log all agent thoughts, actions, and observations to AuditLog table
   - Track decision-making process for transparency

4. **Create Agent Communication**
   - Multi-agent coordination
   - Agent handoffs based on dispute type
   - Consensus mechanisms for complex cases

---

## Function Summary Table

| Function | Purpose | Auto-Resolve Capable | Typical Use Case |
|----------|---------|---------------------|------------------|
| get_transaction_details | Info retrieval | No | Always first step |
| get_customer_history | Pattern analysis | No | Fraud detection |
| check_atm_logs | ATM verification | Yes | ATM disputes |
| check_duplicate_transactions | Duplicate detection | Yes | Duplicate charges |
| block_card | Fraud prevention | N/A | Suspected fraud |
| initiate_refund | Resolution action | N/A | Approved disputes |
| route_to_human | Escalation | N/A | Complex/unclear cases |

---

## Notes

- All dummy functions (block_card, initiate_refund) simulate real operations
- In production, these would integrate with actual banking APIs
- All functions return structured dictionaries for easy parsing by LLMs
- Google-style docstrings enable LLMs to understand tool capabilities
- Functions are designed to be called by ReAct agents in any order as needed