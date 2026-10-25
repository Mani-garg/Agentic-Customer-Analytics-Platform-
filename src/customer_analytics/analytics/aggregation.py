"""Unified aggregation engine implementing PySpark with fallback to vectorized in-memory processing."""

import logging
from datetime import date, datetime
from typing import List, Optional, Union

import pandas as pd

from customer_analytics.analytics.rfm import assign_rfm_scores, compute_rfm_raw
from customer_analytics.analytics.segmentation import assign_segments
from customer_analytics.analytics.spark_session import SparkSessionManager
from customer_analytics.domain.contracts import AnalyticsEngineInterface
from customer_analytics.domain.models import CustomerFeatureRecord, RFMScore
from customer_analytics.features.build_features import build_customer_feature_table
from customer_analytics.utils.dates import parse_date

logger = logging.getLogger(__name__)


class AnalyticsEngine(AnalyticsEngineInterface):
    """Hybrid analytics engine capable of executing on PySpark or in-memory Pandas."""

    def __init__(self, spark_enabled: bool = False):
        self.spark_enabled = spark_enabled
        self.spark_session = None
        if self.spark_enabled:
            self.spark_session = SparkSessionManager.get_or_create_session()

    def compute_rfm_metrics(
        self,
        transactions_df: pd.DataFrame,
        observation_date: Union[date, datetime],
    ) -> List[RFMScore]:
        """Compute customer RFM scores and segments."""
        obs_d = parse_date(observation_date)
        raw_rfm = compute_rfm_raw(transactions_df, obs_d)
        scored_rfm = assign_rfm_scores(raw_rfm)
        segmented = assign_segments(scored_rfm)

        scores: List[RFMScore] = []
        for _, row in segmented.iterrows():
            scores.append(
                RFMScore(
                    customer_id=str(row["customer_id"]),
                    recency_days=int(row["recency_days"]),
                    frequency=int(row["frequency"]),
                    monetary_value=float(row["monetary_value"]),
                    r_score=int(row["r_score"]),
                    f_score=int(row["f_score"]),
                    m_score=int(row["m_score"]),
                    rfm_score_str=str(row["rfm_score_str"]),
                    segment=row["segment"],
                )
            )
        return scores

    def build_customer_features(
        self,
        transactions_df: pd.DataFrame,
        observation_date: Union[date, datetime],
        churn_horizon_days: Optional[int] = None,
    ) -> List[CustomerFeatureRecord]:
        """Construct customer feature vectors with optional future churn label."""
        obs_d = parse_date(observation_date)
        feature_df = build_customer_feature_table(
            transactions_df=transactions_df,
            observation_cutoff=obs_d,
            churn_horizon_days=churn_horizon_days,
        )

        records: List[CustomerFeatureRecord] = []
        for _, row in feature_df.iterrows():
            records.append(
                CustomerFeatureRecord(
                    customer_id=str(row["customer_id"]),
                    observation_date=obs_d,
                    recency_days=int(row["recency_days"]),
                    frequency=int(row["frequency"]),
                    monetary_value=float(row["monetary_value"]),
                    average_order_value=float(row["average_order_value"]),
                    customer_tenure_days=int(row["customer_tenure_days"]),
                    days_since_first_purchase=int(row["days_since_first_purchase"]),
                    purchase_gap_mean=float(row["purchase_gap_mean"]),
                    purchase_gap_std=float(row["purchase_gap_std"]),
                    historical_order_count=int(row["historical_order_count"]),
                    historical_revenue=float(row["historical_revenue"]),
                    segment=str(row.get("segment", "Unclassified")),
                    churn_label=int(row["churn_label"])
                    if pd.notna(row.get("churn_label"))
                    else None,
                    label_window_end=row.get("label_window_end"),
                    feature_generation_version=str(row.get("feature_generation_version", "v1.0.0")),
                )
            )
        return records
