#!/usr/bin/env python3
"""CLI script to validate raw e-commerce transaction data."""

import argparse
import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from customer_analytics.data.ingestion import ingest_transactions_csv
from customer_analytics.data.validation import validate_transactions
from customer_analytics.utils.serialization import to_json


def main():
    parser = argparse.ArgumentParser(description="Validate raw transaction dataset.")
    parser.add_argument("--input", "-i", default="data/raw/transactions.csv", help="Input CSV path")
    parser.add_argument(
        "--report",
        "-r",
        default="artifacts/reports/data_quality_report.json",
        help="Report output path",
    )
    args = parser.parse_args()

    print(f"Reading raw data from {args.input}...")
    df = ingest_transactions_csv(args.input)
    print(f"Loaded {len(df):,} records. Running data quality validation...")

    accepted, rejected, report = validate_transactions(df, dataset_name=Path(args.input).name)

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(to_json(report.model_dump()))

    print("\n================ DATA QUALITY REPORT ================")
    print(f"Records Read:     {report.records_read:,}")
    print(f"Records Accepted: {report.records_accepted:,}")
    print(f"Records Rejected: {report.records_rejected:,} ({report.rejection_rate * 100:.2f}%)")
    print(f"Quality Status:   {'PASSED' if report.checks_passed else 'FAILED'}")
    if report.reasons_breakdown:
        print("Rejection Breakdown:")
        for reason, count in report.reasons_breakdown.items():
            print(f"  - {reason}: {count}")
    if report.warnings:
        print("Warnings:")
        for w in report.warnings:
            print(f"  - [WARNING] {w}")
    print(f"Saved full JSON quality report to: {report_path.resolve()}\n")


if __name__ == "__main__":
    main()
