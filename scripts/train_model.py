#!/usr/bin/env python3
"""CLI script to train churn prediction models with baseline comparison and threshold selection."""

import argparse
import sys
from pathlib import Path

import pandas as pd

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from customer_analytics.data.repository import AnalyticsRepository
from customer_analytics.ml.predict import ChurnInferenceService
from customer_analytics.ml.train import train_churn_model


def main():
    parser = argparse.ArgumentParser(description="Train customer churn model.")
    parser.add_argument(
        "--features",
        "-f",
        default="data/processed/customer_features.parquet",
        help="Path to customer feature Parquet",
    )
    parser.add_argument(
        "--artifact-dir", "-a", default="artifacts/models", help="Artifact storage directory"
    )
    parser.add_argument("--seed", "-s", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--min-precision",
        "-p",
        type=float,
        default=0.35,
        help="Minimum precision constraint for threshold tuning",
    )
    args = parser.parse_args()

    print(f"Loading customer features from {args.features}...")
    df = pd.read_parquet(args.features)
    print(f"Loaded {len(df):,} customer records. Starting model training pipeline...")

    model, metadata, report = train_churn_model(
        feature_df=df,
        artifact_dir=args.artifact_dir,
        seed=args.seed,
        min_precision=args.min_precision,
    )

    print("\n================ MODEL EVALUATION SUMMARY ================")
    print(f"Model Version:         {metadata.model_version}")
    print(f"Operating Threshold:   {metadata.operating_threshold:.3f}")
    print(f"Class Imbalance Weight (scale_pos_weight): {metadata.scale_pos_weight:.2f}")

    xgb_metrics = report["xgb_test_metrics"]["metrics"]
    dummy_metrics = report["baseline_dummy_metrics"]["metrics"]
    logreg_metrics = report["baseline_logreg_metrics"]["metrics"]

    print("\nHeld-Out Test Partition Benchmark:")
    print(
        f"{'Metric':<20} | {'Dummy Baseline':<16} | {'Logistic Regression':<20} | {'XGBoost (Tuned)':<16}"
    )
    print("-" * 80)
    for m in ["recall", "precision", "f1_score", "pr_auc", "roc_auc", "brier_score"]:
        d_val = dummy_metrics.get(m, 0.0)
        l_val = logreg_metrics.get(m, 0.0)
        x_val = xgb_metrics.get(m, 0.0)
        print(f"{m:<20} | {d_val:<16.4f} | {l_val:<20.4f} | {x_val:<16.4f}")

    cm = report["xgb_test_metrics"]["confusion_matrix"]
    print("\nXGBoost Test Confusion Matrix:")
    print(f"  TP: {cm['true_positives']} | FP: {cm['false_positives']}")
    print(f"  FN: {cm['false_negatives']} | TN: {cm['true_negatives']}")

    # Batch score current customer base and store in database
    print("\nGenerating batch predictions for active customer population...")
    inference = ChurnInferenceService(artifact_dir=args.artifact_dir)
    feature_records = df.to_dict(orient="records")
    from customer_analytics.domain.models import CustomerFeatureRecord

    parsed_records = [CustomerFeatureRecord(**r) for r in feature_records]
    results = inference.predict_batch(parsed_records)

    pred_df = pd.DataFrame([r.model_dump() for r in results])
    repo = AnalyticsRepository()
    repo.sync_churn_predictions_to_db(pred_df)
    print(f"Scored and persisted {len(pred_df):,} customer risk profiles to database.")
    print("================ MODEL TRAINING COMPLETED SUCCESSFULLY ================\n")


if __name__ == "__main__":
    main()
