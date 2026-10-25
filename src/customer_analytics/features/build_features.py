"""Customer feature table construction with strict temporal boundary enforcement."""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd

from customer_analytics.analytics.rfm import assign_rfm_scores, compute_rfm_raw
from customer_analytics.analytics.segmentation import assign_segments
from customer_analytics.features.labels import construct_churn_labels
from customer_analytics.utils.dates import parse_date

logger = logging.getLogger(__name__)


def build_customer_feature_table(
    transactions_df: pd.DataFrame,
    observation_cutoff: Union[date, datetime],
    churn_horizon_days: Optional[int] = 90,
    version: str = "v1.0.0",
) -> pd.DataFrame:
    """Build leakage-safe customer feature vectors evaluated strictly at observation_cutoff."""
    if transactions_df.empty:
        return pd.DataFrame()

    cutoff_d = parse_date(observation_cutoff)
    df = transactions_df.copy()
    df["order_date_dt"] = pd.to_datetime(df["order_date"]).dt.date

    # Enforce strict temporal filter: transactions at or before cutoff only!
    historical_df = df[df["order_date_dt"] <= cutoff_d].copy()
    if historical_df.empty:
        return pd.DataFrame()

    # Calculate base RFM and segment assignment
    raw_rfm = compute_rfm_raw(historical_df, observation_date=cutoff_d)
    scored_rfm = assign_rfm_scores(raw_rfm)
    segmented = assign_segments(scored_rfm)

    # Customer tenure and purchase gap statistics
    tenure_stats: List[Dict[str, Union[str, float, int]]] = []

    # Sort historical orders chronologically to compute inter-purchase gaps
    ordered_history = historical_df.sort_values(["customer_id", "order_date_dt"])

    for cid, group in ordered_history.groupby("customer_id"):
        # Distinct dates when orders were placed
        order_dates = sorted(group["order_date_dt"].drop_duplicates().tolist())
        min_date = order_dates[0]
        order_dates[-1]

        tenure_days = (cutoff_d - min_date).days
        days_since_first = tenure_days

        if len(order_dates) > 1:
            gaps = [(order_dates[i] - order_dates[i - 1]).days for i in range(1, len(order_dates))]
            gap_mean = float(np.mean(gaps))
            gap_std = float(np.std(gaps)) if len(gaps) > 1 else 0.0
        else:
            gap_mean = 0.0
            gap_std = 0.0

        tenure_stats.append(
            {
                "customer_id": cid,
                "customer_tenure_days": tenure_days,
                "days_since_first_purchase": days_since_first,
                "purchase_gap_mean": round(gap_mean, 2),
                "purchase_gap_std": round(gap_std, 2),
            }
        )

    tenure_df = pd.DataFrame(tenure_stats)

    # Merge features
    feature_df = segmented.merge(tenure_df, on="customer_id", how="left")
    feature_df["observation_date"] = cutoff_d
    feature_df["average_order_value"] = (
        feature_df["monetary_value"] / feature_df["frequency"].replace(0, 1)
    ).round(2)
    feature_df["historical_order_count"] = feature_df["frequency"]
    feature_df["historical_revenue"] = feature_df["monetary_value"]
    feature_df["feature_generation_version"] = version

    # If horizon is provided, append temporal future churn label
    if churn_horizon_days is not None:
        label_df = construct_churn_labels(
            transactions_df=df,
            observation_cutoff=cutoff_d,
            horizon_days=churn_horizon_days,
        )
        feature_df = feature_df.merge(
            label_df[["customer_id", "churn_label"]], on="customer_id", how="left"
        )
        feature_df["label_window_end"] = cutoff_d + timedelta(days=churn_horizon_days)

    logger.info(
        f"Built customer feature table at cutoff {cutoff_d}: "
        f"{len(feature_df)} rows, {len(feature_df.columns)} columns"
    )

    return feature_df
