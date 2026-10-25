"""Domain enumerations for customer analytics, segmentation, churn, and simulation."""

from enum import Enum


class OrderStatus(str, Enum):
    """Transaction fulfillment statuses."""

    COMPLETED = "completed"
    SHIPPED = "shipped"
    PENDING = "pending"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class CustomerSegment(str, Enum):
    """Interpretable customer segment classifications based on RFM quantiles."""

    CHAMPIONS = "Champions"
    LOYAL_CUSTOMERS = "Loyal Customers"
    POTENTIAL_LOYALISTS = "Potential Loyalists"
    NEW_CUSTOMERS = "New Customers"
    PROMISING = "Promising"
    ABOUT_TO_SLEEP = "About to Sleep"
    AT_RISK = "At Risk"
    HIBERNATING = "Hibernating"
    UNCLASSIFIED = "Unclassified"


class RiskTier(str, Enum):
    """Categorical churn risk classifications."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SimulationTargetPopulation(str, Enum):
    """Target cohort options for retention discount simulations."""

    ALL_CUSTOMERS = "all_customers"
    HIGH_RISK_ONLY = "high_risk_only"
    AT_RISK_SEGMENT = "at_risk_segment"
    CHAMPIONS_AND_LOYAL = "champions_and_loyal"
    CUSTOM = "custom"
