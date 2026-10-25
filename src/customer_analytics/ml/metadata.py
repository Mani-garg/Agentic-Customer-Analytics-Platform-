"""Model metadata tracking and lineage documentation."""

from datetime import datetime, timezone
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from customer_analytics.data.schemas import MODEL_FEATURE_NAMES


class ModelTrainingMetadata(BaseModel):
    """Metadata capturing model training provenance, configuration, and data partition counts."""

    model_name: str = "XGBoostChurnClassifier"
    model_version: str = "v1.0.0"
    training_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    feature_names: List[str] = Field(default_factory=lambda: list(MODEL_FEATURE_NAMES))
    operating_threshold: float
    seed: int
    train_size: int
    val_size: int
    test_size: int
    train_positive_count: int
    train_negative_count: int
    scale_pos_weight: float
    hyperparameters: Dict[str, Any]
    metrics: Dict[str, Any]
