"""Request context and correlation ID tracking using contextvars."""

import contextvars
import uuid
from typing import Optional

# Thread/async safe context variable for correlation ID
_correlation_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "correlation_id", default=None
)


def get_correlation_id() -> str:
    """Retrieve current correlation ID or generate a new one if not set."""
    cid = _correlation_id_ctx.get()
    if not cid:
        cid = str(uuid.uuid4())
        _correlation_id_ctx.set(cid)
    return cid


def set_correlation_id(correlation_id: str) -> None:
    """Explicitly set correlation ID for the current context."""
    _correlation_id_ctx.set(correlation_id)


def clear_correlation_id() -> None:
    """Clear correlation ID from current context."""
    _correlation_id_ctx.set(None)
