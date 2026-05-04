"""
Email templates for dispute notification system.

This module contains HTML and plain text email templates for dispute approval notifications.
"""

from datetime import datetime
from typing import Dict, Any, Optional


def generate_approval_email_html(
    customer_name: str,
    ticket_id: int,
    transaction_amount: float,
    merchant_name: str,
    transaction_date: str,
    resolution_notes: str,
    dispute_category: str = "unknown",
    created_at: Optional[str] = None,
    resolved_at: Optional[str] = None
) -> str:
    """
    Generate HTML email content for dispute approval notification.
    
    Args:
        customer_name: Name of the customer
        ticket_id: Dispute ticket ID
        transaction_amount: Amount of the disputed transaction
        merchant_name: Merchant/business name
        transaction_date: Date of the transaction
        resolution_notes: Detailed resolution notes
        dispute_category: Category of the dispute
        created_at: When dispute was created
        resolved_at: When dispute was resolved
        
    Returns:
        str: HTML formatted email content
    """
    
    formatted_amount = f"${transaction_amount:,.2f}"
    
    if not resolved_at:
        resolved_at = datetime.utcnow().strftime("%B %d, %Y at %I:%M %p UTC")
    
    if not created_at:
        created_at = "Recently"
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dispute Approved - #{ticket_id}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background-color: #f4f4f4; margin: 0; padding: 0; }}
        .email-container {{ max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 24px; font-weight: 600; }}
        .status-badge {{ display: inline-block; background-color: #10b981; color: white; padding: 8px 16px; border-radius: 20px; font-size: 14px; font-weight: 600; margin-top: 10px; }}
        .content {{ padding: 30px; }}
        .greeting {{ font-size: 18px; margin-bottom: 20px; color: #1f2937; }}
        .success-message {{ background-color: #d1fae5; border-left: 4px solid #10b981; padding: 15px; margin: 20px 0; border-radius: 4px; }}
        .success-message p {{ margin: 0; color: #065f46; font-weight: 500; }}
        .details-section {{ margin: 25px 0; }}
        .section-title {{ font-size: 16px; font-weight: 600; color: #1f2937; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #e5e7eb; }}
        .details-table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        .details-table tr {{ border-bottom: 1px solid #f3f4f6; }}
        .details-table td {{ padding: 12px 8px; }}
        .details-table td:first-child {{ font-weight: 600; color: #6b7280; width: 40%; }}
        .details-table td:last-child {{ color: #1f2937; }}
        .resolution-box {{ background-color: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 15px; margin: 15px 0; }}
        .resolution-box p {{ margin: 8px 0; color: #374151; line-height: 1.6; }}
        .next-steps {{ background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 15px; margin: 20px 0; border-radius: 4px; }}
        .next-steps h3 {{ margin: 0 0 10px 0; color: #1e40af; font-size: 16px; }}
        .next-steps ul {{ margin: 10px 0; padding-left: 20px; }}
        .next-steps li {{ margin: 8px 0; color: #1e3a8a; }}
        .footer {{ background-color: #f9fafb; padding: 20px; text-align: center; border-top: 1px solid #e5e7eb; }}
        .footer p {{ margin: 5px 0; font-size: 14px; color: #6b7280; }}
        .contact-info {{ margin-top: 15px; padding-top: 15px; border-top: 1px solid #e5e7eb; }}
        .amount-highlight {{ font-size: 20px; font-weight: 700; color: #10b981; }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>✅ Dispute Approved</h1>
            <div class="status-badge">APPROVED</div>
        </div>
        <div class="content">
            <p class="greeting">Dear {customer_name},</p>
            <div class="success-message">
                <p>Great news! Your dispute has been approved and resolved in your favor.</p>
            </div>
            <div class="details-section">
                <div class="section-title">Dispute Details</div>
                <table class="details-table">
                    <tr><td>Dispute ID</td><td><strong>#{ticket_id}</strong></td></tr>
                    <tr><td>Status</td><td><span style="color: #10b981; font-weight: 600;">APPROVED</span></td></tr>
                    <tr><td>Date Submitted</td><td>{created_at}</td></tr>
                    <tr><td>Resolution Date</td><td>{resolved_at}</td></tr>
                    <tr><td>Category</td><td>{dispute_category.replace('_', ' ').title()}</td></tr>
                </table>
            </div>
            <div class="details-section">
                <div class="section-title">Transaction Details</div>
                <table class="details-table">
                    <tr><td>Amount</td><td class="amount-highlight">{formatted_amount}</td></tr>
                    <tr><td>Merchant</td><td>{merchant_name}</td></tr>
                    <tr><td>Transaction Date</td><td>{transaction_date}</td></tr>
                </table>
            </div>
            <div class="details-section">
                <div class="section-title">Resolution</div>
                <div class="resolution-box"><p>{resolution_notes}</p></div>
            </div>
            <div class="next-steps">
                <h3>What Happens Next?</h3>
                <ul>
                    <li>Your account will be credited with <strong>{formatted_amount}</strong> within 3-5 business days</li>
                    <li>You will receive a confirmation once the refund is processed</li>
                    <li>No further action is required from your side</li>
                    <li>You can track the refund status in your account dashboard</li>
                </ul>
            </div>
            <p style="margin-top: 25px; color: #6b7280;">We appreciate your patience during the review process. If you have any questions about this resolution, please don't hesitate to contact our support team.</p>
        </div>
        <div class="footer">
            <div class="contact-info">
                <p><strong>Need Help?</strong></p>
                <p>Contact us at: <a href="mailto:support@disputemanagement.com" style="color: #667eea;">support@disputemanagement.com</a></p>
                <p>Phone: 1-800-DISPUTE (1-800-347-7883)</p>
            </div>
            <p style="margin-top: 20px;">Best regards,<br><strong>Dispute Management Team</strong></p>
            <p style="font-size: 12px; color: #9ca3af; margin-top: 15px;">This is an automated message. Please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
"""
    return html_content


def generate_approval_email_text(
    customer_name: str,
    ticket_id: int,
    transaction_amount: float,
    merchant_name: str,
    transaction_date: str,
    resolution_notes: str,
    dispute_category: str = "unknown",
    created_at: Optional[str] = None,
    resolved_at: Optional[str] = None
) -> str:
    """Generate plain text email content for dispute approval notification."""
    
    formatted_amount = f"${transaction_amount:,.2f}"
    
    if not resolved_at:
        resolved_at = datetime.utcnow().strftime("%B %d, %Y at %I:%M %p UTC")
    
    if not created_at:
        created_at = "Recently"
    
    text_content = f"""
DISPUTE APPROVED - TICKET #{ticket_id}

Dear {customer_name},

Great news! Your dispute has been approved and resolved in your favor.

DISPUTE DETAILS
Dispute ID:           #{ticket_id}
Status:               APPROVED
Date Submitted:       {created_at}
Resolution Date:      {resolved_at}
Category:             {dispute_category.replace('_', ' ').title()}

TRANSACTION DETAILS
Amount:               {formatted_amount}
Merchant:             {merchant_name}
Transaction Date:     {transaction_date}

RESOLUTION
{resolution_notes}

WHAT HAPPENS NEXT?
- Your account will be credited with {formatted_amount} within 3-5 business days
- You will receive a confirmation once the refund is processed
- No further action is required from your side
- You can track the refund status in your account dashboard

We appreciate your patience during the review process. If you have any questions about this resolution, please contact our support team.

NEED HELP?
Email:  support@disputemanagement.com
Phone:  1-800-DISPUTE (1-800-347-7883)

Best regards,
Dispute Management Team

This is an automated message. Please do not reply to this email.
"""
    return text_content


def generate_rejection_email_html(
    customer_name: str,
    ticket_id: int,
    transaction_amount: float,
    merchant_name: str,
    transaction_date: str,
    resolution_notes: str,
    dispute_category: str = "unknown",
    created_at: Optional[str] = None,
    resolved_at: Optional[str] = None
) -> str:
    """
    Generate HTML email content for dispute rejection notification.
    
    Args:
        customer_name: Name of the customer
        ticket_id: Dispute ticket ID
        transaction_amount: Amount of the disputed transaction
        merchant_name: Merchant/business name
        transaction_date: Date of the transaction
        resolution_notes: Detailed resolution notes
        dispute_category: Category of the dispute
        created_at: When dispute was created
        resolved_at: When dispute was resolved
        
    Returns:
        str: HTML formatted email content
    """
    
    formatted_amount = f"${transaction_amount:,.2f}"
    
    if not resolved_at:
        resolved_at = datetime.utcnow().strftime("%B %d, %Y at %I:%M %p UTC")
    
    if not created_at:
        created_at = "Recently"
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dispute Decision - #{ticket_id}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background-color: #f4f4f4; margin: 0; padding: 0; }}
        .email-container {{ max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%); color: white; padding: 30px 20px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 24px; font-weight: 600; }}
        .status-badge {{ display: inline-block; background-color: #dc2626; color: white; padding: 8px 16px; border-radius: 20px; font-size: 14px; font-weight: 600; margin-top: 10px; }}
        .content {{ padding: 30px; }}
        .greeting {{ font-size: 18px; margin-bottom: 20px; color: #1f2937; }}
        .rejection-message {{ background-color: #fee2e2; border-left: 4px solid #dc2626; padding: 15px; margin: 20px 0; border-radius: 4px; }}
        .rejection-message p {{ margin: 0; color: #991b1b; font-weight: 500; }}
        .details-section {{ margin: 25px 0; }}
        .section-title {{ font-size: 16px; font-weight: 600; color: #1f2937; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #e5e7eb; }}
        .details-table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        .details-table tr {{ border-bottom: 1px solid #f3f4f6; }}
        .details-table td {{ padding: 12px 8px; }}
        .details-table td:first-child {{ font-weight: 600; color: #6b7280; width: 40%; }}
        .details-table td:last-child {{ color: #1f2937; }}
        .resolution-box {{ background-color: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 15px; margin: 15px 0; }}
        .resolution-box p {{ margin: 8px 0; color: #374151; line-height: 1.6; }}
        .next-steps {{ background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; border-radius: 4px; }}
        .next-steps h3 {{ margin: 0 0 10px 0; color: #92400e; font-size: 16px; }}
        .next-steps ul {{ margin: 10px 0; padding-left: 20px; }}
        .next-steps li {{ margin: 8px 0; color: #78350f; }}
        .footer {{ background-color: #f9fafb; padding: 20px; text-align: center; border-top: 1px solid #e5e7eb; }}
        .footer p {{ margin: 5px 0; font-size: 14px; color: #6b7280; }}
        .contact-info {{ margin-top: 15px; padding-top: 15px; border-top: 1px solid #e5e7eb; }}
        .amount-highlight {{ font-size: 20px; font-weight: 700; color: #dc2626; }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>❌ Dispute Decision</h1>
            <div class="status-badge">REJECTED</div>
        </div>
        <div class="content">
            <p class="greeting">Dear {customer_name},</p>
            <div class="rejection-message">
                <p>After careful review, we regret to inform you that your dispute has been rejected.</p>
            </div>
            <div class="details-section">
                <div class="section-title">Dispute Details</div>
                <table class="details-table">
                    <tr><td>Dispute ID</td><td><strong>#{ticket_id}</strong></td></tr>
                    <tr><td>Status</td><td><span style="color: #dc2626; font-weight: 600;">REJECTED</span></td></tr>
                    <tr><td>Date Submitted</td><td>{created_at}</td></tr>
                    <tr><td>Resolution Date</td><td>{resolved_at}</td></tr>
                    <tr><td>Category</td><td>{dispute_category.replace('_', ' ').title()}</td></tr>
                </table>
            </div>
            <div class="details-section">
                <div class="section-title">Transaction Details</div>
                <table class="details-table">
                    <tr><td>Amount</td><td class="amount-highlight">{formatted_amount}</td></tr>
                    <tr><td>Merchant</td><td>{merchant_name}</td></tr>
                    <tr><td>Transaction Date</td><td>{transaction_date}</td></tr>
                </table>
            </div>
            <div class="details-section">
                <div class="section-title">Reason for Rejection</div>
                <div class="resolution-box"><p>{resolution_notes}</p></div>
            </div>
            <div class="next-steps">
                <h3>What You Can Do Next</h3>
                <ul>
                    <li>Review the rejection reason carefully</li>
                    <li>If you have additional evidence, you may submit a new dispute with supporting documentation</li>
                    <li>Contact our support team if you believe this decision was made in error</li>
                    <li>You can appeal this decision within 30 days by providing new evidence</li>
                </ul>
            </div>
            <p style="margin-top: 25px; color: #6b7280;">We understand this may not be the outcome you were hoping for. If you have any questions about this decision or would like to discuss your options, please don't hesitate to contact our support team.</p>
        </div>
        <div class="footer">
            <div class="contact-info">
                <p><strong>Need Help?</strong></p>
                <p>Contact us at: <a href="mailto:support@disputemanagement.com" style="color: #dc2626;">support@disputemanagement.com</a></p>
                <p>Phone: 1-800-DISPUTE (1-800-347-7883)</p>
            </div>
            <p style="margin-top: 20px;">Best regards,<br><strong>Dispute Management Team</strong></p>
            <p style="font-size: 12px; color: #9ca3af; margin-top: 15px;">This is an automated message. Please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
"""
    return html_content


def generate_rejection_email_text(
    customer_name: str,
    ticket_id: int,
    transaction_amount: float,
    merchant_name: str,
    transaction_date: str,
    resolution_notes: str,
    dispute_category: str = "unknown",
    created_at: Optional[str] = None,
    resolved_at: Optional[str] = None
) -> str:
    """Generate plain text email content for dispute rejection notification."""
    
    formatted_amount = f"${transaction_amount:,.2f}"
    
    if not resolved_at:
        resolved_at = datetime.utcnow().strftime("%B %d, %Y at %I:%M %p UTC")
    
    if not created_at:
        created_at = "Recently"
    
    text_content = f"""
DISPUTE DECISION - TICKET #{ticket_id}

Dear {customer_name},

After careful review, we regret to inform you that your dispute has been rejected.

DISPUTE DETAILS
Dispute ID:           #{ticket_id}
Status:               REJECTED
Date Submitted:       {created_at}
Resolution Date:      {resolved_at}
Category:             {dispute_category.replace('_', ' ').title()}

TRANSACTION DETAILS
Amount:               {formatted_amount}
Merchant:             {merchant_name}
Transaction Date:     {transaction_date}

REASON FOR REJECTION
{resolution_notes}

WHAT YOU CAN DO NEXT
- Review the rejection reason carefully
- If you have additional evidence, you may submit a new dispute with supporting documentation
- Contact our support team if you believe this decision was made in error
- You can appeal this decision within 30 days by providing new evidence

We understand this may not be the outcome you were hoping for. If you have any questions about this decision or would like to discuss your options, please contact our support team.

NEED HELP?
Email:  support@disputemanagement.com
Phone:  1-800-DISPUTE (1-800-347-7883)

Best regards,
Dispute Management Team

This is an automated message. Please do not reply to this email.
"""
    return text_content