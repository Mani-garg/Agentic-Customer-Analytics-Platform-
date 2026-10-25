"""Analytics overview and business metric definitions endpoints."""

from typing import Dict, List

from fastapi import APIRouter, Depends

from customer_analytics.api.dependencies import get_analytics_service
from customer_analytics.api.v1.schemas import OverviewMetricsResponse
from customer_analytics.application.analytics_service import AnalyticsService
from customer_analytics.observability.metrics import get_all_metric_definitions

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/overview",
    response_model=OverviewMetricsResponse,
    summary="Get Overview Analytics",
    description="Retrieve high-level business metrics including active customers, total gross revenue, and churn concentration.",
)
def get_overview(
    service: AnalyticsService = Depends(get_analytics_service),
) -> OverviewMetricsResponse:
    metrics = service.get_overview()
    return OverviewMetricsResponse(
        total_customers=metrics.get("total_customers", 0),
        total_gross_revenue=metrics.get("total_gross_revenue", 0.0),
        avg_revenue_per_customer=metrics.get("avg_revenue_per_customer", 0.0),
        avg_order_frequency=metrics.get("avg_order_frequency", 0.0),
        avg_recency_days=metrics.get("avg_recency_days", 0.0),
        scored_customers=metrics.get("scored_customers", 0),
        high_risk_customers=metrics.get("high_risk_customers", 0),
        average_churn_probability=metrics.get("average_churn_probability", 0.0),
    )


@router.get(
    "/metrics",
    response_model=List[Dict[str, str]],
    summary="Get Central Metric Definitions",
    description="Retrieve centralized definitions, mathematical formulas, and units for all metrics.",
)
def list_metrics() -> List[Dict[str, str]]:
    return get_all_metric_definitions()
