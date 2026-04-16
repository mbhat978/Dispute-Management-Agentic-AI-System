"""
Centralized configuration for the Dispute Management System.

This module configures Loguru to intercept standard logging and ensures
proper log streaming for asynchronous operations.
"""
import sys
import logging
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
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Intercept standard logging to route through Loguru
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            # Get corresponding Loguru level if it exists
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            # Find caller from where originated the logged message
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )
    
    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    logger.info("Logging configuration initialized successfully")

# Made with Bob
