import json
import logging
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import settings


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if hasattr(record, "request_id"):
            record.msg = f"[{record.request_id}] {record.msg}"
        return super().format(record)


class JSONFormatter(logging.Formatter):
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


def setup_logging() -> None:
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    formatter = JSONFormatter() if settings.is_production else StructuredFormatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    handlers: list[logging.Handler] = []

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    handlers.append(console_handler)

    try:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = RotatingFileHandler(
            filename=log_dir / "app.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        handlers.append(file_handler)
    except Exception as e:
        print(f"Warning: Could not set up file logging: {e}", file=sys.stderr)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = handlers

    logging.getLogger("looks_lab").setLevel(log_level)

    for name, level in {
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
        "google.genai":             logging.WARNING,
        "google.auth":              logging.WARNING,
        "botocore":                 logging.WARNING,
        "boto3":                    logging.WARNING,
        "PIL":                      logging.WARNING,
        "multipart":                logging.WARNING,
    }.items():
        logging.getLogger(name).setLevel(level)

    logging.getLogger("looks_lab").info(
        f"Logging configured | level={settings.LOG_LEVEL} | env={settings.ENV} | "
        f"format={'json' if settings.is_production else 'text'}"
    )


logger = logging.getLogger("looks_lab")

