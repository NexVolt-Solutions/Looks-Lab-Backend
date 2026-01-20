"""
Enhanced logging configuration with structured logging support.
"""
import logging
import sys
from typing import Any
from app.core.config import settings


class StructuredFormatter(logging.Formatter):
    """Formatter that adds request_id and other context to log messages."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Add request_id if present in extra
        if hasattr(record, "request_id"):
            record.msg = f"[Request-ID: {record.request_id}] {record.msg}"
        return super().format(record)


def setup_logging() -> None:
    """Configure logging based on settings."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Create formatter
    formatter = StructuredFormatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = [console_handler]
    
    # Application logger
    app_logger = logging.getLogger("looks_lab")
    app_logger.setLevel(log_level)


# Initialize logging
setup_logging()
logger = logging.getLogger("looks_lab")
