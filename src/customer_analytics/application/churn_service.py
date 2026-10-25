"""Application service for customer churn risk inference and prioritization."""

from typing import Any, Dict, List

from customer_analytics.data.repository import AnalyticsRepository
from customer_analytics.domain.models import ChurnPredictionResult, CustomerFeatureRecord
from customer_analytics.ml.predict import ChurnInferenceService


class ChurnService:
    """Orchestrates churn prediction inference and high-risk customer querying."""

    def __init__(self, inference_service: ChurnInferenceService, repository: AnalyticsRepository):
        self.inference = inference_service
        self.repo = repository

    def get_summary(self) -> Dict[str, Any]:
        """Retrieve model metadata, operating threshold, and risk distribution."""
        overview = self.repo.get_overview_metrics()
        meta = self.inference.metadata
        return {
            "model_ready": self.inference.is_ready(),
            "model_version": meta.model_version if meta else "unloaded",
            "operating_threshold": meta.operating_threshold if meta else 0.5,
            "training_samples": meta.train_size if meta else 0,
            "metrics": meta.metrics if meta else {},
            "active_scored_customers": overview.get("scored_customers", 0),
            "high_risk_customers_count": overview.get("high_risk_customers", 0),
            "average_churn_probability": overview.get("average_churn_probability", 0.0),
        }

    def predict_churn(self, features: CustomerFeatureRecord) -> ChurnPredictionResult:
        """Score customer churn risk."""
        return self.inference.predict_customer_risk(features)

    def get_high_risk_customers(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Retrieve paginated high risk customers."""
        return self.repo.get_high_risk_customers(limit=limit, offset=offset)
