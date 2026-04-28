# Sample Receipt Images for GPT-4o Vision Testing

This directory contains realistic receipt images for testing the `analyze_receipt_evidence` tool with GPT-4o Vision.

## 6-Customer Test Scenario Receipts

These receipts correspond to the streamlined 6-customer test scenarios in `seed_data.py`:

### Scenario 2: Merchant Dispute - Item Not Delivered

#### `receipt_scenario2_amazon_iphone.png`
- **Customer:** Rahul Verma (Customer 2)
- **Merchant:** Amazon India
- **Amount Charged:** $799.99
- **Amount on Receipt:** $799.99 (matches)
- **Issue:** iPhone 15 Pro not delivered
- **Use Case:** Test merchant dispute with trusted merchant (Amazon)

#### `receipt_scenario2b_shopxyz_empty_box.png`
- **Customer:** Rahul Verma (Customer 2)
- **Merchant:** ShopXYZ Online (HIGH-RISK MERCHANT)
- **Amount Charged:** $150.00
- **Amount on Receipt:** $150.00 (matches)
- **Issue:** Received empty box instead of gaming laptop
- **Use Case:** Test merchant dispute with high-risk merchant (86.7% approval rate from 15 historic disputes)

### Scenario 4: Duplicate Transaction

#### `receipt_scenario4_taj_restaurant_duplicate.png`
- **Customer:** Vikram Singh (Customer 4)
- **Merchant:** Taj Restaurant
- **Amount Charged:** $25.00 (charged twice within 5 minutes)
- **Amount on Receipt:** $24.81
- **Issue:** Duplicate charge for same meal
- **Use Case:** Test duplicate transaction detection

### Scenario 5: Incorrect Amount - Overcharged

#### `receipt_scenario5_electronics_store_overcharged.png`
- **Customer:** Karthik Menon (Customer 6)
- **Merchant:** Electronics Store
- **Amount Charged:** $50.00
- **Amount on Receipt:** $45.00
- **Discrepancy:** Customer overcharged by $5.00
- **Use Case:** Test receipt analysis for amount verification

### Scenario 8: Refund Not Received

#### `receipt_scenario8_fashion_store_refund.png`
- **Customer:** Meera Reddy (Customer 5)
- **Merchant:** Fashion Store
- **Amount Charged:** $35.00
- **Amount on Receipt:** $32.38
- **Issue:** Merchant promised refund 10 days ago, not received
- **Use Case:** Test refund timeline tracking and escalation

### Scenario 9: Quality/Service Dispute

#### `receipt_scenario9_electronics_mart_damaged.png`
- **Customer:** Karthik Menon (Customer 6)
- **Merchant:** Electronics Mart
- **Amount Charged:** $250.00
- **Amount on Receipt:** $237.58
- **Issue:** Received damaged product, merchant refusing refund
- **Use Case:** Test subjective quality disputes requiring human review

---

## Legacy Receipts (Original Test Data)

### `receipt_incorrect_amount_overcharged.png`
**Scenario:** Incorrect Amount Dispute - Customer Overcharged
- **Transaction:** John Smith - TechGadgets Online
- **Amount Charged:** $299.99
- **Amount on Receipt:** $103.96
- **Discrepancy:** Customer was charged $196.03 MORE than the receipt shows
- **Use Case:** Test detection of overcharging fraud

### `receipt_incorrect_amount_undercharged.png`
**Scenario:** Incorrect Amount Dispute - Suspicious Undercharge
- **Transaction:** Emily Rodriguez - Coffee Shop Downtown
- **Amount Charged:** $89.99
- **Amount on Receipt:** $19.50
- **Discrepancy:** Customer was charged $70.49 MORE than receipt shows
- **Use Case:** Test detection of receipt tampering or wrong receipt submission

### `receipt_merchant_dispute.png`
**Scenario:** Merchant Dispute - Wrong Merchant Name
- **Transaction:** Sarah Johnson - Luxury Watches International
- **Amount Charged:** $8,500.00
- **Merchant on Receipt:** Budget Electronics Outlet
- **Amount on Receipt:** $1,350.00
- **Discrepancy:** Completely different merchant and amount
- **Use Case:** Test detection of fraudulent transactions or identity theft

### `receipt_valid_match.png`
**Scenario:** Valid Receipt - Should Match Transaction
- **Transaction:** Michael Chen - Electronics Store
- **Amount Charged:** $450.00
- **Amount on Receipt:** $287.24 (calculated with tax)
- **Use Case:** Test that legitimate receipts are properly validated

---

## How to Use These Receipts

### Method 1: Convert to Base64 for API Testing

```python
import base64

# Read and encode the receipt
with open('sample_receipts/receipt_scenario5_electronics_store_overcharged.png', 'rb') as f:
    image_data = f.read()
    base64_str = base64.b64encode(image_data).decode('utf-8')

# Now you can pass base64_str to the analyze_receipt_evidence function
```

### Method 2: Use the Test Script

Run the automated test script:

```bash
python test_receipt_vision.py
```

This will test all receipts sequentially and show the GPT-4o Vision analysis results.

### Method 3: Manual Testing via MCP Server

1. Start the MCP server:
   ```bash
   python backend/mcp_servers/core_banking_server.py
   ```

2. Call the `analyze_receipt_evidence_tool` with the Base64-encoded receipt

### Method 4: Test Through the Full Dispute Flow

1. Create a dispute ticket for one of the transactions
2. Upload the corresponding receipt image
3. The Investigator agent will automatically call the vision tool
4. Review the analysis in the ticket resolution notes

---

## Expected GPT-4o Vision Output

The tool should return JSON with:

```json
{
    "extracted_merchant": "Merchant name from receipt",
    "extracted_amount": "123.45",
    "receipt_legibility": "High|Medium|Low",
    "fraud_indicators_found": true/false,
    "note": "Explanation of findings"
}
```

---

## Testing Scenarios

### ✅ Successful Detection Cases
- **Overcharging:** Scenario 5 receipt should detect $5.00 discrepancy
- **Merchant Mismatch:** Legacy receipt #3 should flag different merchant name
- **Valid Receipt:** Scenario 2 (Amazon) should validate as legitimate
- **High-Risk Merchant:** Scenario 2B should flag ShopXYZ as high-risk

### ⚠️ Edge Cases to Test
- **Receipt Tampering:** Legacy receipt #2 (suspicious low amount)
- **Partial Refunds:** Scenario 8 (refund not received)
- **Quality Issues:** Scenario 9 (damaged product - subjective)
- **Duplicate Charges:** Scenario 4 (same receipt, charged twice)

---

## Regenerating Receipts

To regenerate the 6-customer test scenario receipts:

```bash
python generate_test_receipts.py
```

To regenerate legacy receipts:

```bash
python generate_sample_receipts.py
```

Edit the respective script to customize:
- Merchant names
- Item lists
- Amounts
- Dates
- Receipt formatting

---

## Integration with Dispute System

### 6-Customer Test Scenarios

| Receipt File | Scenario | Customer | Transaction ID* | Merchant | Amount |
|-------------|----------|----------|----------------|----------|--------|
| receipt_scenario2_amazon_iphone.png | 2 | Rahul Verma | ~15 | Amazon India | $799.99 |
| receipt_scenario2b_shopxyz_empty_box.png | 2B | Rahul Verma | ~40 | ShopXYZ Online | $150.00 |
| receipt_scenario4_taj_restaurant_duplicate.png | 4 | Vikram Singh | ~20-21 | Taj Restaurant | $25.00 |
| receipt_scenario5_electronics_store_overcharged.png | 5 | Karthik Menon | ~22 | Electronics Store | $50.00 |
| receipt_scenario8_fashion_store_refund.png | 8 | Meera Reddy | ~35 | Fashion Store | $35.00 |
| receipt_scenario9_electronics_mart_damaged.png | 9 | Karthik Menon | ~37 | Electronics Mart | $250.00 |

*Transaction IDs are approximate and depend on seed order. Run `python backend/seed_data.py` and check the summary output for exact IDs.

### Legacy Receipts

| Receipt File | Transaction ID | Customer | Merchant | Amount |
|-------------|----------------|----------|----------|--------|
| receipt_incorrect_amount_overcharged.png | 3 | John Smith | TechGadgets Online | $299.99 |
| receipt_incorrect_amount_undercharged.png | 4 | Emily Rodriguez | Coffee Shop Downtown | $89.99 |
| receipt_merchant_dispute.png | 1 | Sarah Johnson | Luxury Watches International | $8,500.00 |
| receipt_valid_match.png | 2 | Michael Chen | Electronics Store | $450.00 |

---

## Notes

- All receipts are generated programmatically using PIL (Pillow)
- Receipt format mimics real-world retail receipts
- Amounts include 8% sales tax calculation
- Images are 400x600 pixels, optimized for OCR
- Font: Arial (fallback to default if unavailable)

---

## Troubleshooting

**Issue:** GPT-4o returns error
- Check that your OpenAI API key is set in `.env`
- Verify the API key has access to GPT-4o Vision
- Ensure the Base64 string includes the data URI prefix

**Issue:** Poor OCR accuracy
- Increase image resolution in the generation script
- Use higher quality fonts
- Ensure good contrast (black text on white background)

**Issue:** Receipt not matching transaction
- Verify you're using the correct receipt for the transaction
- Check the transaction ID mapping in the tables above
- Run `python backend/seed_data.py` to see exact transaction IDs

---

## Quick Reference: Which Receipt for Which Test?

| Test Scenario | Receipt to Upload | Expected Outcome |
|--------------|-------------------|------------------|
| Scenario 1: Fraud (International) | None needed | Auto-approve based on fraud score |
| Scenario 2: Amazon dispute | receipt_scenario2_amazon_iphone.png | Route to human (trusted merchant) |
| Scenario 2B: ShopXYZ dispute | receipt_scenario2b_shopxyz_empty_box.png | Auto-approve (high-risk merchant) |
| Scenario 3: ATM fault | None needed | Auto-approve based on ATM logs |
| Scenario 4: Duplicate | receipt_scenario4_taj_restaurant_duplicate.png | Auto-approve (duplicate detected) |
| Scenario 5: Overcharged | receipt_scenario5_electronics_store_overcharged.png | Auto-approve $5 refund |
| Scenario 6: Subscription | None needed | Auto-approve based on cancellation |
| Scenario 7: EMI dispute | None needed | Auto-approve based on loan records |
| Scenario 8: Refund delay | receipt_scenario8_fashion_store_refund.png | Escalate to chargeback |
| Scenario 9: Quality issue | receipt_scenario9_electronics_mart_damaged.png | Route to human (subjective) |
| Scenario 10: Chargeback | None needed | Initiate chargeback |

---

**Generated with ❤️ for comprehensive dispute testing!**