"""
Test script for the GPT-4o Vision receipt analysis tool.
Converts sample receipts to Base64 and tests the analyze_receipt_evidence function.
"""

import base64
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from mcp_servers.banking_tools import analyze_receipt_evidence


async def test_receipt(receipt_path: str, expected_merchant: str, scenario_name: str):
    """Test a receipt image with the GPT-4o Vision tool."""
    print(f"\n{'='*70}")
    print(f"Testing: {scenario_name}")
    print(f"{'='*70}")
    print(f"Receipt file: {receipt_path}")
    print(f"Expected merchant: {expected_merchant}")
    print()
    
    # Read and encode the receipt image
    with open(receipt_path, 'rb') as f:
        image_data = f.read()
        base64_str = base64.b64encode(image_data).decode('utf-8')
    
    print(f"Image size: {len(image_data)} bytes")
    print(f"Base64 length: {len(base64_str)} characters")
    print()
    
    # Call the vision analysis tool
    print("Calling GPT-4o Vision for analysis...")
    result_json = await analyze_receipt_evidence(base64_str, expected_merchant)
    
    print("\n" + "="*70)
    print("ANALYSIS RESULT:")
    print("="*70)
    print(result_json)
    print()
    
    return result_json


async def main():
    """Run all receipt tests."""
    print("\n" + "="*70)
    print("GPT-4o VISION RECEIPT ANALYSIS TEST SUITE")
    print("="*70)
    
    receipts_dir = Path("sample_receipts")
    
    if not receipts_dir.exists():
        print("\n❌ Error: sample_receipts directory not found!")
        print("Please run 'python generate_sample_receipts.py' first.")
        return
    
    # Test 1: Incorrect Amount - Overcharged
    await test_receipt(
        receipt_path=str(receipts_dir / "receipt_incorrect_amount_overcharged.png"),
        expected_merchant="TechGadgets Online",
        scenario_name="INCORRECT AMOUNT - Customer Overcharged ($299.99 charged, receipt shows $103.96)"
    )
    
    input("\nPress Enter to continue to next test...")
    
    # Test 2: Incorrect Amount - Undercharged (suspicious)
    await test_receipt(
        receipt_path=str(receipts_dir / "receipt_incorrect_amount_undercharged.png"),
        expected_merchant="Coffee Shop Downtown",
        scenario_name="INCORRECT AMOUNT - Receipt Shows Less ($89.99 charged, receipt shows $19.50)"
    )
    
    input("\nPress Enter to continue to next test...")
    
    # Test 3: Merchant Dispute
    await test_receipt(
        receipt_path=str(receipts_dir / "receipt_merchant_dispute.png"),
        expected_merchant="Luxury Watches International",
        scenario_name="MERCHANT DISPUTE - Wrong Merchant (Expected: Luxury Watches, Receipt: Budget Electronics)"
    )
    
    input("\nPress Enter to continue to next test...")
    
    # Test 4: Valid Receipt
    await test_receipt(
        receipt_path=str(receipts_dir / "receipt_valid_match.png"),
        expected_merchant="Electronics Store",
        scenario_name="VALID RECEIPT - Should Match Transaction ($450.00)"
    )
    
    print("\n" + "="*70)
    print("✅ ALL TESTS COMPLETED")
    print("="*70)
    print("\nThe GPT-4o Vision tool has analyzed all sample receipts.")
    print("Review the results above to see how it extracts merchant names,")
    print("amounts, and detects fraud indicators.")


if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob
