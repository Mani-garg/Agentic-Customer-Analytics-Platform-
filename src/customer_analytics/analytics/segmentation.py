"""Interpretable customer segmentation based on RFM score matrices."""

import logging
from typing import Dict, List

import pandas as pd

from customer_analytics.domain.enums import CustomerSegment
from customer_analytics.domain.models import SegmentSummary

logger = logging.getLogger(__name__)


def map_rfm_to_segment(r: int, f: int, m: int) -> CustomerSegment:
    """Map individual R, F, M scores (1..5) to an actionable business segment."""
    # Champions: Bought recently, buy often, and spend the most
    if r in (4, 5) and f in (4, 5) and m in (4, 5):
        return CustomerSegment.CHAMPIONS

    # Loyal Customers: Consistent regular purchasers with solid spend
    if r in (3, 4, 5) and f in (3, 4, 5) and m in (3, 4, 5):
        return CustomerSegment.LOYAL_CUSTOMERS

    # New Customers: Bought very recently for the first time
    if r in (4, 5) and f == 1:
        return CustomerSegment.NEW_CUSTOMERS

    # Potential Loyalists: Recent buyers with moderate spend/frequency
    if r in (4, 5) and f in (2, 3):
        return CustomerSegment.POTENTIAL_LOYALISTS

    # Promising: Recent buyers with low frequency
    if r in (3, 4) and f == 1:
        return CustomerSegment.PROMISING

    # At Risk: Spent heavily and bought often in the past, but haven't returned recently
    if r in (1, 2) and f in (3, 4, 5) and m in (3, 4, 5):
        return CustomerSegment.AT_RISK

    # About to Sleep: Below average recency and frequency; heading for hibernation
    if r in (2, 3) and f in (1, 2):
        return CustomerSegment.ABOUT_TO_SLEEP

    # Hibernating: Long time since purchase, low frequency, low monetary value
    if r in (1, 2) and f in (1, 2):
        return CustomerSegment.HIBERNATING

    return CustomerSegment.UNCLASSIFIED


def assign_segments(scored_rfm_df: pd.DataFrame) -> pd.DataFrame:
    """Apply segment mapping across the scored RFM dataframe."""
    if scored_rfm_df.empty:
        df = scored_rfm_df.copy()
        df["segment"] = ""
        return df

    df = scored_rfm_df.copy()
    segments = [
        map_rfm_to_segment(int(r), int(f), int(m)).value
        for r, f, m in zip(df["r_score"], df["f_score"], df["m_score"], strict=False)
    ]
    df["segment"] = segments
    return df


def generate_segment_summaries(
    segmented_df: pd.DataFrame,
    risk_df: pd.DataFrame = None,
) -> List[SegmentSummary]:
    """Calculate aggregated analytical metrics per customer segment."""
    if segmented_df.empty:
        return []

    df = segmented_df.copy()
    total_customers = len(df)
    df["monetary_value"].sum()

    summaries: List[SegmentSummary] = []

    priority_map: Dict[str, str] = {
        CustomerSegment.CHAMPIONS.value: "Reward & Retain",
        CustomerSegment.LOYAL_CUSTOMERS.value: "Upsell & Cross-sell",
        CustomerSegment.POTENTIAL_LOYALISTS.value: "Nurture with Membership Programs",
        CustomerSegment.NEW_CUSTOMERS.value: "Onboard & Early Engagement",
        CustomerSegment.PROMISING.value: "Product Recommendations",
        CustomerSegment.AT_RISK.value: "High Priority Win-Back Campaigns",
        CustomerSegment.ABOUT_TO_SLEEP.value: "Reactivation Discounts",
        CustomerSegment.HIBERNATING.value: "Low Cost Automated Outreach",
        CustomerSegment.UNCLASSIFIED.value: "General Nurture",
    }

    # Group by segment
    grouped = df.groupby("segment")

    for seg_val, group in grouped:
        count = len(group)
        tot_rev = float(group["monetary_value"].sum())
        avg_rev = float(group["monetary_value"].mean())
        avg_freq = float(group["frequency"].mean())
        avg_rec = float(group["recency_days"].mean())
        pct = round((count / total_customers) * 100.0, 2)

        summaries.append(
            SegmentSummary(
                segment=CustomerSegment(seg_val),
                customer_count=count,
                customer_percentage=pct,
                total_revenue=round(tot_rev, 2),
                average_revenue_per_customer=round(avg_rev, 2),
                average_order_frequency=round(avg_freq, 2),
                average_recency_days=round(avg_rec, 1),
                high_risk_customer_count=0,
                retention_priority=priority_map.get(seg_val, "Standard"),
            )
        )

    # Sort by total revenue descending
    summaries.sort(key=lambda s: s.total_revenue, reverse=True)
    return summaries
