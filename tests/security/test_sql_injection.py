"""Security tests verifying defense against SQL injection, stacked queries, DDL, DML, and catalog access."""

import pytest

from customer_analytics.agent.sql_guard import SQLGuard
from customer_analytics.exceptions import UnsafeSQLException


@pytest.fixture
def guard() -> SQLGuard:
    return SQLGuard(allowed_tables={"rfm_segments", "churn_risk_scores", "customer_features"})


def test_reject_stacked_queries(guard: SQLGuard):
    """Stacked queries separated by semicolon must be strictly rejected."""
    query = "SELECT * FROM rfm_segments; DROP TABLE rfm_segments;"
    with pytest.raises(UnsafeSQLException) as exc:
        guard.validate_and_sanitize(query)
    assert "multiple statements" in str(exc.value).lower()


@pytest.mark.parametrize(
    "dml_query",
    [
        "DELETE FROM rfm_segments WHERE customer_id = 'CUST-1'",
        "INSERT INTO rfm_segments (customer_id) VALUES ('CUST-HACK')",
        "UPDATE rfm_segments SET monetary_value = 999999",
        "TRUNCATE TABLE rfm_segments",
    ],
)
def test_reject_dml_queries(guard: SQLGuard, dml_query: str):
    """Data modification statements (INSERT, UPDATE, DELETE, TRUNCATE) must be rejected."""
    with pytest.raises(UnsafeSQLException):
        guard.validate_and_sanitize(dml_query)


@pytest.mark.parametrize(
    "ddl_query",
    [
        "DROP TABLE rfm_segments",
        "ALTER TABLE rfm_segments ADD COLUMN hacked TEXT",
        "CREATE TABLE backdoor (id INT)",
    ],
)
def test_reject_ddl_queries(guard: SQLGuard, ddl_query: str):
    """DDL operations (DROP, ALTER, CREATE) must be rejected."""
    with pytest.raises(UnsafeSQLException):
        guard.validate_and_sanitize(ddl_query)


@pytest.mark.parametrize(
    "catalog_query",
    [
        "SELECT * FROM sqlite_master",
        "SELECT * FROM sqlite_schema",
        "SELECT * FROM information_schema.tables",
        "SELECT * FROM pg_catalog.pg_tables",
        "PRAGMA table_info(rfm_segments)",
    ],
)
def test_reject_system_catalog_queries(guard: SQLGuard, catalog_query: str):
    """Access to system catalogs and metadata tables must be rejected."""
    with pytest.raises(UnsafeSQLException):
        guard.validate_and_sanitize(catalog_query)


def test_reject_comments(guard: SQLGuard):
    """SQL comments that could be used for token obfuscation must be rejected."""
    assert_queries = [
        "SELECT * FROM rfm_segments -- bypass",
        "SELECT * FROM /* comment */ rfm_segments",
    ]
    for q in assert_queries:
        with pytest.raises(UnsafeSQLException) as exc:
            guard.validate_and_sanitize(q)
        assert "comments" in str(exc.value).lower()
