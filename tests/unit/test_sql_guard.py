"""Unit tests for SQL Guard parsing, allow-listing, and limit enforcement."""

import pytest

from customer_analytics.agent.sql_guard import SQLGuard
from customer_analytics.exceptions import UnsafeSQLException


def test_sql_guard_accepts_valid_select():
    """Valid read-only SELECT against allow-listed table must be accepted and sanitized."""
    guard = SQLGuard(allowed_tables={"rfm_segments", "churn_risk_scores"})
    query = "SELECT customer_id, monetary_value FROM rfm_segments WHERE monetary_value > 100"
    sanitized = guard.validate_and_sanitize(query)
    assert "SELECT" in sanitized
    assert "FROM rfm_segments" in sanitized
    assert "LIMIT 100" in sanitized  # Default injected limit


def test_sql_guard_rejects_unauthorized_table():
    """Query referencing an unapproved table must be rejected."""
    guard = SQLGuard(allowed_tables={"rfm_segments"})
    query = "SELECT * FROM secret_passwords"
    with pytest.raises(UnsafeSQLException) as exc_info:
        guard.validate_and_sanitize(query)
    assert "unauthorized table" in str(exc_info.value).lower()


def test_sql_guard_caps_excessive_limit():
    """Limit exceeding max_rows must be clamped down."""
    guard = SQLGuard(allowed_tables={"rfm_segments"}, max_rows=50)
    query = "SELECT * FROM rfm_segments LIMIT 500"
    sanitized = guard.validate_and_sanitize(query)
    assert "LIMIT 50" in sanitized
