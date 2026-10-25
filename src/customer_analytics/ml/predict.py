"""Model inference service with input validation, feature alignment, and risk explanation."""

import logging
from datetime import datetime, timezone
from typing import List, Optional

import pandas as pd
import xgboost as xgb

from customer_analytics.domain.contracts import ModelInferenceInterface
from customer_analytics.domain.enums import RiskTier
from customer_analytics.domain.models import ChurnPredictionResult, CustomerFeatureRecord
from customer_analytics.exceptions import ModelInferenceException
from customer_analytics.features.feature_schema import validate_inference_features
from customer_analytics.ml.artifacts import load_model_artifacts
from customer_analytics.ml.metadata import ModelTrainingMetadata

logger = logging.getLogger(__name__)


class ChurnInferenceService(ModelInferenceInterface):
    """Production inference engine for scoring customer churn risk."""

    def __init__(self, artifact_dir: str = "./artifacts/models"):
        self.artifact_dir = artifact_dir
        self.model: Optional[xgb.XGBClassifier] = None
        self.metadata: Optional[ModelTrainingMetadata] = None
        self._load()

    def _load(self) -> None:
        """Load and cache model binary and training metadata."""
        try:
            self.model, self.metadata = load_model_artifacts(self.artifact_dir)
        except Exception as e:
            logger.warning(f"ChurnInferenceService initialized without trained model: {e}")
            self.model = None
            self.metadata = None

    def is_ready(self) -> bool:
        """Check whether model and metadata are loaded and ready for inference."""
        return self.model is not None and self.metadata is not None

    def predict_customer_risk(
        self,
        features: CustomerFeatureRecord,
    ) -> ChurnPredictionResult:
        """Score a single customer's churn risk."""
        if not self.is_ready():
            raise ModelInferenceException(
                "Model is not initialized or trained artifacts are missing."
            )

        # Convert record to 1-row DataFrame
        df_row = pd.DataFrame([features.model_dump()])
        results = self._predict_dataframe(df_row)
        return results[0]

    def predict_batch(
        self,
        features_list: List[CustomerFeatureRecord],
    ) -> List[ChurnPredictionResult]:
        """Score multiple customers in batch."""
        if not self.is_ready():
            raise ModelInferenceException(
                "Model is not initialized or trained artifacts are missing."
            )

        if not features_list:
            return []

        df_batch = pd.DataFrame([f.model_dump() for f in features_list])
        return self._predict_dataframe(df_batch)

    def _predict_dataframe(self, df: pd.DataFrame) -> List[ChurnPredictionResult]:
        """Internal scoring method executing matrix prediction and risk categorization."""
        # Validate feature presence and alignment
        feature_matrix = validate_inference_features(df).values
        probs = self.model.predict_proba(feature_matrix)[:, 1]

        threshold = self.metadata.operating_threshold
        version = self.metadata.model_version
        now = datetime.now(timezone.utc)

        results: List[ChurnPredictionResult] = []
        for i, prob in enumerate(probs):
            prob_float = round(float(prob), 4)
            is_churn = prob_float >= threshold

            # Categorize Risk Tier
            if prob_float >= threshold:
                tier = RiskTier.HIGH
            elif prob_float >= (threshold * 0.6):
                tier = RiskTier.MEDIUM
            else:
                tier = RiskTier.LOW

            # Generate grounded evidence explanation
            row = df.iloc[i]
            recency = row.get("recency_days", 0)
            frequency = row.get("frequency", 1)
            spend = row.get("monetary_value", 0.0)

            explanation = (
                f"Customer has {recency} days recency, {frequency} historical orders, "
                f"and ${spend:.2f} lifetime spend. Churn risk estimated at {prob_float * 100:.1f}% "
                f"(threshold: {threshold:.2f}, risk tier: {tier.value.upper()})."
            )

            results.append(
                ChurnPredictionResult(
                    customer_id=str(row["customer_id"]),
                    churn_probability=prob_float,
                    is_churn_predicted=is_churn,
                    risk_tier=tier,
                    operating_threshold=threshold,
                    model_version=version,
                    explanation=explanation,
                    timestamp=now,
                )
            )

        return results
