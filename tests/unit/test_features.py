"""Unit tests for customer feature engineering and temporal isolation."""

from datetime import date

import pandas as pd

from customer_analytics.features.build_features import build_customer_feature_table
from customer_analytics.features.feature_schema import validate_inference_features
from customer_analytics.features.leakage_checks import verify_temporal_leakage_safety


def test_build_customer_feature_table(sample_transactions_df: pd.DataFrame):
    """Verify that features contain all required analytical and predictive dimensions."""
    cutoff = date(2026, 6, 30)
    features = build_customer_feature_table(
        transactions_df=sample_transactions_df,
        observation_cutoff=cutoff,
        churn_horizon_days=90,
    )

    assert not features.empty
    expected_cols = [
        "customer_id",
        "recency_days",
        "frequency",
        "monetary_value",
        "average_order_value",
        "customer_tenure_days",
        "days_since_first_purchase",
        "purchase_gap_mean",
        "purchase_gap_std",
        "churn_label",
    ]
    for col in expected_cols:
        assert col in features.columns, f"Expected column {col} in feature table"

    # Validate inference alignment
    ordered_matrix = validate_inference_features(features)
    assert len(ordered_matrix.columns) == 10


def test_temporal_leakage_isolation(sample_transactions_df: pd.DataFrame):
    """Verify that adding future transactions beyond cutoff T does NOT alter feature vectors at T."""
    cutoff = date(2026, 6, 30)
    is_safe, msg = verify_temporal_leakage_safety(
        transactions_df=sample_transactions_df,
        observation_cutoff=cutoff,
        churn_horizon_days=90,
    )
    assert is_safe is True
    assert "Zero future leakage" in msg
