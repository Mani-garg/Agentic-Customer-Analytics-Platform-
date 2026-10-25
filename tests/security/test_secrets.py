"""Security tests verifying that secrets and credentials are never exposed in logs or outputs."""

from customer_analytics.logging_config import redact_secrets


def test_redact_api_keys_and_passwords():
    """Verify that credentials in text logs are masked."""
    sample_log = (
        "Error connecting with api_key='sk-abcdef1234567890' and password='super_secret_password'"
    )
    redacted = redact_secrets(sample_log)
    assert "sk-abcdef1234567890" not in redacted
    assert "super_secret_password" not in redacted
    assert "***REDACTED***" in redacted


def test_redact_postgres_connection_uri():
    """Verify that database passwords in connection URIs are masked."""
    db_uri = "postgresql://analytics_app:my_super_secret_pass@localhost:5432/analytics_db"
    redacted = redact_secrets(db_uri)
    assert "my_super_secret_pass" not in redacted
    assert "***REDACTED***" in redacted
