"""Cohort retention analysis for customer cohorts based on first purchase date."""

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def compute_cohort_retention(
    transactions_df: pd.DataFrame,
    max_cohorts: int = 12,
    max_periods: int = 6,
) -> pd.DataFrame:
    """Compute monthly cohort retention matrix showing percentage of cohort active in subsequent months."""
    if transactions_df.empty:
        return pd.DataFrame()

    df = transactions_df.copy()
    df["order_dt"] = pd.to_datetime(df["order_date"])
    df["order_period"] = df["order_dt"].dt.to_period("M")

    # Determine cohort month (first purchase month) per customer
    customer_cohort = df.groupby("customer_id")["order_period"].min().reset_index()
    customer_cohort.rename(columns={"order_period": "cohort_period"}, inplace=True)

    df = df.merge(customer_cohort, on="customer_id", how="left")

    # Group by cohort_period and order_period, count distinct customers
    grouped = df.groupby(["cohort_period", "order_period"])["customer_id"].nunique().reset_index()
    grouped.rename(columns={"customer_id": "active_customers"}, inplace=True)

    # Calculate period offset (number of months since cohort start)
    grouped["period_offset"] = (
        grouped["order_period"].dt.year - grouped["cohort_period"].dt.year
    ) * 12 + (grouped["order_period"].dt.month - grouped["cohort_period"].dt.month)

    # Filter out negative periods if any and limit max periods
    grouped = grouped[grouped["period_offset"] >= 0]
    grouped = grouped[grouped["period_offset"] <= max_periods]

    # Pivot into matrix
    pivot = grouped.pivot(
        index="cohort_period", columns="period_offset", values="active_customers"
    ).fillna(0)

    # Calculate retention rates as proportion of Month 0
    cohort_sizes = pivot[0] if 0 in pivot.columns else pd.Series(dtype=float)
    retention_matrix = pivot.divide(cohort_sizes, axis=0).round(4)

    # Retain the most recent max_cohorts
    retention_matrix = retention_matrix.tail(max_cohorts)
    return retention_matrix
