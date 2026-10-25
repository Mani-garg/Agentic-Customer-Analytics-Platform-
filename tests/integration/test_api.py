"""Integration tests for FastAPI endpoints."""

from starlette.testclient import TestClient


def test_health_endpoints(test_client: TestClient):
    """Verify liveness and readiness health endpoints."""
    live_resp = test_client.get("/health/live")
    assert live_resp.status_code == 200
    assert live_resp.json()["status"] == "live"

    ready_resp = test_client.get("/health/ready")
    assert ready_resp.status_code == 200
    assert "ready" in ready_resp.json()["status"]


def test_analytics_overview(test_client: TestClient):
    """Verify overview metrics endpoint."""
    resp = test_client.get("/api/v1/analytics/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_customers" in data
    assert "total_gross_revenue" in data
    assert data["total_customers"] > 0


def test_segmentation_endpoints(test_client: TestClient):
    """Verify segments listing and single segment fetch."""
    resp = test_client.get("/api/v1/segments")
    assert resp.status_code == 200
    segments = resp.json()
    assert len(segments) > 0

    first_name = segments[0]["segment"]
    detail_resp = test_client.get(f"/api/v1/segments/{first_name}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["segment"] == first_name


def test_agent_ask_endpoint(test_client: TestClient):
    """Verify natural-language analytics agent inquiry endpoint."""
    payload = {"question": "Which customer segments contribute the most revenue?"}
    resp = test_client.post("/api/v1/agent/ask", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert "intent" in data
    assert len(data["source_tools"]) > 0


def test_simulation_discount_endpoint(test_client: TestClient):
    """Verify discount simulation endpoint."""
    payload = {
        "scenario_name": "Test Win-Back",
        "target_population": "all_customers",
        "discount_percentage": 0.15,
        "max_discount_per_customer": 40.0,
        "expected_redemption_rate": 0.25,
        "estimated_retention_probability": 0.50,
    }
    resp = test_client.post("/api/v1/simulations/discount", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "estimated_net_incremental_value" in data
    assert "contacted_customers" in data
    assert data["is_causal_estimate"] is False
