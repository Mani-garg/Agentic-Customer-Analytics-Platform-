"""Domain entities and value objects."""

from datetime import date, datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from customer_analytics.domain.enums import CustomerSegment, OrderStatus, RiskTier


class TransactionRecord(BaseModel):
    """Raw or validated e-commerce transaction entity."""

    model_config = ConfigDict(frozen=True)

    order_id: str
    customer_id: str
    order_date: datetime
    product_id: Optional[str] = None
    category: Optional[str] = "General"
    quantity: int = Field(gt=0)
    unit_price: float = Field(ge=0.0)
    discount: float = Field(default=0.0, ge=0.0, le=1.0)
    country: Optional[str] = "US"
    order_status: OrderStatus = OrderStatus.COMPLETED
    currency: str = "USD"

    @property
    def line_gross_revenue(self) -> float:
        """Gross revenue: quantity * unit_price."""
        return round(self.quantity * self.unit_price, 4)

    @property
    def line_net_revenue(self) -> float:
        """Net revenue accounting for line discount."""
        return round(self.line_gross_revenue * (1.0 - self.discount), 4)


class RFMScore(BaseModel):
    """Recency, Frequency, Monetary values and quantiles for a customer."""

    model_config = ConfigDict(frozen=True)

    customer_id: str
    recency_days: int = Field(ge=0)
    frequency: int = Field(ge=1)
    monetary_value: float = Field(ge=0.0)
    r_score: int = Field(ge=1, le=5)
    f_score: int = Field(ge=1, le=5)
    m_score: int = Field(ge=1, le=5)
    rfm_score_str: str  # e.g., '555', '421'
    segment: CustomerSegment


class SegmentSummary(BaseModel):
    """Aggregated analytical profile of a customer segment."""

    segment: CustomerSegment
    customer_count: int
    customer_percentage: float
    total_revenue: float
    average_revenue_per_customer: float
    average_order_frequency: float
    average_recency_days: float
    high_risk_customer_count: int = 0
    retention_priority: str = "Standard"


class CustomerFeatureRecord(BaseModel):
    """Customer-level feature vector for modeling and inference."""

    customer_id: str
    observation_date: date
    recency_days: int
    frequency: int
    monetary_value: float
    average_order_value: float
    customer_tenure_days: int
    days_since_first_purchase: int
    purchase_gap_mean: float
    purchase_gap_std: float
    historical_order_count: int
    historical_revenue: float
    segment: Optional[str] = None
    churn_label: Optional[int] = None  # None during unlabeled inference
    label_window_end: Optional[date] = None
    feature_generation_version: str = "v1.0.0"


class ChurnPredictionResult(BaseModel):
    """Output contract for churn inference on a single customer."""

    customer_id: str
    churn_probability: float = Field(ge=0.0, le=1.0)
    is_churn_predicted: bool
    risk_tier: RiskTier
    operating_threshold: float
    model_version: str
    explanation: str
    timestamp: datetime


class SimulationScenario(BaseModel):
    """Input configuration for a what-if discount simulation."""

    scenario_id: str
    name: str
    target_population: str
    discount_percentage: float = Field(ge=0.0, le=0.90)
    max_discount_per_customer: float = Field(gt=0.0)
    expected_redemption_rate: float = Field(ge=0.0, le=1.0)
    estimated_retention_probability: float = Field(ge=0.0, le=1.0)
    expected_future_revenue_per_retained: float = Field(ge=0.0)
    campaign_cost_per_contacted: float = Field(default=0.0, ge=0.0)
    max_customers_to_contact: Optional[int] = Field(default=None, gt=0)


class SimulationResult(BaseModel):
    """Structured financial and operational outputs from a simulation scenario."""

    scenario_id: str
    name: str
    eligible_customers: int
    contacted_customers: int
    expected_redeemed_customers: int
    expected_retained_customers: int
    gross_revenue_per_retained: float
    estimated_discount_expenditure: float
    estimated_campaign_expenditure: float
    total_cost: float
    estimated_incremental_revenue: float
    estimated_net_incremental_value: float
    roi_percentage: Optional[float]
    net_value_per_contacted: float
    warnings: List[str] = Field(default_factory=list)
    is_causal_estimate: bool = False
    disclaimer: str


class DataQualityReport(BaseModel):
    """Structured report documenting data ingestion and validation results."""

    dataset_name: str
    timestamp: datetime
    records_read: int
    records_accepted: int
    records_rejected: int
    rejection_rate: float
    reasons_breakdown: Dict[str, int]
    checks_passed: bool
    warnings: List[str] = Field(default_factory=list)
