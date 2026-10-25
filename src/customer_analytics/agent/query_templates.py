"""Approved, parameterized query templates for common analytical questions."""

from typing import Dict

QUERY_TEMPLATES: Dict[str, str] = {
    "overview_metrics": """
        SELECT
            COUNT(DISTINCT customer_id) AS total_customers,
            ROUND(SUM(monetary_value), 2) AS total_revenue,
            ROUND(AVG(monetary_value), 2) AS avg_customer_spend,
            ROUND(AVG(frequency), 2) AS avg_frequency,
            ROUND(AVG(recency_days), 1) AS avg_recency_days
        FROM rfm_segments
    """,
    "segment_summary": """
        SELECT
            segment,
            COUNT(*) AS customer_count,
            ROUND(SUM(monetary_value), 2) AS total_revenue,
            ROUND(AVG(monetary_value), 2) AS avg_revenue_per_customer,
            ROUND(AVG(frequency), 2) AS avg_frequency,
            ROUND(AVG(recency_days), 1) AS avg_recency_days
        FROM rfm_segments
        GROUP BY segment
        ORDER BY total_revenue DESC
    """,
    "top_customers": """
        SELECT
            customer_id,
            segment,
            recency_days,
            frequency,
            monetary_value
        FROM rfm_segments
        ORDER BY monetary_value DESC
        LIMIT :limit
    """,
    "churn_summary": """
        SELECT
            risk_tier,
            COUNT(*) AS customer_count,
            ROUND(AVG(churn_probability), 4) AS avg_churn_probability
        FROM churn_risk_scores
        GROUP BY risk_tier
        ORDER BY avg_churn_probability DESC
    """,
    "churn_by_segment": """
        SELECT
            r.segment,
            COUNT(*) AS total_customers,
            SUM(CASE WHEN c.risk_tier = 'high' THEN 1 ELSE 0 END) AS high_risk_customers,
            ROUND(AVG(c.churn_probability), 4) AS avg_churn_probability
        FROM rfm_segments r
        LEFT JOIN churn_risk_scores c ON r.customer_id = c.customer_id
        GROUP BY r.segment
        ORDER BY high_risk_customers DESC
    """,
}


def get_template(name: str) -> str:
    """Retrieve an approved query template by name."""
    if name not in QUERY_TEMPLATES:
        raise KeyError(
            f"Unknown query template '{name}'. Available: {list(QUERY_TEMPLATES.keys())}"
        )
    return QUERY_TEMPLATES[name].strip()
