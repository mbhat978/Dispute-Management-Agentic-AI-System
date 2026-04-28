from PIL import Image, ImageDraw, ImageFont
import os

def create_refund_evidence_email():
    """Create a mock email screenshot showing refund request communication"""
    
    # Create image with email-like appearance
    width, height = 800, 1000
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a system font, fallback to default
    try:
        title_font = ImageFont.truetype("arial.ttf", 24)
        header_font = ImageFont.truetype("arial.ttf", 16)
        body_font = ImageFont.truetype("arial.ttf", 14)
        small_font = ImageFont.truetype("arial.ttf", 12)
    except:
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Email header background
    draw.rectangle([0, 0, width, 60], fill='#1a73e8')
    draw.text((20, 20), "Gmail", fill='white', font=title_font)
    
    # Email metadata section
    y_pos = 80
    draw.text((20, y_pos), "From: support@fashionstore.com", fill='#333', font=header_font)
    y_pos += 30
    draw.text((20, y_pos), "To: meera.reddy@email.com", fill='#333', font=header_font)
    y_pos += 30
    draw.text((20, y_pos), "Date: January 10, 2024, 3:45 PM", fill='#666', font=small_font)
    y_pos += 30
    draw.text((20, y_pos), "Subject: Re: Return Confirmation - Order #FS-2024-1357", fill='#333', font=header_font)
    
    # Separator line
    y_pos += 40
    draw.line([20, y_pos, width-20, y_pos], fill='#ddd', width=2)
    
    # Email body
    y_pos += 30
    email_body = [
        "Dear Meera Reddy,",
        "",
        "Thank you for contacting Fashion Store Customer Support.",
        "",
        "We have received your returned item:",
        "",
        "Order Number: FS-2024-1357",
        "Product: Designer Handbag - Classic Collection",
        "Return Date: January 8, 2024",
        "Return Tracking: RET-FS-456789",
        "Original Payment: $35.00 (Card ending in 1357)",
        "",
        "Your return has been processed and approved. The refund of",
        "$35.00 will be credited to your original payment method within",
        "5-7 business days from the date of this email.",
        "",
        "Refund Status: APPROVED - Processing",
        "Expected Credit Date: January 15-17, 2024",
        "",
        "If you do not see the refund in your account after 7 business",
        "days, please contact your bank or card issuer, as processing",
        "times may vary.",
        "",
        "Thank you for shopping with Fashion Store.",
        "",
        "Best regards,",
        "Fashion Store Customer Support Team",
        "support@fashionstore.com",
        "1-800-FASHION-1"
    ]
    
    for line in email_body:
        if y_pos > height - 50:
            break
        draw.text((40, y_pos), line, fill='#333', font=body_font)
        y_pos += 25
    
    # Footer
    draw.rectangle([0, height-40, width, height], fill='#f5f5f5')
    draw.text((20, height-30), "This is an automated message. Please do not reply directly.", 
              fill='#666', font=small_font)
    
    # Save the image
    output_path = os.path.join('sample_receipts', 'refund_evidence_email_screenshot.png')
    img.save(output_path)
    print(f"Created: {output_path}")
    return output_path

def create_return_receipt():
    """Create a mock return receipt/shipping label"""
    
    width, height = 800, 600
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        title_font = ImageFont.truetype("arial.ttf", 28)
        header_font = ImageFont.truetype("arial.ttf", 18)
        body_font = ImageFont.truetype("arial.ttf", 14)
        bold_font = ImageFont.truetype("arialbd.ttf", 16)
    except:
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
        bold_font = ImageFont.load_default()
    
    # Header
    draw.rectangle([0, 0, width, 80], fill='#e91e63')
    draw.text((width//2 - 150, 25), "RETURN RECEIPT", fill='white', font=title_font)
    
    # Border
    draw.rectangle([10, 10, width-10, height-10], outline='#333', width=3)
    
    # Content
    y_pos = 100
    
    # Return tracking barcode area (simulated)
    draw.rectangle([50, y_pos, width-50, y_pos+60], outline='#333', width=2)
    draw.text((width//2 - 100, y_pos+20), "RET-FS-456789", fill='#333', font=header_font)
    
    y_pos += 80
    
    # Return details
    details = [
        ("Return Authorization:", "RA-2024-FS-1357"),
        ("Return Date:", "January 8, 2024"),
        ("Carrier:", "India Post Speed Post"),
        ("Tracking Number:", "SP456789123456"),
        ("", ""),
        ("Customer:", "Meera Reddy"),
        ("Order Number:", "FS-2024-1357"),
        ("Product:", "Designer Handbag - Classic Collection"),
        ("Reason:", "Changed mind - Color not as expected"),
        ("", ""),
        ("Return Address:", "Fashion Store Returns Center"),
        ("", "456 Fashion Plaza, 2nd Floor"),
        ("", "Mumbai, Maharashtra 400001"),
        ("", ""),
        ("Refund Amount:", "$35.00"),
        ("Refund Method:", "Original Payment (Card ****1357)"),
        ("Expected Refund:", "5-7 business days after receipt"),
    ]
    
    for label, value in details:
        if label:
            draw.text((50, y_pos), label, fill='#666', font=body_font)
            draw.text((300, y_pos), value, fill='#333', font=bold_font)
        y_pos += 25
    
    # Footer
    y_pos = height - 60
    draw.rectangle([0, y_pos, width, height], fill='#f0f0f0')
    draw.text((50, y_pos+15), "Keep this receipt for your records. Contact support@techgadgets.com for questions.", 
              fill='#666', font=body_font)
    
    output_path = os.path.join('sample_receipts', 'refund_evidence_return_receipt.png')
    img.save(output_path)
    print(f"Created: {output_path}")
    return output_path

def create_merchant_chat_screenshot():
    """Create a mock chat/support ticket screenshot"""
    
    width, height = 700, 900
    img = Image.new('RGB', (width, height), color='#f5f5f5')
    draw = ImageDraw.Draw(img)
    
    try:
        title_font = ImageFont.truetype("arial.ttf", 20)
        header_font = ImageFont.truetype("arial.ttf", 14)
        body_font = ImageFont.truetype("arial.ttf", 13)
        time_font = ImageFont.truetype("arial.ttf", 10)
    except:
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
        time_font = ImageFont.load_default()
    
    # Header
    draw.rectangle([0, 0, width, 60], fill='#e91e63')
    draw.text((20, 20), "Fashion Store Support - Ticket #FS1357", fill='white', font=title_font)
    
    y_pos = 80
    
    # Chat messages
    messages = [
        ("customer", "January 6, 2024 - 11:30 AM",
         "Hi, I'd like to return the Designer Handbag I ordered (Order #FS-2024-1357). The color doesn't match what I expected from the website."),
        ("agent", "January 6, 2024 - 11:45 AM",
         "Hello Meera! I'm sorry the handbag didn't meet your expectations. We'd be happy to process a return for you. Let me create a return authorization."),
        ("agent", "January 6, 2024 - 11:50 AM",
         "I've generated return authorization RA-2024-FS-1357. Please ship the item back using the prepaid label sent to your email at meera.reddy@email.com."),
        ("customer", "January 6, 2024 - 11:52 AM",
         "Thank you! When will I receive my refund of $35.00?"),
        ("agent", "January 6, 2024 - 11:55 AM",
         "Once we receive and inspect the item, your refund will be processed within 5-7 business days to your original payment method (card ending 1357)."),
        ("customer", "January 10, 2024 - 9:15 AM",
         "I shipped the item on January 8. Tracking shows it was delivered to your warehouse on January 9. When will the refund be issued?"),
        ("agent", "January 10, 2024 - 3:45 PM",
         "Thank you for the update! I've confirmed receipt of your return. The refund has been approved and will appear in your account within 5-7 business days from today."),
    ]
    
    for sender, timestamp, message in messages:
        # Message bubble
        if sender == "customer":
            bubble_color = '#e3f2fd'
            x_offset = 50
            text_color = '#1565c0'
        else:
            bubble_color = '#fff'
            x_offset = 20
            text_color = '#333'
        
        # Calculate message height
        lines = []
        words = message.split()
        current_line = ""
        for word in words:
            test_line = current_line + word + " "
            if len(test_line) * 7 < width - 150:  # Approximate width check
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "
        lines.append(current_line)
        
        bubble_height = len(lines) * 20 + 40
        
        # Draw bubble
        draw.rectangle([x_offset, y_pos, width-x_offset-30, y_pos+bubble_height], 
                      fill=bubble_color, outline='#ddd', width=1)
        
        # Draw timestamp
        draw.text((x_offset+10, y_pos+5), timestamp, fill='#999', font=time_font)
        
        # Draw message text
        text_y = y_pos + 20
        for line in lines:
            draw.text((x_offset+10, text_y), line.strip(), fill=text_color, font=body_font)
            text_y += 20
        
        y_pos += bubble_height + 15
    
    # Footer
    draw.rectangle([0, height-40, width, height], fill='#e91e63')
    draw.text((20, height-28), "Ticket Status: RESOLVED | Refund Approved",
              fill='white', font=header_font)
    
    output_path = os.path.join('sample_receipts', 'refund_evidence_support_chat.png')
    img.save(output_path)
    print(f"Created: {output_path}")
    return output_path

if __name__ == "__main__":
    print("Generating refund evidence images...")
    print("-" * 50)
    
    # Create sample_receipts directory if it doesn't exist
    os.makedirs('sample_receipts', exist_ok=True)
    
    # Generate all evidence types
    create_refund_evidence_email()
    create_return_receipt()
    create_merchant_chat_screenshot()
    
    print("-" * 50)
    print("All refund evidence images created successfully!")
    print("\nThese images can be used to test the 'refund not received' dispute scenario.")
    print("They show proof of:")
    print("  1. Email confirmation of return and refund approval")
    print("  2. Return receipt with tracking information")
    print("  3. Support chat conversation about the return")

# Made with Bob
