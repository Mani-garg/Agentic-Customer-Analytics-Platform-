"""Integration tests for the end-to-end analytical and training pipeline."""

import tempfile
from datetime import date
from pathlib import Path

from customer_analytics.data.cleaning import clean_transactions
from customer_analytics.data.synthetic import generate_synthetic_transactions
from customer_analytics.data.validation import validate_transactions
from customer_analytics.features.build_features import build_customer_feature_table
from customer_analytics.ml.train import train_churn_model


def test_full_pipeline_flow():
    """Verify data generation -> validation -> cleaning -> feature building -> model training."""
    # 1. Generate small dataset
    df_raw = generate_synthetic_transactions(n_customers=60, seed=123)
    assert len(df_raw) > 50

    # 2. Validate
    accepted, rejected, report = validate_transactions(df_raw)
    assert report.checks_passed is True

    # 3. Clean
    cleaned, stats = clean_transactions(accepted)
    assert stats["final_rows"] > 0

    # 4. Feature table
    cutoff = date(2026, 6, 30)
    features = build_customer_feature_table(
        cleaned, observation_cutoff=cutoff, churn_horizon_days=90
    )
    assert not features.empty
    assert "churn_label" in features.columns

    # 5. Train model
    with tempfile.TemporaryDirectory() as tmp_art_dir:
        model, metadata, eval_report = train_churn_model(
            feature_df=features,
            artifact_dir=tmp_art_dir,
            seed=42,
            min_precision=0.20,
        )
        assert model is not None
        assert metadata.model_version == "v1.0.0"
        assert "precision" in eval_report["xgb_test_metrics"]["metrics"]
        assert (Path(tmp_art_dir) / "churn_xgb_model.json").exists()
