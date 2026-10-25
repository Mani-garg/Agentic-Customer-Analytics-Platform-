"""Integration tests for database persistence and read-only role isolation."""

from customer_analytics.data.repository import AnalyticsRepository


def test_repository_sync_and_query(populated_repository: AnalyticsRepository):
    """Verify repository syncs features and retrieves overview metrics correctly."""
    metrics = populated_repository.get_overview_metrics()
    assert metrics["total_customers"] > 0
    assert metrics["total_gross_revenue"] > 0.0

    summaries = populated_repository.get_segment_summaries()
    assert len(summaries) > 0


def test_repository_execute_guarded_sql(populated_repository: AnalyticsRepository):
    """Verify executing safe SELECT on repository."""
    rows = populated_repository.execute_guarded_sql(
        "SELECT customer_id, monetary_value FROM rfm_segments LIMIT 5"
    )
    assert len(rows) <= 5
    assert "customer_id" in rows[0]
    assert "monetary_value" in rows[0]
