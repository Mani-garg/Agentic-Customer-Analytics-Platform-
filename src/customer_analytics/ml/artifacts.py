"""Artifact persistence and secure loading for churn models and schemas."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import xgboost as xgb

from customer_analytics.exceptions import (
    IncompatibleModelVersionException,
    MissingArtifactException,
)
from customer_analytics.ml.metadata import ModelTrainingMetadata
from customer_analytics.utils.serialization import to_json

logger = logging.getLogger(__name__)


def save_model_artifacts(
    model: xgb.XGBClassifier,
    metadata: ModelTrainingMetadata,
    artifact_dir: Union[str, Path],
    evaluation_report: Optional[Dict[str, Any]] = None,
) -> Path:
    """Persist XGBoost model binary, training metadata, threshold config, and evaluation report."""
    base_dir = Path(artifact_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    # 1. Save model binary using XGBoost native format (JSON or UBJ)
    model_path = base_dir / "churn_xgb_model.json"
    model.save_model(str(model_path))

    # 2. Save metadata JSON
    metadata_path = base_dir / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        f.write(to_json(metadata.model_dump()))

    # 3. Save threshold config
    threshold_path = base_dir / "threshold_config.json"
    threshold_data = {
        "operating_threshold": metadata.operating_threshold,
        "model_version": metadata.model_version,
        "feature_names": metadata.feature_names,
    }
    with open(threshold_path, "w", encoding="utf-8") as f:
        json.dump(threshold_data, f, indent=2)

    # 4. Save evaluation report if provided
    if evaluation_report is not None:
        report_path = base_dir / "evaluation_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(to_json(evaluation_report))

    logger.info(f"Model artifacts successfully persisted to {base_dir.resolve()}")
    return base_dir


def load_model_artifacts(
    artifact_dir: Union[str, Path],
) -> Tuple[xgb.XGBClassifier, ModelTrainingMetadata]:
    """Securely load and validate XGBoost model and associated metadata."""
    base_dir = Path(artifact_dir)
    model_path = base_dir / "churn_xgb_model.json"
    metadata_path = base_dir / "metadata.json"

    if not model_path.exists():
        raise MissingArtifactException(f"Model artifact not found: {model_path.resolve()}")
    if not metadata_path.exists():
        raise MissingArtifactException(f"Model metadata not found: {metadata_path.resolve()}")

    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata_dict = json.load(f)
        metadata = ModelTrainingMetadata(**metadata_dict)
    except Exception as e:
        raise IncompatibleModelVersionException(f"Failed to parse model metadata: {e}") from e

    try:
        model = xgb.XGBClassifier()
        model.load_model(str(model_path))
    except Exception as e:
        raise IncompatibleModelVersionException(f"Failed to load XGBoost model binary: {e}") from e

    logger.info(
        f"Loaded model version {metadata.model_version} from {base_dir.resolve()} "
        f"(operating threshold: {metadata.operating_threshold})"
    )
    return model, metadata
