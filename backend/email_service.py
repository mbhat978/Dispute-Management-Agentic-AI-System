"""
Email service for sending dispute notifications.

This module handles SMTP email sending with error handling and logging.
"""

import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import aiosmtplib
from loguru import logger

try:
    from .config import get_smtp_config
    from .email_templates import (
        generate_approval_email_html,
        generate_approval_email_text,
        generate_rejection_email_html,
        generate_rejection_email_text
    )
except ImportError:
    from config import get_smtp_config
    from email_templates import (
        generate_approval_email_html,
        generate_approval_email_text,
        generate_rejection_email_html,
        generate_rejection_email_text
    )


async def send_dispute_approval_email(
    customer_email: str,
    customer_name: str,
    ticket_id: int,
    transaction_amount: float,
    merchant_name: str,
    transaction_date: str,
    resolution_notes: str,
    dispute_category: str = "unknown",
    created_at: Optional[str] = None,
    resolved_at: Optional[str] = None
) -> bool:
    """
    Send dispute approval email notification to customer.
    
    Args:
        customer_email: Customer's email address
        customer_name: Customer's full name
        ticket_id: Dispute ticket ID
        transaction_amount: Transaction amount
        merchant_name: Merchant name
        transaction_date: Transaction date string
        resolution_notes: Resolution notes
        dispute_category: Category of dispute
        created_at: When dispute was created
        resolved_at: When dispute was resolved
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        smtp_config = get_smtp_config()
        
        # Validate SMTP configuration
        if not smtp_config.get("username") or not smtp_config.get("password"):
            logger.warning("[EMAIL] SMTP credentials not configured. Skipping email send.")
            return False
        
        # Create message
        message = MIMEMultipart("alternative")
        message["From"] = f"{smtp_config['from_name']} <{smtp_config['from_email']}>"
        message["To"] = customer_email
        message["Subject"] = f"✅ Your Dispute #{ticket_id} Has Been Approved"
        
        # Generate email content
        text_content = generate_approval_email_text(
            customer_name=customer_name,
            ticket_id=ticket_id,
            transaction_amount=transaction_amount,
            merchant_name=merchant_name,
            transaction_date=transaction_date,
            resolution_notes=resolution_notes,
            dispute_category=dispute_category,
            created_at=created_at,
            resolved_at=resolved_at
        )
        
        html_content = generate_approval_email_html(
            customer_name=customer_name,
            ticket_id=ticket_id,
            transaction_amount=transaction_amount,
            merchant_name=merchant_name,
            transaction_date=transaction_date,
            resolution_notes=resolution_notes,
            dispute_category=dispute_category,
            created_at=created_at,
            resolved_at=resolved_at
        )
        
        # Attach parts
        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        message.attach(part1)
        message.attach(part2)
        
        # Send email
        logger.info(f"[EMAIL] Sending approval email to {customer_email} for ticket #{ticket_id}")
        logger.debug(f"[EMAIL] Using SMTP server: {smtp_config['host']}:{smtp_config['port']} (use_tls={smtp_config['use_tls']}, start_tls={smtp_config['start_tls']})")
        
        await aiosmtplib.send(
            message,
            hostname=smtp_config["host"],
            port=smtp_config["port"],
            username=smtp_config["username"],
            password=smtp_config["password"],
            use_tls=smtp_config["use_tls"],
            start_tls=smtp_config["start_tls"],
            timeout=30
        )
        
        logger.success(f"[EMAIL] Successfully sent approval email to {customer_email} for ticket #{ticket_id}")
        return True
        
    except aiosmtplib.SMTPException as e:
        logger.error(f"[EMAIL] SMTP error sending email to {customer_email}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"[EMAIL] Unexpected error sending email to {customer_email}: {str(e)}")
        return False


def send_dispute_approval_email_sync(
    customer_email: str,
    customer_name: str,
    ticket_id: int,
    transaction_amount: float,
    merchant_name: str,
    transaction_date: str,
    resolution_notes: str,
    dispute_category: str = "unknown",
    created_at: Optional[str] = None,
    resolved_at: Optional[str] = None
) -> bool:
    """
    Synchronous wrapper for sending dispute approval email.
    
    This function can be called from synchronous code and will handle
    the async event loop internally. It uses asyncio.run_coroutine_threadsafe
    to properly handle the case when called from an async context.
    
    Args:
        Same as send_dispute_approval_email
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        import threading
        import concurrent.futures
        
        # Create a new thread to run the async function
        # This avoids conflicts with the existing event loop
        def run_async():
            return asyncio.run(send_dispute_approval_email(
                customer_email, customer_name, ticket_id, transaction_amount,
                merchant_name, transaction_date, resolution_notes, dispute_category,
                created_at, resolved_at
            ))
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async)
            return future.result(timeout=30)  # 30 second timeout
            
    except Exception as e:
        logger.error(f"[EMAIL] Error in sync email wrapper: {str(e)}")
        return False


async def send_dispute_rejection_email(
    customer_email: str,
    customer_name: str,
    ticket_id: int,
    transaction_amount: float,
    merchant_name: str,
    transaction_date: str,
    resolution_notes: str,
    dispute_category: str = "unknown",
    created_at: Optional[str] = None,
    resolved_at: Optional[str] = None
) -> bool:
    """
    Send dispute rejection email notification to customer.
    
    Args:
        customer_email: Customer's email address
        customer_name: Customer's full name
        ticket_id: Dispute ticket ID
        transaction_amount: Transaction amount
        merchant_name: Merchant name
        transaction_date: Transaction date string
        resolution_notes: Resolution notes explaining rejection
        dispute_category: Category of dispute
        created_at: When dispute was created
        resolved_at: When dispute was resolved
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        smtp_config = get_smtp_config()
        
        # Validate SMTP configuration
        if not smtp_config.get("username") or not smtp_config.get("password"):
            logger.warning("[EMAIL] SMTP credentials not configured. Skipping email send.")
            return False
        
        # Create message
        message = MIMEMultipart("alternative")
        message["From"] = f"{smtp_config['from_name']} <{smtp_config['from_email']}>"
        message["To"] = customer_email
        message["Subject"] = f"❌ Dispute Decision for Ticket #{ticket_id}"
        
        # Generate email content
        text_content = generate_rejection_email_text(
            customer_name=customer_name,
            ticket_id=ticket_id,
            transaction_amount=transaction_amount,
            merchant_name=merchant_name,
            transaction_date=transaction_date,
            resolution_notes=resolution_notes,
            dispute_category=dispute_category,
            created_at=created_at,
            resolved_at=resolved_at
        )
        
        html_content = generate_rejection_email_html(
            customer_name=customer_name,
            ticket_id=ticket_id,
            transaction_amount=transaction_amount,
            merchant_name=merchant_name,
            transaction_date=transaction_date,
            resolution_notes=resolution_notes,
            dispute_category=dispute_category,
            created_at=created_at,
            resolved_at=resolved_at
        )
        
        # Attach parts
        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        message.attach(part1)
        message.attach(part2)
        
        # Send email
        logger.info(f"[EMAIL] Sending rejection email to {customer_email} for ticket #{ticket_id}")
        logger.debug(f"[EMAIL] Using SMTP server: {smtp_config['host']}:{smtp_config['port']} (use_tls={smtp_config['use_tls']}, start_tls={smtp_config['start_tls']})")
        
        await aiosmtplib.send(
            message,
            hostname=smtp_config["host"],
            port=smtp_config["port"],
            username=smtp_config["username"],
            password=smtp_config["password"],
            use_tls=smtp_config["use_tls"],
            start_tls=smtp_config["start_tls"],
            timeout=30
        )
        
        logger.success(f"[EMAIL] Successfully sent rejection email to {customer_email} for ticket #{ticket_id}")
        return True
        
    except aiosmtplib.SMTPException as e:
        logger.error(f"[EMAIL] SMTP error sending rejection email to {customer_email}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"[EMAIL] Unexpected error sending rejection email to {customer_email}: {str(e)}")
        return False


def send_dispute_rejection_email_sync(
    customer_email: str,
    customer_name: str,
    ticket_id: int,
    transaction_amount: float,
    merchant_name: str,
    transaction_date: str,
    resolution_notes: str,
    dispute_category: str = "unknown",
    created_at: Optional[str] = None,
    resolved_at: Optional[str] = None
) -> bool:
    """
    Synchronous wrapper for sending dispute rejection email.
    
    This function can be called from synchronous code and will handle
    the async event loop internally. It uses asyncio.run in a separate thread
    to properly handle the case when called from an async context.
    
    Args:
        Same as send_dispute_rejection_email
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        import threading
        import concurrent.futures
        
        # Create a new thread to run the async function
        # This avoids conflicts with the existing event loop
        def run_async():
            return asyncio.run(send_dispute_rejection_email(
                customer_email, customer_name, ticket_id, transaction_amount,
                merchant_name, transaction_date, resolution_notes, dispute_category,
                created_at, resolved_at
            ))
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async)
            return future.result(timeout=30)  # 30 second timeout
            
    except Exception as e:
        logger.error(f"[EMAIL] Error in sync rejection email wrapper: {str(e)}")
        return False