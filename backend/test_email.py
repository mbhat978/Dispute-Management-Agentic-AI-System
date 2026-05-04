"""
Test script to verify email sending functionality.
"""
from dotenv import load_dotenv
load_dotenv()

from email_service import send_dispute_approval_email_sync
from loguru import logger
import sys

# Configure logging
logger.remove()
logger.add(sys.stdout, level="DEBUG")

def test_email():
    """Test sending an approval email."""
    logger.info("Testing email sending...")
    
    result = send_dispute_approval_email_sync(
        customer_email="mbhat978.mb@gmail.com",  # Send to same email for testing
        customer_name="Test Customer",
        ticket_id=999,
        transaction_amount=100.00,
        merchant_name="Test Merchant",
        transaction_date="April 30, 2026",
        resolution_notes="This is a test email to verify the email system is working correctly.",
        dispute_category="test",
        created_at="April 30, 2026",
        resolved_at="April 30, 2026 at 01:00 PM UTC"
    )
    
    if result:
        logger.success("✅ Email sent successfully!")
        return True
    else:
        logger.error("❌ Email failed to send!")
        return False

if __name__ == "__main__":
    success = test_email()
    sys.exit(0 if success else 1)

# Made with Bob
