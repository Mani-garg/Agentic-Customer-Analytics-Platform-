"""Unit tests for deterministic RFM customer segmentation."""

import pandas as pd

from customer_analytics.analytics.segmentation import (
    assign_segments,
    generate_segment_summaries,
    map_rfm_to_segment,
)
from customer_analytics.domain.enums import CustomerSegment


def test_map_rfm_to_segment_rules():
    """Verify segment classification rules."""
    assert map_rfm_to_segment(5, 5, 5) == CustomerSegment.CHAMPIONS
    assert map_rfm_to_segment(4, 4, 4) == CustomerSegment.CHAMPIONS
    assert map_rfm_to_segment(3, 4, 3) == CustomerSegment.LOYAL_CUSTOMERS
    assert map_rfm_to_segment(5, 1, 1) == CustomerSegment.NEW_CUSTOMERS
    assert map_rfm_to_segment(1, 4, 4) == CustomerSegment.AT_RISK
    assert map_rfm_to_segment(1, 1, 1) == CustomerSegment.HIBERNATING


def test_assign_segments_dataframe():
    """Verify segment assignment on a dataframe."""
    df = pd.DataFrame(
        [
            {
                "customer_id": "C1",
                "r_score": 5,
                "f_score": 5,
                "m_score": 5,
                "monetary_value": 1000.0,
                "frequency": 10,
                "recency_days": 2,
            },
            {
                "customer_id": "C2",
                "r_score": 1,
                "f_score": 4,
                "m_score": 4,
                "monetary_value": 800.0,
                "frequency": 8,
                "recency_days": 120,
            },
        ]
    )
    res = assign_segments(df)
    assert res.iloc[0]["segment"] == CustomerSegment.CHAMPIONS.value
    assert res.iloc[1]["segment"] == CustomerSegment.AT_RISK.value

    summaries = generate_segment_summaries(res)
    assert len(summaries) == 2
    champ = next(s for s in summaries if s.segment == CustomerSegment.CHAMPIONS)
    assert champ.customer_count == 1
    assert champ.total_revenue == 1000.0
