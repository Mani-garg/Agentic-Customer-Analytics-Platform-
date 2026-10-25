"""Deterministic RFM (Recency, Frequency, Monetary) calculation and quantile scoring."""

import logging
from datetime import date, datetime
from typing import Union

import pandas as pd

from customer_analytics.utils.dates import parse_date

logger = logging.getLogger(__name__)


def compute_rfm_raw(
    transactions_df: pd.DataFrame,
    observation_date: Union[date, datetime],
) -> pd.DataFrame:
    """Aggregate customer-level Recency, Frequency, and Monetary metrics relative to observation cutoff."""
    if transactions_df.empty:
        return pd.DataFrame(columns=["customer_id", "recency_days", "frequency", "monetary_value"])

    obs_date = parse_date(observation_date)
    df = transactions_df.copy()
    df["order_date_dt"] = pd.to_datetime(df["order_date"]).dt.date

    # Filter to orders strictly at or before observation date
    df_window = df[df["order_date_dt"] <= obs_date].copy()
    if df_window.empty:
        return pd.DataFrame(columns=["customer_id", "recency_days", "frequency", "monetary_value"])

    # Aggregation per customer:
    # Recency: obs_date - max(order_date_dt)
    # Frequency: distinct order_id count
    # Monetary: sum of line_gross_revenue (or derived from quantity * unit_price)
    if "line_gross_revenue" not in df_window.columns:
        if "unit_price" in df_window.columns and "quantity" in df_window.columns:
            df_window["line_gross_revenue"] = (
                pd.to_numeric(df_window["quantity"], errors="coerce").fillna(1)
                * pd.to_numeric(df_window["unit_price"], errors="coerce").fillna(0.0)
            ).round(2)
        else:
            df_window["line_gross_revenue"] = pd.to_numeric(
                df_window["quantity"], errors="coerce"
            ).fillna(0.0)

    revenue_col = "line_gross_revenue"

    grouped = (
        df_window.groupby("customer_id")
        .agg(
            last_order_date=("order_date_dt", "max"),
            frequency=("order_id", "nunique"),
            monetary_value=(revenue_col, "sum"),
        )
        .reset_index()
    )

    grouped["recency_days"] = grouped["last_order_date"].apply(lambda d: (obs_date - d).days)
    grouped["monetary_value"] = grouped["monetary_value"].round(2)

    return grouped[["customer_id", "recency_days", "frequency", "monetary_value"]]


def score_quantiles(
    series: pd.Series,
    n_bins: int = 5,
    ascending: bool = True,
) -> pd.Series:
    """Score a series into 1..n_bins based on quantiles with robust tie-breaking and duplicate handling."""
    if len(series) == 0:
        return pd.Series(dtype=int)

    # If all values are identical or count is less than n_bins, assign median score
    if series.nunique() <= 1 or len(series) < n_bins:
        mid_score = (n_bins // 2) + 1
        return pd.Series([mid_score] * len(series), index=series.index, dtype=int)

    # Use percent_rank to break ties smoothly across duplicate boundaries
    ranks = series.rank(method="first", ascending=ascending)
    scores = pd.qcut(ranks, q=n_bins, labels=False, duplicates="drop")
    # Convert 0..4 to 1..5
    return (scores + 1).astype(int)


def assign_rfm_scores(
    rfm_df: pd.DataFrame,
    n_bins: int = 5,
) -> pd.DataFrame:
    """Assign 1..5 scores to R, F, M metrics. Recency has fewer days = higher score."""
    if rfm_df.empty:
        df = rfm_df.copy()
        df["r_score"] = 0
        df["f_score"] = 0
        df["m_score"] = 0
        df["rfm_score_str"] = ""
        return df

    df = rfm_df.copy()

    # Recency: fewer days is better -> ascending=False for rank scoring
    df["r_score"] = score_quantiles(df["recency_days"], n_bins=n_bins, ascending=False)
    # Frequency: more orders is better -> ascending=True
    df["f_score"] = score_quantiles(df["frequency"], n_bins=n_bins, ascending=True)
    # Monetary: more spend is better -> ascending=True
    df["m_score"] = score_quantiles(df["monetary_value"], n_bins=n_bins, ascending=True)

    df["rfm_score_str"] = (
        df["r_score"].astype(str) + df["f_score"].astype(str) + df["m_score"].astype(str)
    )

    return df
