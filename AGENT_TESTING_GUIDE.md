# 🧪 Agent Testing Guide - Dispute Management System

**Complete Testing Scenarios for Validating Agentic AI Dispute Resolution**

This guide provides step-by-step testing scenarios to validate that your multi-agent system (Triage → Investigator → Decision) correctly handles all dispute types according to UC4 requirements.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Testing Framework](#testing-framework)
3. [Scenario 1: Fraudulent Transaction (Auto-Decision)](#scenario-1-fraudulent-transaction-auto-decision)
4. [Scenario 2: Merchant Dispute - Item Not Delivered (Human-in-Loop)](#scenario-2-merchant-dispute---item-not-delivered-human-in-loop)
5. [Scenario 3: ATM Dispute - Cash Not Dispensed](#scenario-3-atm-dispute---cash-not-dispensed)
6. [Scenario 4: Duplicate Transaction](#scenario-4-duplicate-transaction)
7. [Scenario 5: Incorrect Amount - Overcharged](#scenario-5-incorrect-amount---overcharged)
8. [Scenario 6: Subscription Dispute - Unauthorized Recurring Charge](#scenario-6-subscription-dispute---unauthorized-recurring-charge)
9. [Scenario 7: Loan/EMI Dispute](#scenario-7-loanemi-dispute)
10. [Scenario 8: Refund Not Received](#scenario-8-refund-not-received)
11. [Scenario 9: Quality/Service Dispute](#scenario-9-qualityservice-dispute)
12. [Scenario 10: Chargeback Scenario](#scenario-10-chargeback-scenario)
13. [Validation Checklist](#validation-checklist)
14. [Expected Agent Behaviors](#expected-agent-behaviors)

---

## Prerequisites

### 1. Start All Servers
```bash
# Run the cluster
start_cluster.bat

# Verify all servers are running
netstat -an | findstr "8001 8002 8003 8000 3000"
```

### 2. Access Points
- **Frontend UI:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### 3. Test Data Setup
```bash
# Seed the database with test data
cd backend
python seed_data.py
```

---

## 📝 Quick Reference: Test Transaction IDs

After running `python seed_data.py`, use these transaction IDs for testing:

| Scenario | Transaction ID | Customer ID | Customer Name | Merchant | Amount |
|----------|---------------|-------------|---------------|----------|--------|
| **1. Fraudulent (International)** | 13 | 1 | Priya Sharma | Harrods Department Store | $250.00 |
| **2. Merchant Dispute (Amazon)** | 14 | 2 | Rahul Verma | Amazon India | $799.99 |
| **2b. High-Risk Merchant** | 46 | 2 | Rahul Verma | ShopXYZ Online | $150.00 |
| **3. ATM Fault** | 15 | 3 | Ananya Patel | ATM Withdrawal | $100.00 |
| **3b. ATM Success** | 16 | 3 | Ananya Patel | ATM Withdrawal | $50.00 |
| **4. Duplicate Transaction** | 17-18 | 4 | Vikram Singh | Taj Restaurant | $25.00 |
| **5. Incorrect Amount** | 19 | 6 | Karthik Menon | Electronics Store | $50.00 |
| **6. Subscription (Netflix)** | 32 | 5 | Meera Reddy | Netflix | $15.99 |
| **6b. Active Subscription (Spotify)** | 33-44 | 4 | Vikram Singh | Spotify | $10.99 |
| **7. EMI Overcharge** | 45 | 4 | Vikram Singh | Loan EMI Payment | $1500.00 |
| **8. Refund Not Received** | 33 | 5 | Meera Reddy | Fashion Store | $35.00 |
| **9. Quality Dispute** | 34 | 6 | Karthik Menon | Electronics Mart | $250.00 |
| **10. Chargeback** | 35 | 1 | Priya Sharma | Online Gadgets | $180.00 |

### Available Banking Tools

The system provides these tools for investigation and resolution:

**Investigation Tools:**
- `get_transaction_details(transaction_id)` - Get complete transaction info
- `get_customer_history(customer_id, limit=5)` - Check spending patterns
- `check_atm_logs(transaction_id)` - Verify ATM dispense status
- `check_duplicate_transactions(customer_id, merchant, amount, date, hours)` - Find duplicates
- `get_loan_details(customer_id)` - Check EMI amounts and loan info
- `check_merchant_refund_status(transaction_id)` - Verify refund status
- `verify_receipt_amount(transaction_id, claimed_amount)` - Compare receipt vs ledger
- `analyze_receipt_evidence(receipt_base64, merchant)` - OCR receipt analysis
- `calculate_timeline_from_evidence(transaction_id, evidence_base64)` - Extract return dates

**Action Tools:**
- `initiate_refund(transaction_id, amount, reason)` - Process refunds
- `block_card(customer_id, reason)` - Block fraudulent cards
- `issue_replacement_card(customer_id, expedited)` - Issue new cards
- `initiate_chargeback(transaction_id, amount, code, notes)` - Start chargeback
- `route_to_human(ticket_id, summary)` - Escalate to human review

---

## Testing Framework

### How to Test Each Scenario

**Method 1: Via Frontend UI**
1. Navigate to http://localhost:3000
2. Click "Create New Dispute"
3. Fill in the form with scenario details
4. Submit and observe agent workflow

**Method 2: Via API (Postman/curl)**
```bash
curl -X POST http://localhost:8000/disputes \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": 1,
    "customer_id": 1,
    "category": "fraudulent_transaction",
    "description": "I did not make this transaction"
  }'
```

**Method 3: Via Python Script**
```python
import requests

response = requests.post(
    "http://localhost:8000/disputes",
    json={
        "transaction_id": 1,
        "customer_id": 1,
        "category": "fraudulent_transaction",
        "description": "I did not make this transaction"
    }
)
print(response.json())
```

### What to Observe

For each test, monitor:
1. **Triage Agent:** Category classification, confidence score
2. **Investigator Agent:** Tools called, evidence gathered
3. **Decision Agent:** Final decision, reasoning, actions taken
4. **Audit Trail:** Complete step-by-step trace in database
5. **Explainability:** Clear reasoning for each decision

---

## Scenario 1: Fraudulent Transaction (Auto-Decision)

### 🎯 Objective
Validate that the system automatically detects and approves obvious fraud cases without human intervention.

### Test Case 1.1: International Transaction (High Risk)

**Input:**
```json
{
  "transaction_id": 13,
  "customer_id": 1,
  "category": "fraudulent_transaction",
  "description": "$250 charge in London - I never traveled abroad",
  "additional_context": {
    "customer_location": "Mumbai, India",
    "transaction_location": "London, UK",
    "amount": 250,
    "merchant": "Harrods Department Store"
  }
}
```

**Expected Agent Behavior:**

**Triage Agent:**
- ✅ Classifies as `fraudulent_transaction`
- ✅ Confidence: >80%
- ✅ Routes to Investigator

**Investigator Agent:**
- ✅ Calls `get_transaction_details(13)`
- ✅ Calls `get_customer_history(1)`
- ✅ Calls `fraud_scorer.calculate_fraud_risk_score()`
- ✅ Detects: International transaction, no travel history
- ✅ Fraud risk score: >70 (HIGH)
- ✅ Evidence quality: HIGH
- ✅ Routes to Decision Agent

**Decision Agent:**
- ✅ Decision: **APPROVE** (refund customer)
- ✅ Actions:
  - Calls `block_card(1, "Suspected fraud")`
  - Calls `initiate_refund(13, 250, "Fraudulent transaction")`
  - Calls `issue_replacement_card(1, expedited=True)`
- ✅ Status: `resolved` (auto-decision, no human needed)
- ✅ Reasoning: "High fraud risk score (85/100). International transaction with no travel history. Card blocked and refund initiated."

**Validation:**
```sql
-- Check dispute record
SELECT * FROM dispute_tickets WHERE transaction_id = 13;
-- Should show: status='resolved', decision='approve', confidence>0.8

-- Check audit trail
SELECT * FROM audit_trail WHERE dispute_id = <dispute_id> ORDER BY timestamp;
-- Should show: triage → investigation → decision with all tool calls
```

### Test Case 1.2: Velocity Fraud (Multiple Transactions)

**Input:**
```json
{
  "transaction_id": 13,
  "customer_id": 1,
  "category": "fraudulent_transaction",
  "description": "5 transactions in 30 minutes - my card was stolen",
  "additional_context": {
    "transactions_in_hour": 5,
    "total_amount": 450,
    "locations": ["Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata"]
  }
}
```

**Expected Behavior:**
- ✅ Fraud risk score: >90 (CRITICAL)
- ✅ Velocity check fails (>3 transactions/hour)
- ✅ Geographic anomaly (impossible travel)
- ✅ Auto-approve the submitted fraudulent transaction
- ✅ Card is immediately blocked, which automatically declines the other 4 pending charges on the network

---

## Scenario 2: Merchant Dispute - Item Not Delivered (Human-in-Loop)

### 🎯 Objective
Validate that merchant disputes require human review due to insufficient clarity.

### Test Case 2.1: E-commerce Non-Delivery

**Input:**
```json
{
  "transaction_id": 14,
  "customer_id": 2,
  "category": "merchant_dispute",
  "description": "Ordered iPhone from Amazon, never received it",
  "additional_context": {
    "merchant": "Amazon India",
    "amount": 799.99,
    "order_date": "2024-01-15",
    "expected_delivery": "2024-01-20",
    "tracking_number": "TRK123456"
  }
}
```

**Expected Agent Behavior:**

**Triage Agent:**
- ✅ Classifies as `merchant_dispute`
- ✅ Confidence: 75%
- ✅ Routes to Investigator

**Investigator Agent:**
- ✅ Calls `get_transaction_details(14)`
- ✅ Calls `get_delivery_tracking_status(14, "TRK123456")`
- ✅ Calls `check_merchant_reputation_score("Amazon India")`
- ✅ Calls `get_merchant_dispute_history("Amazon India")`
- ✅ Evidence gathered:
  - Delivery status: "delivered" (conflict!)
  - Merchant reputation: 95/100 (TRUSTED)
  - Dispute history: Low (2% approval rate)
- ✅ Evidence quality: MEDIUM (conflicting evidence)
- ✅ Routes to Decision Agent

**Decision Agent:**
- ✅ Decision: **ROUTE_TO_HUMAN**
- ✅ Reasoning: "Delivery tracking shows 'delivered' but customer claims non-delivery. Trusted merchant with low dispute rate. Requires human investigation to verify delivery proof."
- ✅ Status: `pending_review`
- ✅ Actions:
  - Calls `route_to_human(dispute_id, summary)`
  - No refund initiated yet

**Validation:**
```sql
SELECT * FROM dispute_tickets WHERE transaction_id = 14;
-- Should show: status='pending_review', decision='route_to_human'
```

### Test Case 2.2: Merchant Dispute - High-Risk Merchant

**Input:**
```json
{
  "transaction_id": 46,
  "customer_id": 2,
  "category": "merchant_dispute",
  "description": "Ordered gadget, received empty box",
  "additional_context": {
    "merchant": "ShopXYZ Online",
    "amount": 150
  }
}
```

**Expected Behavior:**
- ✅ Merchant reputation: 35/100 (UNTRUSTED)
- ✅ Dispute history: 65% approval rate (HIGH)
- ✅ Recommendation: "Untrusted merchant. Approve customer dispute by default."
- ✅ Decision: **APPROVE** (favor customer)
- ✅ Actions: Initiate chargeback against merchant

---

## Scenario 3: ATM Dispute - Cash Not Dispensed

### 🎯 Objective
Validate ATM log checking and technical fault detection.

### Test Case 3.1: ATM Hardware Fault

**Input:**
```json
{
  "transaction_id": 15,
  "customer_id": 3,
  "category": "atm_dispute",
  "description": "ATM debited $100 but no cash came out",
  "additional_context": {
    "atm_id": "ATM_MUM_BKC_001",
    "amount": 100,
    "time": "2024-01-20T14:30:00Z"
  }
}
```

**Expected Agent Behavior:**

**Investigator Agent:**
- ✅ Calls `check_atm_logs(15)`
- ✅ ATM log shows: `status_code: "DISPENSE_FAULT"`, `cash_dispensed: false`
- ✅ Evidence: Clear hardware fault

**Decision Agent:**
- ✅ Decision: **APPROVE**
- ✅ Reasoning: "ATM logs confirm dispense fault. No cash dispensed."
- ✅ Actions: `initiate_refund(15, 100, "ATM hardware fault")`

### Test Case 3.2: ATM - Cash Dispensed Successfully

**Input:**
```json
{
  "transaction_id": 16,
  "customer_id": 3,
  "category": "atm_dispute",
  "description": "Claiming ATM didn't give cash",
  "additional_context": {
    "amount": 50
  }
}
```

**Expected Behavior:**
- ✅ ATM log shows: `cash_dispensed: true`, `status_code: "SUCCESS"`
- ✅ Decision: **DENY**
- ✅ Reasoning: "ATM logs confirm cash was dispensed successfully."

---

## Scenario 4: Duplicate Transaction

### 🎯 Objective
Validate duplicate transaction detection.

### Test Case 4.1: Duplicate Charge

**Input:**
```json
{
  "transaction_id": 17,
  "customer_id": 4,
  "category": "duplicate_transaction",
  "description": "Charged twice for same restaurant bill",
  "additional_context": {
    "merchant": "Taj Restaurant",
    "amount": 25,
    "date": "2024-01-20"
  }
}
```

**Expected Agent Behavior:**

**Investigator Agent:**
- ✅ Calls `check_duplicate_transactions(4, "Taj Restaurant", 25, "2024-01-20", 24)`
- ✅ Finds: 2 identical transactions within 5 minutes
- ✅ Evidence: Clear duplicate

**Decision Agent:**
- ✅ Decision: **APPROVE**
- ✅ Actions: `initiate_refund(18, 25, "Duplicate transaction")`
- ✅ Reasoning: "Found duplicate transaction for same merchant and amount within 5 minutes."

---

## Scenario 5: Incorrect Amount - Overcharged

### 🎯 Objective
Validate receipt analysis and amount verification.

### Test Case 5.1: Receipt Shows Lower Amount

**Input:**
```json
{
  "transaction_id": 19,
  "customer_id": 6,
  "category": "incorrect_amount",
  "description": "Charged $50 but receipt shows $45",
  "additional_context": {
    "merchant": "Electronics Store",
    "billed_amount": 50,
    "claimed_amount": 45,
    "receipt_image": "base64_encoded_receipt_data"
  }
}
```

**Expected Agent Behavior:**

**Investigator Agent:**
- ✅ Calls `analyze_receipt_evidence(receipt_base64, "Electronics Store")`
- ✅ OCR extracts: `amount: 45`, `merchant: "Electronics Store"`
- ✅ Calls `verify_receipt_amount(19, 45)`
- ✅ Discrepancy: $5 overcharge

**Decision Agent:**
- ✅ Decision: **APPROVE** (partial refund)
- ✅ Actions: `initiate_refund(19, 5, "Overcharged - receipt verified")`
- ✅ Reasoning: "Receipt analysis confirms customer was overcharged by $5."

---

## Scenario 6: Subscription Dispute - Unauthorized Recurring Charge

### 🎯 Objective
Validate subscription cancellation verification.

### Test Case 6.1: Cancelled Subscription Still Charging

**Input:**
```json
{
  "transaction_id": 32,
  "customer_id": 5,
  "category": "subscription_dispute",
  "description": "Cancelled Netflix in December but charged in January",
  "additional_context": {
    "merchant": "Netflix",
    "amount": 15.99,
    "cancellation_date": "2023-12-15",
    "charge_date": "2024-01-15"
  }
}
```

**Expected Agent Behavior:**

**Investigator Agent:**
- ✅ Calls `get_customer_history(5)` to check subscription pattern
- ✅ Detects: Recurring monthly subscription ($15.99)
- ✅ Analyzes: 11 months of charges, then gap, then disputed charge
- ✅ Finds: Charge occurred 31 days after claimed cancellation
- ✅ Evidence: Cancellation claim appears valid

**Decision Agent:**
- ✅ Decision: **APPROVE**
- ✅ Actions: `initiate_refund(32, 15.99, "Subscription charged after cancellation")`
- ✅ Reasoning: "Customer cancelled subscription on 2023-12-15 but was charged on 2024-01-15. Approve refund."

### Test Case 6.2: Active Subscription - No Cancellation

**Input:**
```json
{
  "transaction_id": 44,
  "customer_id": 4,
  "category": "subscription_dispute",
  "description": "I don't recognize this charge",
  "additional_context": {
    "merchant": "Spotify",
    "amount": 10.99
  }
}
```

**Expected Behavior:**
- ✅ Subscription status: Active, 12 months of charges
- ✅ No cancellation found
- ✅ Decision: **DENY** or **ROUTE_TO_HUMAN**
- ✅ Reasoning: "Active subscription with 12 months of recurring charges. No cancellation record found."

---

## Scenario 7: Loan/EMI Dispute

### 🎯 Objective
Validate loan EMI verification.

### Test Case 7.1: Incorrect EMI Amount

**Input:**
```json
{
  "transaction_id": 45,
  "customer_id": 4,
  "category": "loan_dispute",
  "subcategory": "emi_amount_error",
  "description": "Charged $1500 EMI but should be $1200",
  "additional_context": {
    "expected_emi": 1200,
    "charged_emi": 1500
  }
}
```

**Expected Agent Behavior:**

**Investigator Agent:**
- ✅ Calls `get_loan_details(4)`
- ✅ Retrieves: EMI schedule, outstanding balance
- ✅ Verifies: Actual EMI is $1200
- ✅ Discrepancy: $300 overcharge

**Decision Agent:**
- ✅ Decision: **APPROVE**
- ✅ Actions: `initiate_refund(45, 300, "EMI overcharge")`
- ✅ Reasoning: "Loan records confirm EMI should be $1200. Customer overcharged by $300."

---

## Scenario 8: Refund Not Received

### 🎯 Objective
Validate refund timeline tracking and escalation.

### Test Case 8.1: Merchant Refund Delayed

**Input:**
```json
{
  "transaction_id": 33,
  "customer_id": 5,
  "category": "refund_not_received",
  "description": "Merchant promised refund 10 days ago, still not received",
  "additional_context": {
    "merchant": "Fashion Store",
    "amount": 35,
    "refund_promised_date": "2024-01-10"
  }
}
```

**Expected Agent Behavior:**

**Investigator Agent:**
- ✅ Calls `check_merchant_refund_status(33)`
- ✅ Timeline shows: 10 days elapsed, stage: "merchant_escalation"
- ✅ Status: "pending" (merchant hasn't processed)
- ✅ Calls `calculate_timeline_from_evidence(33, evidence_base64)` if evidence provided

**Decision Agent:**
- ✅ Decision: **APPROVE** (escalate to chargeback)
- ✅ Actions: `initiate_chargeback(33, 35, "4853", "Merchant failed to refund within 7 days")`
- ✅ Reasoning: "Merchant refund delayed >7 days. Escalating to chargeback."

### Test Case 8.2: Bank Processing Delay (>14 days)

**Expected Behavior:**
- ✅ Refund timeline: 15 days elapsed
- ✅ Stage: "provisional_credit"
- ✅ Action: Issue provisional credit immediately
- ✅ Reasoning: "Investigation taking >14 days. Issuing provisional credit per policy."

---

## Scenario 9: Quality/Service Dispute

### 🎯 Objective
Validate handling of subjective disputes.

### Test Case 9.1: Product Quality Issue

**Input:**
```json
{
  "transaction_id": 34,
  "customer_id": 6,
  "category": "quality_dispute",
  "description": "Received damaged product, merchant refusing refund",
  "additional_context": {
    "merchant": "Electronics Mart",
    "amount": 250,
    "evidence": "photos_of_damage.jpg"
  }
}
```

**Expected Agent Behavior:**

**Investigator Agent:**
- ✅ Calls `get_transaction_details(34)`
- ✅ Calls `get_customer_history(6)`
- ✅ Evidence quality: MEDIUM (subjective claim)

**Decision Agent:**
- ✅ Decision: **ROUTE_TO_HUMAN**
- ✅ Reasoning: "Quality disputes require human judgment. Customer claims damage, merchant disputes. Needs manual review of evidence."
- ✅ Status: `pending_review`

---

## Scenario 10: Chargeback Scenario

### 🎯 Objective
Validate chargeback initiation for merchant disputes.

### Test Case 10.1: Merchant Non-Response

**Input:**
```json
{
  "transaction_id": 35,
  "customer_id": 1,
  "category": "merchant_dispute",
  "description": "Merchant not responding to refund request for 15 days",
  "additional_context": {
    "merchant": "Online Gadgets",
    "amount": 180,
    "days_elapsed": 15
  }
}
```

**Expected Agent Behavior:**

**Decision Agent:**
- ✅ Decision: **APPROVE** (chargeback)
- ✅ Actions: `initiate_chargeback(35, 180, "4855", "Merchant non-response >14 days")`
- ✅ Reasoning: "Merchant failed to respond within 14 days. Initiating chargeback per policy."

---

## Validation Checklist

### ✅ Triage Agent Validation

- [ ] Correctly classifies all dispute categories
- [ ] Confidence scores are reasonable (>70% for clear cases)
- [ ] Routes to investigator for all cases
- [ ] Handles ambiguous descriptions (asks clarifying questions)

### ✅ Investigator Agent Validation

- [ ] Calls appropriate tools for each category:
  - `get_transaction_details()` - Get transaction info
  - `get_customer_history()` - Check spending patterns
  - `check_atm_logs()` - Verify ATM dispense status
  - `check_duplicate_transactions()` - Find duplicates
  - `get_loan_details()` - Check EMI amounts
  - `check_merchant_refund_status()` - Verify refund status
  - `verify_receipt_amount()` - Compare receipt vs ledger
  - `analyze_receipt_evidence()` - OCR receipt analysis
  - `calculate_timeline_from_evidence()` - Extract return dates
- [ ] Gathers sufficient evidence before decision
- [ ] Uses fraud scorer for fraud cases
- [ ] Uses ATM logs for ATM disputes
- [ ] Calculates evidence quality score
- [ ] Routes to decision agent with complete context

### ✅ Decision Agent Validation

- [ ] Makes correct approve/deny decisions
- [ ] Routes to human when evidence is insufficient
- [ ] Executes appropriate actions:
  - `initiate_refund()` - Process refunds
  - `block_card()` - Block fraudulent cards
  - `issue_replacement_card()` - Issue new cards
  - `initiate_chargeback()` - Start chargeback process
  - `route_to_human()` - Escalate to human review
- [ ] Provides clear reasoning for all decisions
- [ ] Respects confidence thresholds
- [ ] Handles edge cases gracefully

### ✅ Orchestration Validation

- [ ] Agents execute in correct order (Triage → Investigator → Decision)
- [ ] State is maintained across agent transitions
- [ ] Confidence calibration works correctly
- [ ] Evidence quality scoring influences decisions
- [ ] Re-investigation triggers work when evidence is poor

### ✅ Compliance & Governance

- [ ] All decisions have audit trail
- [ ] PII is masked in logs
- [ ] Explainability is clear and understandable
- [ ] Compliance policies are checked
- [ ] Human-in-loop works for ambiguous cases

---

## Expected Agent Behaviors

### Auto-Decision Scenarios (No Human Needed)

**Should Auto-Approve:**
1. ✅ Fraudulent transactions with high risk score (>70)
2. ✅ ATM faults confirmed by logs
3. ✅ Duplicate transactions detected
4. ✅ Incorrect amounts verified by receipt
5. ✅ Subscription charges after verified cancellation
6. ✅ Merchant refund delays >7 days
7. ✅ Loan EMI errors confirmed by records

**Should Auto-Deny:**
1. ✅ ATM logs show cash dispensed
2. ✅ No duplicate found
3. ✅ Receipt matches billed amount
4. ✅ Active subscription with no cancellation
5. ✅ Fraud risk score <30 (legitimate transaction)

### Human-in-Loop Scenarios

**Should Route to Human:**
1. ✅ Merchant disputes with conflicting evidence
2. ✅ Quality/service disputes (subjective)
3. ✅ Insufficient evidence to make decision
4. ✅ Confidence score <60%
5. ✅ Evidence quality score <0.5
6. ✅ High-value disputes (>$10,000)
7. ✅ Complex multi-party disputes

---

## Performance Metrics to Track

### Agent Performance
- **Triage Accuracy:** >90% correct classification
- **Investigation Completeness:** >85% evidence gathered
- **Decision Accuracy:** >95% correct decisions
- **Auto-Resolution Rate:** >70% (no human needed)
- **Average Resolution Time:** <5 minutes for auto-decisions

### System Performance
- **Fraud Detection Rate:** >95% catch rate
- **False Positive Rate:** <5%
- **Customer Satisfaction:** >85% (post-resolution survey)
- **Compliance Score:** 100% (all decisions auditable)

---

## Troubleshooting

### If Agents Don't Call Expected Tools

**Check:**
1. Tool descriptions in `mcp_client.py`
2. Agent prompts in `agents/` directory
3. LangGraph routing logic in `orchestrator.py`
4. MCP server logs for errors

### If Decisions Are Incorrect

**Check:**
1. Confidence thresholds in `agents/config.py`
2. Evidence quality scoring in `evidence_scorer.py`
3. Fraud risk scoring in `fraud_scorer.py`
4. Decision logic in `agents/decision.py`

### If Audit Trail Is Incomplete

**Check:**
1. State management in `agents/state.py`
2. Database writes in `main.py`
3. Audit trail table schema

---

## 🎯 Success Criteria

Your system passes testing if:

1. ✅ **All 10 scenarios execute successfully**
2. ✅ **Agents call appropriate tools for each category**
3. ✅ **Decisions match expected outcomes**
4. ✅ **Audit trail is complete and explainable**
5. ✅ **Auto-decision rate >70%**
6. ✅ **Human-in-loop triggers correctly**
7. ✅ **Fraud detection works accurately**
8. ✅ **Compliance policies are enforced**
9. ✅ **PII is masked in all logs**
10. ✅ **System handles edge cases gracefully**

---

## 📊 Test Results Template

```markdown
# Test Results - [Date]

## Scenario 1: Fraudulent Transaction
- Status: ✅ PASS / ❌ FAIL
- Triage: Correct classification
- Investigation: Tools called correctly
- Decision: Auto-approved
- Notes: [Any observations]

## Scenario 2: Merchant Dispute
- Status: ✅ PASS / ❌ FAIL
- Triage: Correct classification
- Investigation: Delivery tracking used
- Decision: Routed to human
- Notes: [Any observations]

[Continue for all scenarios...]

## Overall Results
- Total Scenarios: 10
- Passed: X
- Failed: Y
- Pass Rate: Z%
```

---

## 🚀 Next Steps After Testing

1. **Fix any failing scenarios**
2. **Tune confidence thresholds** based on results
3. **Adjust agent prompts** for better tool selection
4. **Optimize evidence scoring** for edge cases
5. **Deploy to staging** for pilot testing
6. **Monitor production metrics**
7. **Iterate based on real-world feedback**

---

**Your Agentic AI Dispute Management System is now ready for comprehensive testing!** 🎉

Use this guide to systematically validate all agent behaviors and ensure production readiness.