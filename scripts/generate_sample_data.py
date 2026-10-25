#!/usr/bin/env python3
"""CLI script to generate synthetic e-commerce transactions."""

import argparse
import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from customer_analytics.data.synthetic import generate_synthetic_transactions, save_synthetic_data


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic e-commerce transactions.")
    parser.add_argument(
        "--output", "-o", default="data/raw/transactions.csv", help="Output CSV path"
    )
    parser.add_argument(
        "--n-customers", "-n", type=int, default=1000, help="Number of unique customers"
    )
    parser.add_argument("--seed", "-s", type=int, default=42, help="Reproducibility random seed")
    args = parser.parse_args()

    print(
        f"Generating synthetic transactions for {args.n_customers} customers (seed={args.seed})..."
    )
    df = generate_synthetic_transactions(n_customers=args.n_customers, seed=args.seed)
    out_path = save_synthetic_data(df, args.output)
    print(
        f"Success! Generated {len(df):,} transactions across {df['customer_id'].nunique():,} customers."
    )
    print(f"Saved dataset to: {out_path.resolve()}")


if __name__ == "__main__":
    main()
