# Sample Receipt Images for GPT-4o Vision Testing

This directory contains realistic receipt images for testing the `analyze_receipt_evidence` tool with GPT-4o Vision.

## Generated Receipts

### 1. `receipt_incorrect_amount_overcharged.png`
**Scenario:** Incorrect Amount Dispute - Customer Overcharged
- **Transaction:** John Smith - TechGadgets Online
- **Amount Charged:** $299.99
- **Amount on Receipt:** $103.96
- **Discrepancy:** Customer was charged $196.03 MORE than the receipt shows
- **Use Case:** Test detection of overcharging fraud

### 2. `receipt_incorrect_amount_undercharged.png`
**Scenario:** Incorrect Amount Dispute - Suspicious Undercharge
- **Transaction:** Emily Rodriguez - Coffee Shop Downtown
- **Amount Charged:** $89.99
- **Amount on Receipt:** $19.50
- **Discrepancy:** Customer was charged $70.49 MORE than receipt shows
- **Use Case:** Test detection of receipt tampering or wrong receipt submission

### 3. `receipt_merchant_dispute.png`
**Scenario:** Merchant Dispute - Wrong Merchant Name
- **Transaction:** Sarah Johnson - Luxury Watches International
- **Amount Charged:** $8,500.00
- **Merchant on Receipt:** Budget Electronics Outlet
- **Amount on Receipt:** $1,350.00
- **Discrepancy:** Completely different merchant and amount
- **Use Case:** Test detection of fraudulent transactions or identity theft

### 4. `receipt_valid_match.png`
**Scenario:** Valid Receipt - Should Match Transaction
- **Transaction:** Michael Chen - Electronics Store
- **Amount Charged:** $450.00
- **Amount on Receipt:** $287.24 (calculated with tax)
- **Use Case:** Test that legitimate receipts are properly validated

## How to Use These Receipts

### Method 1: Convert to Base64 for API Testing

```python
import base64

# Read and encode the receipt
with open('sample_receipts/receipt_incorrect_amount_overcharged.png', 'rb') as f:
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

## Testing Scenarios

### ✅ Successful Detection Cases
- **Overcharging:** Receipt #1 should detect $196.03 discrepancy
- **Merchant Mismatch:** Receipt #3 should flag different merchant name
- **Valid Receipt:** Receipt #4 should validate as legitimate

### ⚠️ Edge Cases to Test
- **Receipt Tampering:** Receipt #2 (suspicious low amount)
- **Partial Refunds:** Test with receipts showing partial amounts
- **Poor Quality:** Test with blurry or low-resolution images

## Regenerating Receipts

To regenerate these receipts with different data:

```bash
python generate_sample_receipts.py
```

Edit the `generate_sample_receipts.py` script to customize:
- Merchant names
- Item lists
- Amounts
- Dates
- Receipt formatting

## Integration with Dispute System

These receipts correspond to the following seeded transactions:

| Receipt File | Transaction ID | Customer | Merchant | Amount |
|-------------|----------------|----------|----------|--------|
| receipt_incorrect_amount_overcharged.png | 3 | John Smith | TechGadgets Online | $299.99 |
| receipt_incorrect_amount_undercharged.png | 4 | Emily Rodriguez | Coffee Shop Downtown | $89.99 |
| receipt_merchant_dispute.png | 1 | Sarah Johnson | Luxury Watches International | $8,500.00 |
| receipt_valid_match.png | 2 | Michael Chen | Electronics Store | $450.00 |

## Notes

- All receipts are generated programmatically using PIL (Pillow)
- Receipt format mimics real-world retail receipts
- Amounts include 8% sales tax calculation
- Images are 400x600 pixels, optimized for OCR
- Font: Arial (fallback to default if unavailable)

## Troubleshooting

**Issue:** GPT-4o returns error
- Check that your OpenAI API key is set in `.env`
- Verify the API key has access to GPT-4o Vision
- Ensure the Base64 string includes the data URI prefix

**Issue:** Poor OCR accuracy
- Increase image resolution in `generate_sample_receipts.py`
- Use higher quality fonts
- Ensure good contrast (black text on white background)

**Issue:** Receipt not matching transaction
- Verify you're using the correct receipt for the transaction
- Check the transaction ID mapping in the table above