#!/usr/bin/env python3
"""CLI script to execute the full data engineering and analytical pipeline."""

import argparse
import sys
from datetime import date
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from customer_analytics.data.cleaning import clean_transactions
from customer_analytics.data.ingestion import ingest_transactions_csv
from customer_analytics.data.repository import AnalyticsRepository
from customer_analytics.data.validation import validate_transactions
from customer_analytics.features.build_features import build_customer_feature_table
from customer_analytics.features.leakage_checks import verify_temporal_leakage_safety


def main():
    parser = argparse.ArgumentParser(description="Run analytics and customer feature pipeline.")
    parser.add_argument(
        "--input", "-i", default="data/raw/transactions.csv", help="Input transaction CSV"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="data/processed/customer_features.parquet",
        help="Output Parquet path",
    )
    parser.add_argument(
        "--cutoff", "-c", default="2026-06-30", help="Observation cutoff date (YYYY-MM-DD)"
    )
    parser.add_argument("--horizon", type=int, default=90, help="Future churn horizon in days")
    args = parser.parse_args()

    print("================ RUNNING ANALYTICS PIPELINE ================")
    # 1. Ingestion
    print(f"Step 1: Ingesting transactions from {args.input}...")
    df_raw = ingest_transactions_csv(args.input)
    print(f"Loaded {len(df_raw):,} raw records.")

    # 2. Validation
    print("Step 2: Validating data quality...")
    accepted_df, rejected_df, report = validate_transactions(df_raw)
    if not report.checks_passed:
        print("ERROR: Ingestion validation failed. Aborting pipeline.")
        sys.exit(1)
    print(f"Accepted {len(accepted_df):,} records ({report.rejection_rate * 100:.2f}% rejected).")

    # 3. Cleaning
    print("Step 3: Cleaning transactions and standardizing monetary values...")
    cleaned_df, clean_stats = clean_transactions(accepted_df)
    print(f"Cleaned dataset: {clean_stats['final_rows']:,} eligible transaction items.")

    # 4. Leakage Verification
    cutoff_date = date.fromisoformat(args.cutoff)
    print(f"Step 4: Verifying temporal leakage isolation at cutoff {cutoff_date}...")
    leakage_safe, msg = verify_temporal_leakage_safety(
        cleaned_df, observation_cutoff=cutoff_date, churn_horizon_days=args.horizon
    )
    if not leakage_safe:
        print(f"CRITICAL ERROR: {msg}")
        sys.exit(1)
    print(f"PASSED: {msg}")

    # 5. Build Customer Features & Labels
    print(f"Step 5: Constructing customer feature table (horizon: {args.horizon}d)...")
    feature_df = build_customer_feature_table(
        transactions_df=cleaned_df,
        observation_cutoff=cutoff_date,
        churn_horizon_days=args.horizon,
    )
    print(
        f"Engineered {len(feature_df):,} customer feature records across {len(feature_df.columns)} dimensions."
    )

    # 6. Save Parquet
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    feature_df.to_parquet(out_path, index=False)
    print(f"Saved customer features to Parquet: {out_path.resolve()}")

    # 7. Database Synchronization
    print("Step 7: Synchronizing feature tables and segment summaries to relational persistence...")
    repo = AnalyticsRepository()
    synced = repo.sync_feature_dataframe_to_db(feature_df)
    print(f"Successfully synchronized {synced:,} customer records into relational database.")
    print("================ PIPELINE COMPLETED SUCCESSFULLY ================\n")


if __name__ == "__main__":
    main()
