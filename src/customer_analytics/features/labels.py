"""Temporal churn target definition and label generation."""

import logging
from datetime import date, datetime, timedelta
from typing import Union

import pandas as pd

from customer_analytics.utils.dates import parse_date

logger = logging.getLogger(__name__)


def construct_churn_labels(
    transactions_df: pd.DataFrame,
    observation_cutoff: Union[date, datetime],
    horizon_days: int = 90,
) -> pd.DataFrame:
    """Generate binary churn labels for customers based on future purchasing behavior.

    A customer who was active on or before observation_cutoff is labeled as:
      - churn_label = 0: placed at least 1 eligible order in (observation_cutoff, observation_cutoff + horizon_days]
      - churn_label = 1: placed 0 eligible orders in (observation_cutoff, observation_cutoff + horizon_days]
    """
    if transactions_df.empty:
        return pd.DataFrame(columns=["customer_id", "churn_label", "future_orders_count"])

    cutoff_d = parse_date(observation_cutoff)
    horizon_end_d = cutoff_d + timedelta(days=horizon_days)

    df = transactions_df.copy()
    df["order_date_dt"] = pd.to_datetime(df["order_date"]).dt.date

    # 1. Identify cohort of customers active on or before cutoff date
    historical_df = df[df["order_date_dt"] <= cutoff_d]
    active_customers = historical_df["customer_id"].unique()

    if len(active_customers) == 0:
        return pd.DataFrame(columns=["customer_id", "churn_label", "future_orders_count"])

    # 2. Look exclusively into the future prediction window (cutoff_d, horizon_end_d]
    future_df = df[(df["order_date_dt"] > cutoff_d) & (df["order_date_dt"] <= horizon_end_d)]

    # Count distinct orders in future window per customer
    future_orders = (
        future_df.groupby("customer_id")["order_id"]
        .nunique()
        .reset_index(name="future_orders_count")
    )

    # 3. Merge with active customer base
    label_df = pd.DataFrame({"customer_id": active_customers})
    label_df = label_df.merge(future_orders, on="customer_id", how="left")
    label_df["future_orders_count"] = label_df["future_orders_count"].fillna(0).astype(int)

    # Churn = 1 if 0 orders in horizon, else 0
    label_df["churn_label"] = (label_df["future_orders_count"] == 0).astype(int)

    churn_rate = label_df["churn_label"].mean()
    logger.info(
        f"Churn labels computed at cutoff {cutoff_d} (horizon: {horizon_days}d): "
        f"{len(label_df)} customers, churn rate = {churn_rate * 100:.2f}%"
    )

    return label_df[["customer_id", "churn_label", "future_orders_count"]]
