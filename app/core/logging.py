"""
Enhanced logging configuration with structured logging support.
"""
import logging
import sys

from app.core.config import settings


class StructuredFormatter(logging.Formatter):

    def format(self, record: logging.LogRecord) -> str:
        if hasattr(record, "request_id"):
            record.msg = f"[Request-ID: {record.request_id}] {record.msg}"
        return super().format(record)


def setup_logging() -> None:
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    formatter = StructuredFormatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = [console_handler]

    app_logger = logging.getLogger("looks_lab")
    app_logger.setLevel(log_level)


setup_logging()
logger = logging.getLogger("looks_lab")

