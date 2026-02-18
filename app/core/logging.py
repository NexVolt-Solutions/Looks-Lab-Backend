"""
Enhanced logging configuration with structured logging support.
"""
import json
import logging
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import settings


# ── Formatters ────────────────────────────────────────────────────

class StructuredFormatter(logging.Formatter):
    """
    Plain text formatter for development.
    Includes request_id if present on log record.
    """
    def format(self, record: logging.LogRecord) -> str:
        if hasattr(record, "request_id"):
            record.msg = f"[{record.request_id}] {record.msg}"
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for production.
    Outputs structured logs for log aggregators (CloudWatch, Datadog, etc.)
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level":     record.levelname,
            "logger":    record.name,
            "message":   record.getMessage(),
            "module":    record.module,
            "function":  record.funcName,
            "line":      record.lineno,
        }

        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


# ── Setup ─────────────────────────────────────────────────────────

def setup_logging() -> None:
    """
    Configure application logging.
    - Development: plain text to console + file
    - Production:  JSON to console + rotating file
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    formatter = JSONFormatter() if settings.is_production else StructuredFormatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    handlers: list[logging.Handler] = []

    # ── Console Handler ───────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    handlers.append(console_handler)

    # ── File Handler ──────────────────────────────────────────
    try:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        file_handler = RotatingFileHandler(
            filename=log_dir / "app.log",
            maxBytes=10 * 1024 * 1024,  # 10MB per file
            backupCount=5,              # Keep last 5 files
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        handlers.append(file_handler)
    except Exception as e:
        print(f"Warning: Could not set up file logging: {e}", file=sys.stderr)

    # ── Root Logger ───────────────────────────────────────────
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = handlers

    # ── App Logger ────────────────────────────────────────────
    app_logger = logging.getLogger("looks_lab")
    app_logger.setLevel(log_level)

    # ── Silence Noisy Third-Party Loggers ─────────────────────
    noisy_loggers = {
        "sqlalchemy.engine":        logging.WARNING,
        "sqlalchemy.engine.Engine": logging.WARNING,
        "sqlalchemy.pool":          logging.WARNING,
        "sqlalchemy.orm":           logging.WARNING,
        "alembic":                  logging.WARNING,
        "uvicorn.access":           logging.WARNING,
        "uvicorn.error":            logging.INFO,
        "httpx":                    logging.WARNING,
        "httpcore":                 logging.WARNING,
        "google.generativeai":      logging.WARNING,
        "google.auth":              logging.WARNING,
        "botocore":                 logging.WARNING,
        "boto3":                    logging.WARNING,
        "PIL":                      logging.WARNING,
        "multipart":                logging.WARNING,
    }

    for logger_name, level in noisy_loggers.items():
        logging.getLogger(logger_name).setLevel(level)

    app_logger.info(
        f"Logging configured | "
        f"level={settings.LOG_LEVEL} | "
        f"env={settings.ENV} | "
        f"format={'json' if settings.is_production else 'text'}"
    )


# ── Logger Instance ───────────────────────────────────────────────
# setup_logging() is NOT called here.
# Called explicitly in main.py lifespan on startup.

logger = logging.getLogger("looks_lab")

