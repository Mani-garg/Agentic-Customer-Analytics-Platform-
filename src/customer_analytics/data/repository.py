"""Data repository providing controlled access to relational analytical artifacts."""

import logging
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import text

from customer_analytics.agent.sql_guard import SQLGuard
from customer_analytics.data.database import (
    DatabaseSessionManager,
    churn_risk_scores_table,
    customer_features_table,
    get_db_manager,
    rfm_segments_table,
)
from customer_analytics.domain.contracts import PersistenceRepositoryInterface
from customer_analytics.domain.enums import CustomerSegment
from customer_analytics.domain.models import SegmentSummary

logger = logging.getLogger(__name__)


class AnalyticsRepository(PersistenceRepositoryInterface):
    """Repository accessing analytical datasets and enforcing guarded read-only SQL queries."""

    def __init__(
        self,
        db_manager: Optional[DatabaseSessionManager] = None,
        sql_guard: Optional[SQLGuard] = None,
    ):
        self.db = db_manager or get_db_manager()
        self.sql_guard = sql_guard or SQLGuard()

    def sync_feature_dataframe_to_db(self, feature_df: pd.DataFrame) -> int:
        """Persist feature table, RFM scores, and segment summaries into the database."""
        if feature_df.empty:
            return 0

        with self.db.get_app_session() as session:
            # 1. Clean existing records
            session.execute(text("DELETE FROM rfm_segments"))
            session.execute(text("DELETE FROM customer_features"))
            session.execute(text("DELETE FROM segment_summaries"))

            # 2. Insert rfm_segments
            rfm_records = []
            for _, r in feature_df.iterrows():
                rfm_records.append(
                    {
                        "customer_id": str(r["customer_id"]),
                        "recency_days": int(r["recency_days"]),
                        "frequency": int(r["frequency"]),
                        "monetary_value": float(r["monetary_value"]),
                        "r_score": int(r.get("r_score", 3)),
                        "f_score": int(r.get("f_score", 3)),
                        "m_score": int(r.get("m_score", 3)),
                        "rfm_score_str": str(r.get("rfm_score_str", "333")),
                        "segment": str(r.get("segment", "Unclassified")),
                    }
                )
            session.execute(rfm_segments_table.insert(), rfm_records)

            # 3. Insert customer_features
            features_records = []
            for _, r in feature_df.iterrows():
                features_records.append(
                    {
                        "customer_id": str(r["customer_id"]),
                        "observation_date": r["observation_date"],
                        "recency_days": int(r["recency_days"]),
                        "frequency": int(r["frequency"]),
                        "monetary_value": float(r["monetary_value"]),
                        "average_order_value": float(r["average_order_value"]),
                        "customer_tenure_days": int(r["customer_tenure_days"]),
                        "days_since_first_purchase": int(r["days_since_first_purchase"]),
                        "purchase_gap_mean": float(r["purchase_gap_mean"]),
                        "purchase_gap_std": float(r["purchase_gap_std"]),
                        "historical_order_count": int(r["historical_order_count"]),
                        "historical_revenue": float(r["historical_revenue"]),
                        "segment": str(r.get("segment", "Unclassified")),
                        "churn_label": int(r["churn_label"])
                        if pd.notna(r.get("churn_label"))
                        else None,
                    }
                )
            session.execute(customer_features_table.insert(), features_records)

            session.commit()

        # Generate and sync segment summaries
        self._refresh_segment_summaries()
        logger.info(f"Synchronized {len(feature_df)} customer features into database.")
        return len(feature_df)

    def _refresh_segment_summaries(self) -> None:
        """Aggregate and populate segment_summaries table."""
        with self.db.get_app_session() as session:
            session.execute(text("DELETE FROM segment_summaries"))
            query = text("""
                INSERT INTO segment_summaries (
                    segment, customer_count, customer_percentage, total_revenue,
                    average_revenue_per_customer, average_order_frequency,
                    average_recency_days, retention_priority
                )
                SELECT
                    segment,
                    COUNT(*) AS customer_count,
                    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM rfm_segments), 2) AS customer_percentage,
                    ROUND(SUM(monetary_value), 2) AS total_revenue,
                    ROUND(AVG(monetary_value), 2) AS average_revenue_per_customer,
                    ROUND(AVG(frequency), 2) AS average_order_frequency,
                    ROUND(AVG(recency_days), 1) AS average_recency_days,
                    CASE
                        WHEN segment = 'Champions' THEN 'Reward & Retain'
                        WHEN segment = 'Loyal Customers' THEN 'Upsell & Cross-sell'
                        WHEN segment = 'At Risk' THEN 'High Priority Win-Back Campaigns'
                        WHEN segment = 'About to Sleep' THEN 'Reactivation Discounts'
                        WHEN segment = 'Hibernating' THEN 'Low Cost Outreach'
                        ELSE 'Standard Engagement'
                    END AS retention_priority
                FROM rfm_segments
                GROUP BY segment
            """)
            session.execute(query)
            session.commit()

    def sync_churn_predictions_to_db(self, predictions_df: pd.DataFrame) -> int:
        """Persist batch inference churn scores into database."""
        if predictions_df.empty:
            return 0

        with self.db.get_app_session() as session:
            session.execute(text("DELETE FROM churn_risk_scores"))
            records = []
            for _, r in predictions_df.iterrows():
                records.append(
                    {
                        "customer_id": str(r["customer_id"]),
                        "churn_probability": float(r["churn_probability"]),
                        "is_churn_predicted": int(r["is_churn_predicted"]),
                        "risk_tier": str(r["risk_tier"]),
                        "operating_threshold": float(r["operating_threshold"]),
                        "model_version": str(r["model_version"]),
                        "scored_at": r["timestamp"],
                    }
                )
            session.execute(churn_risk_scores_table.insert(), records)
            session.commit()
        return len(predictions_df)

    def get_overview_metrics(self) -> Dict[str, Any]:
        """Compute high-level summary across the active analytical dataset."""
        with self.db.get_agent_session() as session:
            row = (
                session.execute(
                    text("""
                SELECT
                    COUNT(DISTINCT customer_id) AS total_customers,
                    COALESCE(ROUND(SUM(monetary_value), 2), 0.0) AS total_gross_revenue,
                    COALESCE(ROUND(AVG(monetary_value), 2), 0.0) AS avg_revenue_per_customer,
                    COALESCE(ROUND(AVG(frequency), 2), 0.0) AS avg_order_frequency,
                    COALESCE(ROUND(AVG(recency_days), 1), 0.0) AS avg_recency_days
                FROM rfm_segments
            """)
                )
                .mappings()
                .first()
            )

            # Also check churn counts if available
            churn_row = (
                session.execute(
                    text("""
                SELECT
                    COUNT(*) AS total_scored,
                    SUM(CASE WHEN risk_tier = 'high' THEN 1 ELSE 0 END) AS high_risk_count,
                    COALESCE(ROUND(AVG(churn_probability), 4), 0.0) AS avg_churn_prob
                FROM churn_risk_scores
            """)
                )
                .mappings()
                .first()
            )

        res = dict(row) if row else {}
        if churn_row and churn_row.get("total_scored", 0) > 0:
            res["scored_customers"] = churn_row["total_scored"]
            res["high_risk_customers"] = churn_row["high_risk_count"]
            res["average_churn_probability"] = churn_row["avg_churn_prob"]
        else:
            res["scored_customers"] = 0
            res["high_risk_customers"] = 0
            res["average_churn_probability"] = 0.0

        return res

    def get_segment_summaries(self) -> List[SegmentSummary]:
        """Retrieve aggregated segment summaries from relational persistence."""
        with self.db.get_agent_session() as session:
            rows = (
                session.execute(text("SELECT * FROM segment_summaries ORDER BY total_revenue DESC"))
                .mappings()
                .all()
            )

        summaries: List[SegmentSummary] = []
        for r in rows:
            summaries.append(
                SegmentSummary(
                    segment=CustomerSegment(r["segment"]),
                    customer_count=r["customer_count"],
                    customer_percentage=r["customer_percentage"],
                    total_revenue=r["total_revenue"],
                    average_revenue_per_customer=r["average_revenue_per_customer"],
                    average_order_frequency=r["average_order_frequency"],
                    average_recency_days=r["average_recency_days"],
                    retention_priority=r["retention_priority"],
                )
            )
        return summaries

    def get_high_risk_customers(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Retrieve paginated high-risk customer records with authorized projection."""
        clamped_limit = min(100, max(1, limit))
        clamped_offset = max(0, offset)

        with self.db.get_agent_session() as session:
            rows = (
                session.execute(
                    text("""
                    SELECT
                        c.customer_id,
                        c.churn_probability,
                        c.risk_tier,
                        c.operating_threshold,
                        r.segment,
                        r.recency_days,
                        r.frequency,
                        r.monetary_value
                    FROM churn_risk_scores c
                    JOIN rfm_segments r ON c.customer_id = r.customer_id
                    WHERE c.risk_tier = 'high'
                    ORDER BY c.churn_probability DESC, r.monetary_value DESC
                    LIMIT :limit OFFSET :offset
                """),
                    {"limit": clamped_limit, "offset": clamped_offset},
                )
                .mappings()
                .all()
            )

        return [dict(r) for r in rows]

    def execute_guarded_sql(self, sql: str, max_rows: int = 100) -> List[Dict[str, Any]]:
        """Validate raw SQL through SQLGuard and execute on read-only session."""
        sanitized_sql = self.sql_guard.validate_and_sanitize(sql)

        try:
            with self.db.get_agent_session() as session:
                result = session.execute(text(sanitized_sql))
                rows = result.mappings().fetchmany(max_rows)
                return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"Error during guarded SQL execution: {e}")
            raise
