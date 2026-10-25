"""Integration tests for the analytics tools registry and deterministic fallback query router."""

import json

from customer_analytics.agent.fallback import DeterministicQueryRouter
from customer_analytics.agent.tools import AnalyticsToolsRegistry
from customer_analytics.data.repository import AnalyticsRepository


def test_agent_tools_registry(populated_repository: AnalyticsRepository):
    """Verify core analytics tools return valid JSON outputs."""
    tools = AnalyticsToolsRegistry(populated_repository)

    # 1. Overview metrics
    overview = json.loads(tools.get_overview_metrics())
    assert "total_customers" in overview
    assert overview["total_customers"] > 0

    # 2. Segment summary
    segments = json.loads(tools.get_rfm_segment_summary())
    assert len(segments) > 0

    # 3. Top customers
    top_c = json.loads(tools.get_top_customers(limit=3))
    assert len(top_c) <= 3

    # 4. Metric definition
    definition = json.loads(tools.get_metric_definition("gross_revenue"))
    assert definition["name"] == "gross_revenue"


def test_deterministic_router_inquiries(populated_repository: AnalyticsRepository):
    """Verify deterministic query router answers supported questions with evidence."""
    tools = AnalyticsToolsRegistry(populated_repository)
    router = DeterministicQueryRouter(tools)

    resp = router.answer_question("Which customer segments contribute the most revenue?")
    assert resp.fallback_used is True
    assert "RFM segmentation" in resp.answer
    assert "get_rfm_segment_summary" in resp.source_tools

    resp_churn = router.answer_question("What is our churn risk overview?")
    assert resp_churn.fallback_used is True
    assert "churn" in resp_churn.intent
