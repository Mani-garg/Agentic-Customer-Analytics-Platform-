#!/usr/bin/env python3
"""CLI script to inspect and evaluate persisted model artifacts."""

import argparse
import json
import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from customer_analytics.ml.artifacts import load_model_artifacts


def main():
    parser = argparse.ArgumentParser(description="Evaluate saved model artifacts.")
    parser.add_argument(
        "--artifact-dir", "-a", default="artifacts/models", help="Model artifact directory"
    )
    parser.add_argument(
        "--report-dir", "-r", default="artifacts/reports", help="Evaluation report directory"
    )
    args = parser.parse_args()

    art_dir = Path(args.artifact_dir)
    print(f"Loading model artifacts from {art_dir.resolve()}...")
    model, metadata = load_model_artifacts(art_dir)

    print("\n================ SAVED MODEL METADATA ================")
    print(f"Model Name:          {metadata.model_name}")
    print(f"Version:             {metadata.model_version}")
    print(f"Operating Threshold: {metadata.operating_threshold:.3f}")
    print(f"Trained Timestamp:   {metadata.training_timestamp}")
    print(
        f"Train/Val/Test Split:{metadata.train_size} / {metadata.val_size} / {metadata.test_size}"
    )
    print(f"Scale Pos Weight:    {metadata.scale_pos_weight}")
    print(f"Feature Count:       {len(metadata.feature_names)}")

    report_path = art_dir / "evaluation_report.json"
    if report_path.exists():
        with open(report_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)
        metrics = report_data.get("xgb_test_metrics", {}).get("metrics", {})
        print("\nTest Partition Evaluation Metrics:")
        for k, v in metrics.items():
            print(f"  - {k:<20}: {v}")
    print("=======================================================\n")


if __name__ == "__main__":
    main()
