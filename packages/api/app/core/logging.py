"""Structured logging with request-scoped correlation IDs.

Every log line emitted while handling a request carries the same ``request_id``
(and ``user_id`` once the caller is authenticated), so the checkout →
payment → order-write chain can be reconstructed from a log aggregator with a
single filter. The context lives in :mod:`contextvars`, which means it follows
the request across ``await`` points and into FastAPI background tasks without
threading a logger argument through every function signature.
"""

import json
import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any, Optional

from app.config import settings

# Request-scoped context. Populated by RequestContextMiddleware, read by the
# log formatter and by anything that wants to stamp a correlation ID onto a row.
_request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
_user_id: ContextVar[Optional[str]] = ContextVar("user_id", default=None)

# Attributes LogRecord always carries; anything else was passed via `extra=`
# and belongs in the structured payload.
_RESERVED_ATTRS = frozenset(
    logging.LogRecord("", 0, "", 0, "", None, None).__dict__.keys()
) | {"asctime", "message", "taskName"}


def new_request_id() -> str:
    return uuid.uuid4().hex


def set_request_id(request_id: Optional[str]) -> None:
    _request_id.set(request_id)


def get_request_id() -> Optional[str]:
    return _request_id.get()


def set_user_id(user_id: Optional[str]) -> None:
    _user_id.set(user_id)


def get_user_id() -> Optional[str]:
    return _user_id.get()


class JsonFormatter(logging.Formatter):
    """One JSON object per line — the shape log shippers expect."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": settings.SERVICE_NAME,
            "environment": settings.ENVIRONMENT,
        }

        request_id = get_request_id()
        if request_id:
            payload["request_id"] = request_id
        user_id = get_user_id()
        if user_id:
            payload["user_id"] = user_id

        for key, value in record.__dict__.items():
            if key not in _RESERVED_ATTRS and not key.startswith("_"):
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


class ConsoleFormatter(logging.Formatter):
    """Human-readable format for local development."""

    def format(self, record: logging.LogRecord) -> str:
        request_id = get_request_id()
        prefix = f"[{request_id[:8]}] " if request_id else ""
        extras = {
            k: v
            for k, v in record.__dict__.items()
            if k not in _RESERVED_ATTRS and not k.startswith("_")
        }
        suffix = f" {extras}" if extras else ""
        base = f"{self.formatTime(record, '%H:%M:%S')} {record.levelname:<5} {prefix}{record.name}: {record.getMessage()}{suffix}"
        if record.exc_info:
            base = f"{base}\n{self.formatException(record.exc_info)}"
        return base


def configure_logging() -> None:
    """Install the root handler. Idempotent — safe to call from app startup."""
    formatter = JsonFormatter() if settings.LOG_FORMAT == "json" else ConsoleFormatter()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.LOG_LEVEL.upper())

    # uvicorn ships its own handlers; drop them so everything goes through ours
    # and inherits the correlation ID.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers = []
        logger.propagate = True

    # uvicorn.access duplicates our own request log line with no correlation ID.
    logging.getLogger("uvicorn.access").disabled = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
