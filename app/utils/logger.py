"""
Custom logging configuration for RE-VERSE application.
"""
import logging
import sys
from app.core.config import settings


def setup_logger():
    """
    Configure and return application logger.
    """
    # Create logger
    logger = logging.getLogger("reverse")
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


# Global logger instance
logger = setup_logger()
