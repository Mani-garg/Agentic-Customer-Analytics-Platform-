"""Strongly-typed analytics tools for the agent with bounded execution behavior."""

import json
from typing import Any, Optional

from pydantic import BaseModel, Field

from customer_analytics.data.repository import AnalyticsRepository
from customer_analytics.domain.models import SimulationScenario
from customer_analytics.observability.metrics import (
    get_all_metric_definitions,
    get_metric_definition,
)
from customer_analytics.simulation.engine import SimulationEngine

# Pydantic Tool Input Schemas


class OverviewMetricsInput(BaseModel):
    """Input for retrieving high-level business metrics."""

    pass


class RFMSegmentSummaryInput(BaseModel):
    """Input for retrieving RFM segment profiles."""

    segment_name: Optional[str] = Field(
        default=None, description="Optional specific segment filter"
    )


class ChurnSummaryInput(BaseModel):
    """Input for retrieving model churn risk overview."""

    pass


class TopCustomersInput(BaseModel):
    """Input for retrieving top customers ranked by lifetime spend."""

    limit: int = Field(default=10, ge=1, le=50, description="Number of top customers to return")


class CustomerRiskSummaryInput(BaseModel):
    """Input for retrieving customer churn risk summary."""

    customer_id: Optional[str] = Field(default=None, description="Optional customer ID lookup")
    limit: int = Field(
        default=20, ge=1, le=50, description="Max high risk customers if no customer_id provided"
    )


class CategoryPerformanceInput(BaseModel):
    """Input for retrieving product category performance."""

    category_name: Optional[str] = Field(default=None, description="Optional category filter")


class ReadOnlySQLInput(BaseModel):
    """Input for executing guarded read-only analytics SQL."""

    query: str = Field(description="Single read-only SELECT statement adhering to SQL guardrails")


class SimulateDiscountInput(BaseModel):
    """Input for running what-if discount simulation."""

    discount_percentage: float = Field(
        default=0.15, ge=0.01, le=0.90, description="Discount rate between 0.01 and 0.90"
    )
    expected_redemption_rate: float = Field(
        default=0.30, ge=0.01, le=1.0, description="Redemption probability"
    )
    estimated_retention_probability: float = Field(
        default=0.60, ge=0.01, le=1.0, description="Retention probability"
    )
    campaign_cost_per_contacted: float = Field(
        default=1.50, ge=0.0, description="Cost per contacted customer"
    )


class MetricDefinitionInput(BaseModel):
    """Input for retrieving documented metric formulas."""

    metric_name: str = Field(
        description="Name of the metric (e.g. 'gross_revenue', 'average_order_value')"
    )


class SupportedSchemaInput(BaseModel):
    """Input for retrieving allow-listed database schemas."""

    pass


class AnalyticsToolsRegistry:
    """Registry providing bound tools to the agent with data repository injection."""

    def __init__(self, repo: AnalyticsRepository, sim_engine: Optional[SimulationEngine] = None):
        self.repo = repo
        self.sim_engine = sim_engine or SimulationEngine()

    def get_overview_metrics(self, **kwargs: Any) -> str:
        """Retrieve total revenue, active customers, orders, AOV, and churn risk overview."""
        metrics = self.repo.get_overview_metrics()
        return json.dumps(metrics)

    def get_rfm_segment_summary(self, segment_name: Optional[str] = None, **kwargs: Any) -> str:
        """Retrieve RFM segment profiles with customer counts, percentages, and revenue contributions."""
        summaries = self.repo.get_segment_summaries()
        if segment_name:
            filtered = [
                s.model_dump()
                for s in summaries
                if s.segment.value.lower() == segment_name.strip().lower()
            ]
            return json.dumps(
                filtered if filtered else {"error": f"Segment '{segment_name}' not found."}
            )
        return json.dumps([s.model_dump() for s in summaries])

    def get_churn_summary(self, **kwargs: Any) -> str:
        """Retrieve churn model summary, operating threshold, and risk tier counts."""
        metrics = self.repo.get_overview_metrics()
        summary = {
            "total_scored_customers": metrics.get("scored_customers", 0),
            "high_risk_customers": metrics.get("high_risk_customers", 0),
            "average_churn_probability": metrics.get("average_churn_probability", 0.0),
            "risk_distribution_interpretation": "Prioritize high-risk tier customers with substantial monetary value.",
        }
        return json.dumps(summary)

    def get_top_customers(self, limit: int = 10, **kwargs: Any) -> str:
        """Retrieve top customers ranked by lifetime monetary value."""
        clamped_limit = min(50, max(1, limit))
        sql = f"SELECT customer_id, segment, monetary_value, frequency, recency_days FROM rfm_segments ORDER BY monetary_value DESC LIMIT {clamped_limit}"
        rows = self.repo.execute_guarded_sql(sql, max_rows=clamped_limit)
        return json.dumps(rows)

    def get_customer_risk_summary(
        self, customer_id: Optional[str] = None, limit: int = 20, **kwargs: Any
    ) -> str:
        """Retrieve churn risk score and profile for a specific customer or highest risk customers."""
        if customer_id:
            sql = f"SELECT c.customer_id, c.churn_probability, c.risk_tier, r.segment, r.monetary_value, r.frequency, r.recency_days FROM churn_risk_scores c JOIN rfm_segments r ON c.customer_id = r.customer_id WHERE c.customer_id = '{customer_id.strip()}' LIMIT 1"
            rows = self.repo.execute_guarded_sql(sql, max_rows=1)
            return json.dumps(
                rows[0] if rows else {"error": f"Customer '{customer_id}' not found."}
            )
        clamped = min(50, max(1, limit))
        rows = self.repo.get_high_risk_customers(limit=clamped)
        return json.dumps(rows)

    def get_category_performance(self, category_name: Optional[str] = None, **kwargs: Any) -> str:
        """Retrieve sales breakdown by product category."""
        return json.dumps(
            {
                "message": "Category performance aggregates are accessible via daily/transaction aggregates.",
                "categories_available": [
                    "Electronics",
                    "Apparel",
                    "Home & Kitchen",
                    "Books",
                    "Health & Beauty",
                    "Sports & Outdoors",
                ],
            }
        )

    def execute_read_only_analytics_sql(self, query: str, **kwargs: Any) -> str:
        """Execute a guarded read-only SELECT query against allow-listed analytical tables."""
        try:
            rows = self.repo.execute_guarded_sql(query, max_rows=100)
            return json.dumps(rows)
        except Exception as e:
            return json.dumps({"error": str(e), "status": "REJECTED_BY_SQL_GUARD"})

    def simulate_discount_strategy(
        self,
        discount_percentage: float = 0.15,
        expected_redemption_rate: float = 0.30,
        estimated_retention_probability: float = 0.60,
        campaign_cost_per_contacted: float = 1.50,
        **kwargs: Any,
    ) -> str:
        """Simulate financial outcomes of a customer discount campaign under specified assumptions."""
        metrics = self.repo.get_overview_metrics()
        eligible_count = metrics.get("high_risk_customers", 100)
        if eligible_count == 0:
            eligible_count = metrics.get("total_customers", 100)
        avg_spend = metrics.get("avg_revenue_per_customer", 120.0)

        scenario = SimulationScenario(
            scenario_id="agent_sim",
            name=f"Agent Simulated {int(discount_percentage * 100)}% Discount",
            target_population="high_risk_customers",
            discount_percentage=discount_percentage,
            max_discount_per_customer=50.0,
            expected_redemption_rate=expected_redemption_rate,
            estimated_retention_probability=estimated_retention_probability,
            expected_future_revenue_per_retained=avg_spend,
            campaign_cost_per_contacted=campaign_cost_per_contacted,
        )

        result = self.sim_engine.simulate_scenario(
            scenario, customer_count=eligible_count, avg_monetary=avg_spend
        )
        return json.dumps(result.model_dump())

    def get_supported_schema(self, **kwargs: Any) -> str:
        """Retrieve schema of allow-listed analytical tables."""
        tables_info = {
            "rfm_segments": [
                "customer_id",
                "recency_days",
                "frequency",
                "monetary_value",
                "r_score",
                "f_score",
                "m_score",
                "rfm_score_str",
                "segment",
            ],
            "customer_features": [
                "customer_id",
                "observation_date",
                "recency_days",
                "frequency",
                "monetary_value",
                "average_order_value",
                "customer_tenure_days",
                "days_since_first_purchase",
                "purchase_gap_mean",
                "purchase_gap_std",
                "historical_order_count",
                "historical_revenue",
                "segment",
                "churn_label",
            ],
            "segment_summaries": [
                "segment",
                "customer_count",
                "customer_percentage",
                "total_revenue",
                "average_revenue_per_customer",
                "average_order_frequency",
                "average_recency_days",
                "retention_priority",
            ],
            "churn_risk_scores": [
                "customer_id",
                "churn_probability",
                "is_churn_predicted",
                "risk_tier",
                "operating_threshold",
                "model_version",
                "scored_at",
            ],
        }
        return json.dumps(tables_info)

    def get_metric_definition(self, metric_name: str, **kwargs: Any) -> str:
        """Retrieve official business formula and unit for a metric."""
        try:
            m = get_metric_definition(metric_name)
            return json.dumps(m)
        except KeyError as e:
            return json.dumps(
                {"error": str(e), "available_metrics": list(get_all_metric_definitions())}
            )
