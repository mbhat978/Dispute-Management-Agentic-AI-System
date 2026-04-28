"""
Generate sample receipt images for the 6-customer test scenarios.
Creates realistic receipt images for dispute scenarios that require receipt evidence.
"""

from PIL import Image, ImageDraw, ImageFont  # type: ignore
import os
import sys
import io
from typing import Optional

# Fix Windows console encoding issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def create_receipt_image(
    merchant_name: str,
    amount: float,
    date: str,
    items: list,
    filename: str,
    show_different_amount: bool = False,
    actual_receipt_amount: Optional[float] = None
):
    """
    Create a realistic receipt image.
    
    Args:
        merchant_name: Name of the merchant
        amount: Transaction amount charged to customer
        date: Transaction date
        items: List of (item_name, item_price) tuples
        filename: Output filename
        show_different_amount: If True, show a different amount on receipt than charged
        actual_receipt_amount: The amount shown on receipt (if different from charged)
    """
    # Create image with white background
    width, height = 400, 600
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a monospace font, fallback to default
    try:
        font_large = ImageFont.truetype("arial.ttf", 20)
        font_medium = ImageFont.truetype("arial.ttf", 16)
        font_small = ImageFont.truetype("arial.ttf", 14)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    y_position = 20
    
    # Merchant name (centered)
    merchant_bbox = draw.textbbox((0, 0), merchant_name, font=font_large)
    merchant_width = merchant_bbox[2] - merchant_bbox[0]
    draw.text(((width - merchant_width) // 2, y_position), merchant_name, fill='black', font=font_large)
    y_position += 40
    
    # Date
    draw.text((20, y_position), f"Date: {date}", fill='black', font=font_small)
    y_position += 30
    
    # Separator line
    draw.line([(20, y_position), (width - 20, y_position)], fill='black', width=2)
    y_position += 20
    
    # Items
    draw.text((20, y_position), "ITEMS:", fill='black', font=font_medium)
    y_position += 25
    
    subtotal = 0
    for item_name, item_price in items:
        draw.text((30, y_position), item_name, fill='black', font=font_small)
        price_text = f"${item_price:.2f}"
        price_bbox = draw.textbbox((0, 0), price_text, font=font_small)
        price_width = price_bbox[2] - price_bbox[0]
        draw.text((width - 30 - price_width, y_position), price_text, fill='black', font=font_small)
        y_position += 22
        subtotal += item_price
    
    y_position += 10
    
    # Separator line
    draw.line([(20, y_position), (width - 20, y_position)], fill='black', width=1)
    y_position += 15
    
    # Subtotal
    draw.text((30, y_position), "Subtotal:", fill='black', font=font_small)
    subtotal_text = f"${subtotal:.2f}"
    subtotal_bbox = draw.textbbox((0, 0), subtotal_text, font=font_small)
    subtotal_width = subtotal_bbox[2] - subtotal_bbox[0]
    draw.text((width - 30 - subtotal_width, y_position), subtotal_text, fill='black', font=font_small)
    y_position += 25
    
    # Tax
    tax = subtotal * 0.08
    draw.text((30, y_position), "Tax (8%):", fill='black', font=font_small)
    tax_text = f"${tax:.2f}"
    tax_bbox = draw.textbbox((0, 0), tax_text, font=font_small)
    tax_width = tax_bbox[2] - tax_bbox[0]
    draw.text((width - 30 - tax_width, y_position), tax_text, fill='black', font=font_small)
    y_position += 30
    
    # Total (bold line)
    draw.line([(20, y_position), (width - 20, y_position)], fill='black', width=2)
    y_position += 15
    
    # Use actual_receipt_amount if provided, otherwise calculate from items
    receipt_total = actual_receipt_amount if actual_receipt_amount else (subtotal + tax)
    
    draw.text((30, y_position), "TOTAL:", fill='black', font=font_large)
    total_text = f"${receipt_total:.2f}"
    total_bbox = draw.textbbox((0, 0), total_text, font=font_large)
    total_width = total_bbox[2] - total_bbox[0]
    draw.text((width - 30 - total_width, y_position), total_text, fill='black', font=font_large)
    y_position += 50
    
    # Payment method
    draw.text((30, y_position), "Payment: VISA ****1234", fill='black', font=font_small)
    y_position += 25
    
    # Thank you message
    thank_you = "Thank you for your business!"
    thank_you_bbox = draw.textbbox((0, 0), thank_you, font=font_small)
    thank_you_width = thank_you_bbox[2] - thank_you_bbox[0]
    draw.text(((width - thank_you_width) // 2, y_position), thank_you, fill='black', font=font_small)
    
    # Save image
    img.save(filename)
    print(f"✓ Created receipt: {filename}")
    print(f"  Merchant: {merchant_name}")
    print(f"  Receipt shows: ${receipt_total:.2f}")
    if show_different_amount:
        print(f"  ⚠️  Customer was charged: ${amount:.2f} (DISCREPANCY!)")
    print()


def main():
    """Generate sample receipts for 6-customer test scenarios."""
    
    # Create receipts directory if it doesn't exist
    os.makedirs("sample_receipts", exist_ok=True)
    
    print("Generating sample receipt images for 6-customer test scenarios...\n")
    print("=" * 70)
    
    # ========================================================================
    # SCENARIO 5: INCORRECT AMOUNT - Overcharged (Customer 6 - Karthik Menon)
    # ========================================================================
    print("\n📍 SCENARIO 5: Incorrect Amount - Overcharged")
    print("-" * 70)
    print("Customer: Karthik Menon")
    print("Merchant: Electronics Store")
    print("Charged: $50.00 | Receipt shows: $45.00")
    print("-" * 70)
    create_receipt_image(
        merchant_name="Electronics Store",
        amount=50.00,  # What customer was charged
        date="2026-04-10 04:00 PM",
        items=[
            ("USB Cable", 12.99),
            ("Phone Stand", 15.99),
            ("Screen Cleaner", 8.99),
            ("Cable Ties", 3.99)
        ],
        filename="sample_receipts/receipt_scenario5_electronics_store_overcharged.png",
        show_different_amount=True,
        actual_receipt_amount=45.00  # Receipt shows $45 (customer charged $50)
    )
    
    # ========================================================================
    # SCENARIO 2: MERCHANT DISPUTE - Amazon India (Customer 2 - Rahul Verma)
    # ========================================================================
    print("\n📍 SCENARIO 2: Merchant Dispute - Amazon India (Item Not Delivered)")
    print("-" * 70)
    print("Customer: Rahul Verma")
    print("Merchant: Amazon India")
    print("Amount: $799.99 | Item: iPhone 15 Pro")
    print("-" * 70)
    create_receipt_image(
        merchant_name="Amazon India",
        amount=799.99,
        date="2026-04-03 11:00 AM",
        items=[
            ("iPhone 15 Pro 256GB", 740.73)
        ],
        filename="sample_receipts/receipt_scenario2_amazon_iphone.png",
        show_different_amount=False,
        actual_receipt_amount=None  # Matches transaction
    )
    
    # ========================================================================
    # SCENARIO 2B: HIGH-RISK MERCHANT - ShopXYZ Online (Customer 2 - Rahul Verma)
    # ========================================================================
    print("\n📍 SCENARIO 2B: High-Risk Merchant - ShopXYZ Online (Empty Box)")
    print("-" * 70)
    print("Customer: Rahul Verma")
    print("Merchant: ShopXYZ Online")
    print("Amount: $150.00 | Received: Empty box")
    print("-" * 70)
    create_receipt_image(
        merchant_name="ShopXYZ Online",
        amount=150.00,
        date="2026-03-22 02:30 PM",
        items=[
            ("Gaming Laptop", 138.89)
        ],
        filename="sample_receipts/receipt_scenario2b_shopxyz_empty_box.png",
        show_different_amount=False,
        actual_receipt_amount=None  # Matches transaction
    )
    
    # ========================================================================
    # SCENARIO 9: QUALITY DISPUTE - Electronics Mart (Customer 6 - Karthik Menon)
    # ========================================================================
    print("\n📍 SCENARIO 9: Quality/Service Dispute - Damaged Product")
    print("-" * 70)
    print("Customer: Karthik Menon")
    print("Merchant: Electronics Mart")
    print("Amount: $250.00 | Issue: Damaged product")
    print("-" * 70)
    create_receipt_image(
        merchant_name="Electronics Mart",
        amount=250.00,
        date="2026-04-16 11:00 AM",
        items=[
            ("Wireless Keyboard", 89.99),
            ("Gaming Mouse", 129.99)
        ],
        filename="sample_receipts/receipt_scenario9_electronics_mart_damaged.png",
        show_different_amount=False,
        actual_receipt_amount=None  # Matches transaction
    )
    
    # ========================================================================
    # SCENARIO 8: REFUND NOT RECEIVED - Fashion Store (Customer 5 - Meera Reddy)
    # ========================================================================
    print("\n📍 SCENARIO 8: Refund Not Received - Fashion Store")
    print("-" * 70)
    print("Customer: Meera Reddy")
    print("Merchant: Fashion Store")
    print("Amount: $35.00 | Refund promised 10 days ago")
    print("-" * 70)
    create_receipt_image(
        merchant_name="Fashion Store",
        amount=35.00,
        date="2026-04-06 02:00 PM",
        items=[
            ("T-Shirt", 19.99),
            ("Socks (2 pairs)", 9.99)
        ],
        filename="sample_receipts/receipt_scenario8_fashion_store_refund.png",
        show_different_amount=False,
        actual_receipt_amount=None  # Matches transaction
    )
    
    # ========================================================================
    # SCENARIO 4: DUPLICATE TRANSACTION - Taj Restaurant (Customer 4 - Vikram Singh)
    # ========================================================================
    print("\n📍 SCENARIO 4: Duplicate Transaction - Taj Restaurant")
    print("-" * 70)
    print("Customer: Vikram Singh")
    print("Merchant: Taj Restaurant")
    print("Amount: $25.00 | Charged twice within 5 minutes")
    print("-" * 70)
    create_receipt_image(
        merchant_name="Taj Restaurant",
        amount=25.00,
        date="2026-04-08 07:30 PM",
        items=[
            ("Butter Chicken", 15.99),
            ("Naan Bread", 2.99),
            ("Mango Lassi", 3.99)
        ],
        filename="sample_receipts/receipt_scenario4_taj_restaurant_duplicate.png",
        show_different_amount=False,
        actual_receipt_amount=None  # Matches transaction
    )
    
    print("=" * 70)
    print("\n✅ All test scenario receipts generated successfully!")
    print(f"\nReceipts saved in: {os.path.abspath('sample_receipts')}")
    print("\n📋 Receipt Mapping to Test Scenarios:")
    print("-" * 70)
    print("Scenario 2:  receipt_scenario2_amazon_iphone.png")
    print("Scenario 2B: receipt_scenario2b_shopxyz_empty_box.png")
    print("Scenario 4:  receipt_scenario4_taj_restaurant_duplicate.png")
    print("Scenario 5:  receipt_scenario5_electronics_store_overcharged.png")
    print("Scenario 8:  receipt_scenario8_fashion_store_refund.png")
    print("Scenario 9:  receipt_scenario9_electronics_mart_damaged.png")
    print("-" * 70)
    print("\n💡 To use these receipts in disputes:")
    print("  1. Create a dispute for the corresponding transaction")
    print("  2. Upload the receipt image via the UI or API")
    print("  3. The Investigator agent will analyze it with GPT-4o Vision")
    print("\n🔧 To convert to Base64 for API testing:")
    print("  import base64")
    print("  with open('sample_receipts/receipt_scenario5_electronics_store_overcharged.png', 'rb') as f:")
    print("      base64_str = base64.b64encode(f.read()).decode('utf-8')")


if __name__ == "__main__":
    main()

# Made with Bob
