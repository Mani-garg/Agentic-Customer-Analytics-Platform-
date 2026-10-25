"""Schemas for revenue-recovery discount simulations."""

from typing import List, Optional

from pydantic import BaseModel, Field


class DiscountSimulationRequest(BaseModel):
    """API request payload for executing a retention discount simulation."""

    scenario_name: str = "Standard 15% Win-Back Campaign"
    target_population: str = Field(
        default="at_risk_segment",
        description="Target population: 'all_customers', 'at_risk_segment', 'high_risk_only', 'champions_and_loyal'",
    )
    discount_percentage: float = Field(
        default=0.15, ge=0.01, le=0.90, description="Proposed discount rate (e.g. 0.15 for 15%)"
    )
    max_discount_per_customer: float = Field(
        default=50.0, gt=0.0, description="Dollar cap on discount subsidy per customer order"
    )
    expected_redemption_rate: float = Field(
        default=0.30,
        ge=0.01,
        le=1.0,
        description="Assumed proportion of contacted customers who redeem the discount",
    )
    estimated_retention_probability: float = Field(
        default=0.60, ge=0.01, le=1.0, description="Assumed retention probability given redemption"
    )
    expected_future_revenue_per_retained: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Expected future spend per retained customer. If None, derived from historical ARPU.",
    )
    campaign_cost_per_contacted: float = Field(
        default=1.50,
        ge=0.0,
        description="Fixed marketing outreach cost per contacted customer (SMS, email, catalog)",
    )
    max_customers_to_contact: Optional[int] = Field(
        default=None, gt=0, description="Optional capacity constraint on campaign outreach"
    )


class MultiScenarioComparisonRequest(BaseModel):
    """Request payload to compare multiple simulation scenarios on identical underlying populations."""

    scenarios: List[DiscountSimulationRequest] = Field(
        min_length=1, max_length=10, description="List of 1 to 10 discount scenarios to compare"
    )


class SensitivityAnalysisRequest(BaseModel):
    """Request to compute a 2D parameter sensitivity matrix (e.g. discount rate vs. redemption rate)."""

    base_scenario: DiscountSimulationRequest
    discount_rates: List[float] = Field(
        default=[0.05, 0.10, 0.15, 0.20, 0.25],
        description="Candidate discount percentages",
    )
    redemption_rates: List[float] = Field(
        default=[0.10, 0.20, 0.30, 0.40, 0.50],
        description="Candidate redemption rates",
    )
