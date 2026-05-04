"""
Centralized configuration for the Dispute Management System.

This module configures Loguru to intercept standard logging and ensures
proper log streaming for asynchronous operations.
"""
import sys
import logging
import os
from loguru import logger


def setup_logging():
    """
    Configure Loguru for the application.
    
    - Removes default handler
    - Adds stdout handler with enqueue=True for thread-safe logging
    - Intercepts standard logging to route through Loguru
    - Enables colorized output for better readability
    """
    # Remove default Loguru handler
    logger.remove()
    
    # Add stdout handler with enqueue=True for thread-safe async logging
    logger.add(
        sys.stdout,
        colorize=True,
        enqueue=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"  # Set minimum level to INFO to filter out DEBUG logs
    )
    
    # Intercept standard logging to route through Loguru
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            # Filter out ALL DEBUG logs from external libraries
            if record.levelno < logging.INFO:
                return  # Skip all DEBUG logs
            
            # Get corresponding Loguru level if it exists
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            # Find caller from where originated the logged message
            frame, depth = logging.currentframe(), 2
            while frame and frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                if frame:
                    depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )
    
    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Silence noisy third-party loggers
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    
    logger.info("Logging configuration initialized successfully")

# SMTP Email Configuration
def get_smtp_config():
    """
    Load SMTP configuration from environment variables.
    
    Returns:
        dict: SMTP configuration dictionary with the following keys:
            - host: SMTP server hostname
            - port: SMTP server port
            - username: SMTP authentication username
            - password: SMTP authentication password
            - from_email: Email address to send from
            - from_name: Display name for the sender
            - use_tls: Whether to use implicit TLS (for port 465)
            - start_tls: Whether to use STARTTLS (for port 587)
    """
    port = int(os.getenv("SMTP_PORT", "587"))

    # For port 587, use STARTTLS; for port 465, use implicit TLS
    if port == 587:
        use_tls = False
        start_tls = True
    elif port == 465:
        use_tls = True
        start_tls = False
    else:
        # Custom port - check environment variable
        use_tls = os.getenv("SMTP_USE_TLS", "false").lower() == "true"
        start_tls = os.getenv("SMTP_START_TLS", "true").lower() == "true"

    smtp_username = os.getenv("SMTP_USERNAME", "")
    smtp_from_email = os.getenv("SMTP_FROM_EMAIL", "")
    
    # If SMTP_FROM_EMAIL is not set, use the username as from_email
    if not smtp_from_email and smtp_username:
        smtp_from_email = smtp_username
    
    return {
        "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "port": port,
        "username": smtp_username,
        "password": os.getenv("SMTP_PASSWORD", ""),
        "from_email": smtp_from_email,
        "from_name": os.getenv("SMTP_FROM_NAME", "Dispute Management System"),
        "use_tls": use_tls,
        "start_tls": start_tls,
    }

# Made with Bob
