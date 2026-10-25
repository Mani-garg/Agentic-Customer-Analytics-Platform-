"""Structured and safe logging configuration."""

import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict

from customer_analytics.observability.request_context import get_correlation_id

# Regex patterns for redacting sensitive values
SECRET_PATTERNS = [
    re.compile(r"(api[-_]?key\s*[:=]\s*['\"]?)([\w\-]+)(['\"]?)", re.IGNORECASE),
    re.compile(r"(password\s*[:=]\s*['\"]?)([\w\-]+)(['\"]?)", re.IGNORECASE),
    re.compile(r"(postgres(?:ql)?://\w+:)([^@]+)(@)", re.IGNORECASE),
]


def redact_secrets(text: str) -> str:
    """Mask credentials and keys from logged messages."""
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(r"\1***REDACTED***\3", redacted)
    return redacted


class StructuredJsonFormatter(logging.Formatter):
    """Custom formatter emitting JSON objects with correlation ID and ISO timestamps."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_secrets(record.getMessage()),
            "correlation_id": get_correlation_id(),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_fields"):
            log_entry["extra"] = record.extra_fields
        return json.dumps(log_entry)


class StandardFormatter(logging.Formatter):
    """Clean standard formatter with correlation ID and secret redaction."""

    def format(self, record: logging.LogRecord) -> str:
        record.msg = redact_secrets(str(record.msg))
        cid = get_correlation_id()
        record.correlation_id = cid[:8] if cid else "none"  # type: ignore[attr-defined]
        return super().format(record)


def setup_logging(log_level: str = "INFO", json_format: bool = False) -> None:
    """Initialize root and application loggers."""
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())

    # Remove existing handlers to avoid duplicates
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    if json_format:
        stream_handler.setFormatter(StructuredJsonFormatter())
    else:
        stream_handler.setFormatter(
            StandardFormatter(
                fmt="%(asctime)s [%(levelname)s] [%(correlation_id)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
    root_logger.addHandler(stream_handler)
