"""Abstract domain interfaces defining platform boundaries."""

from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Dict, List, Optional

import pandas as pd

from customer_analytics.domain.models import (
    ChurnPredictionResult,
    CustomerFeatureRecord,
    RFMScore,
    SegmentSummary,
    SimulationResult,
    SimulationScenario,
)


class AnalyticsEngineInterface(ABC):
    """Abstract interface for scalable transaction aggregation and RFM computation."""

    @abstractmethod
    def compute_rfm_metrics(
        self,
        transactions_df: pd.DataFrame,
        observation_date: date,
    ) -> List[RFMScore]:
        """Compute RFM scores and assign segments for customers."""
        pass

    @abstractmethod
    def build_customer_features(
        self,
        transactions_df: pd.DataFrame,
        observation_date: date,
        churn_horizon_days: Optional[int] = None,
    ) -> List[CustomerFeatureRecord]:
        """Construct customer feature vectors with optional future churn label."""
        pass


class PersistenceRepositoryInterface(ABC):
    """Abstract interface for data access and analytical persistence."""

    @abstractmethod
    def get_overview_metrics(self) -> Dict[str, Any]:
        """Retrieve high-level business metrics across the loaded dataset."""
        pass

    @abstractmethod
    def get_segment_summaries(self) -> List[SegmentSummary]:
        """Retrieve aggregated segment summaries."""
        pass

    @abstractmethod
    def get_high_risk_customers(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Retrieve high-risk churn customers with restricted fields."""
        pass

    @abstractmethod
    def execute_guarded_sql(self, sql: str, max_rows: int = 100) -> List[Dict[str, Any]]:
        """Execute a validated read-only SQL query."""
        pass


class ModelInferenceInterface(ABC):
    """Abstract interface for churn risk inference."""

    @abstractmethod
    def predict_customer_risk(self, features: CustomerFeatureRecord) -> ChurnPredictionResult:
        """Score customer churn risk."""
        pass

    @abstractmethod
    def predict_batch(
        self, features_list: List[CustomerFeatureRecord]
    ) -> List[ChurnPredictionResult]:
        """Batch score churn risk for multiple customers."""
        pass


class SimulationEngineInterface(ABC):
    """Abstract interface for discount and retention revenue simulation."""

    @abstractmethod
    def simulate_scenario(
        self, scenario: SimulationScenario, customer_count: int, avg_monetary: float
    ) -> SimulationResult:
        """Run a deterministic revenue recovery simulation."""
        pass

    @abstractmethod
    def compare_scenarios(
        self,
        scenarios: List[SimulationScenario],
        customer_count: int,
        avg_monetary: float,
    ) -> List[SimulationResult]:
        """Compare multiple simulation scenarios on equal footing."""
        pass
