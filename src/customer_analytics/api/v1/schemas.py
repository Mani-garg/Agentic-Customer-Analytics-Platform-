"""API request and response schemas for versioned endpoints."""

from datetime import date, datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from customer_analytics.domain.enums import RiskTier


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str
    timestamp: datetime
    app_env: str
    version: str
    details: Optional[Dict[str, str]] = None


class OverviewMetricsResponse(BaseModel):
    """Analytical overview response."""

    total_customers: int
    total_gross_revenue: float
    avg_revenue_per_customer: float
    avg_order_frequency: float
    avg_recency_days: float
    scored_customers: int = 0
    high_risk_customers: int = 0
    average_churn_probability: float = 0.0


class ChurnSummaryResponse(BaseModel):
    """Churn model summary response."""

    model_ready: bool
    model_version: str
    operating_threshold: float
    training_samples: int
    metrics: Dict[str, Any]
    active_scored_customers: int
    high_risk_customers_count: int
    average_churn_probability: float


class ChurnPredictionRequest(BaseModel):
    """Customer features payload for churn inference."""

    customer_id: str = "CUST-00001"
    observation_date: date = Field(default_factory=date.today)
    recency_days: int = Field(ge=0)
    frequency: int = Field(ge=1)
    monetary_value: float = Field(ge=0.0)
    average_order_value: float = Field(ge=0.0)
    customer_tenure_days: int = Field(ge=0)
    days_since_first_purchase: int = Field(ge=0)
    purchase_gap_mean: float = Field(ge=0.0)
    purchase_gap_std: float = Field(ge=0.0)
    historical_order_count: int = Field(ge=1)
    historical_revenue: float = Field(ge=0.0)


class ChurnPredictionResponse(BaseModel):
    """Prediction inference response."""

    customer_id: str
    churn_probability: float
    is_churn_predicted: bool
    risk_tier: RiskTier
    operating_threshold: float
    model_version: str
    explanation: str
    timestamp: datetime


class HighRiskCustomerResponse(BaseModel):
    """Restricted high-risk customer item for prioritization."""

    customer_id: str
    churn_probability: float
    risk_tier: str
    operating_threshold: float
    segment: str
    recency_days: int
    frequency: int
    monetary_value: float


class AgentAskRequest(BaseModel):
    """Natural-language query payload."""

    question: str = Field(
        min_length=3, max_length=500, description="Analytics inquiry in plain language"
    )
    request_id: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standardized API error response."""

    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    correlation_id: str
    timestamp: datetime
