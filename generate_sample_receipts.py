"""
Generate sample receipt images for testing the GPT-4o Vision receipt analysis tool.
Creates realistic receipt images for various dispute scenarios.
"""

from PIL import Image, ImageDraw, ImageFont
import os
import sys
import io

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
    actual_receipt_amount: float = None
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
    """Generate sample receipts for testing."""
    
    # Create receipts directory if it doesn't exist
    os.makedirs("sample_receipts", exist_ok=True)
    
    print("Generating sample receipt images for testing...\n")
    print("=" * 60)
    
    # Receipt 1: Incorrect Amount - Customer charged MORE than receipt shows
    # Transaction ID 3: John Smith - TechGadgets Online - $299.99
    print("\n1. INCORRECT AMOUNT DISPUTE - Customer overcharged")
    print("-" * 60)
    create_receipt_image(
        merchant_name="TechGadgets Online",
        amount=299.99,  # What customer was charged
        date="2026-04-19 10:30 AM",
        items=[
            ("Wireless Mouse", 45.99),
            ("USB-C Cable", 19.99),
            ("Phone Case", 24.99),
            ("Screen Protector", 12.99)
        ],
        filename="sample_receipts/receipt_incorrect_amount_overcharged.png",
        show_different_amount=True,
        actual_receipt_amount=103.96  # Receipt shows much less (subtotal + tax)
    )
    
    # Receipt 2: Incorrect Amount - Customer charged LESS than receipt shows (rare but possible)
    # Transaction ID 4: Emily Rodriguez - Coffee Shop Downtown - $89.99
    print("\n2. INCORRECT AMOUNT DISPUTE - Receipt shows more")
    print("-" * 60)
    create_receipt_image(
        merchant_name="Coffee Shop Downtown",
        amount=89.99,  # What customer was charged
        date="2026-04-22 02:30 PM",
        items=[
            ("Latte", 5.50),
            ("Cappuccino", 5.50),
            ("Croissant", 4.50),
            ("Muffin", 4.00)
        ],
        filename="sample_receipts/receipt_incorrect_amount_undercharged.png",
        show_different_amount=True,
        actual_receipt_amount=19.50  # Receipt shows correct amount (much less than charged)
    )
    
    # Receipt 3: Merchant Dispute - Wrong merchant name
    # Transaction ID 1: Sarah Johnson - Luxury Watches International - $8500.00
    print("\n3. MERCHANT DISPUTE - Different merchant on receipt")
    print("-" * 60)
    create_receipt_image(
        merchant_name="Budget Electronics Outlet",  # Different merchant!
        amount=8500.00,
        date="2026-04-19 02:00 AM",
        items=[
            ("Laptop Computer", 1200.00),
            ("Extended Warranty", 150.00)
        ],
        filename="sample_receipts/receipt_merchant_dispute.png",
        show_different_amount=True,
        actual_receipt_amount=1350.00  # Much less than charged $8500
    )
    
    # Receipt 4: Valid Receipt - Matches transaction perfectly
    # Transaction ID 2: Michael Chen - Electronics Store - $450.00
    print("\n4. VALID RECEIPT - Matches transaction")
    print("-" * 60)
    create_receipt_image(
        merchant_name="Electronics Store",
        amount=450.00,
        date="2026-04-20 05:00 PM",
        items=[
            ("Bluetooth Speaker", 89.99),
            ("Headphones", 129.99),
            ("Phone Charger", 29.99),
            ("Cable Organizer", 15.99)
        ],
        filename="sample_receipts/receipt_valid_match.png",
        show_different_amount=False,
        actual_receipt_amount=None  # Will calculate from items (should match $450)
    )
    
    print("=" * 60)
    print("\n✅ All sample receipts generated successfully!")
    print(f"\nReceipts saved in: {os.path.abspath('sample_receipts')}")
    print("\nYou can now test the GPT-4o Vision tool with these receipts.")
    print("\nTo convert to Base64 for testing:")
    print("  import base64")
    print("  with open('sample_receipts/receipt_incorrect_amount_overcharged.png', 'rb') as f:")
    print("      base64_str = base64.b64encode(f.read()).decode('utf-8')")


if __name__ == "__main__":
    main()

# Made with Bob
