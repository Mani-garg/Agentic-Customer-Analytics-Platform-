"""Feature schema definitions and validation utilities."""

import pandas as pd

from customer_analytics.data.schemas import MODEL_FEATURE_NAMES
from customer_analytics.exceptions import MissingRequiredFeatureException


def validate_inference_features(features_df: pd.DataFrame) -> pd.DataFrame:
    """Validate that required model features exist and are arranged in training order."""
    missing = [f for f in MODEL_FEATURE_NAMES if f not in features_df.columns]
    if missing:
        raise MissingRequiredFeatureException(
            f"Input features missing required predictive columns: {missing}",
            details={"missing": missing, "required": MODEL_FEATURE_NAMES},
        )

    # Return exactly the required features in the exact feature ordering
    ordered_df = features_df[MODEL_FEATURE_NAMES].copy()

    # Fill any internal NaN with 0.0 for numerical stability
    ordered_df = ordered_df.fillna(0.0)
    return ordered_df
