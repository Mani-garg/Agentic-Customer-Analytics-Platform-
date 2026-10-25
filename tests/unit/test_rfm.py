"""Unit tests for RFM calculation, scoring directionality, and quantile boundary handling."""

from datetime import date

import pandas as pd

from customer_analytics.analytics.rfm import assign_rfm_scores, compute_rfm_raw, score_quantiles


def test_rfm_raw_aggregation():
    """Verify recency days, distinct order frequency, and sum of spend."""
    cutoff = date(2026, 6, 30)
    tx_data = [
        {
            "order_id": "O1",
            "customer_id": "C1",
            "order_date": "2026-06-25",
            "line_gross_revenue": 100.0,
        },
        {
            "order_id": "O1",
            "customer_id": "C1",
            "order_date": "2026-06-25",
            "line_gross_revenue": 50.0,
        },  # Same order, 2 items
        {
            "order_id": "O2",
            "customer_id": "C1",
            "order_date": "2026-06-20",
            "line_gross_revenue": 50.0,
        },
        {
            "order_id": "O3",
            "customer_id": "C2",
            "order_date": "2026-05-01",
            "line_gross_revenue": 200.0,
        },
    ]
    df = pd.DataFrame(tx_data)
    raw = compute_rfm_raw(df, observation_date=cutoff)

    assert len(raw) == 2
    c1 = raw[raw["customer_id"] == "C1"].iloc[0]
    # Recency: 2026-06-30 - 2026-06-25 = 5 days
    assert c1["recency_days"] == 5
    # Frequency: 2 distinct orders (O1 and O2)
    assert c1["frequency"] == 2
    # Monetary: 100 + 50 + 50 = 200.0
    assert c1["monetary_value"] == 200.0


def test_rfm_scoring_directionality():
    """Verify that fewer recency days yields a higher R score, while higher frequency/spend yields higher F/M scores."""
    df = pd.DataFrame(
        [
            {"customer_id": "C_Best", "recency_days": 2, "frequency": 20, "monetary_value": 5000.0},
            {"customer_id": "C_Mid", "recency_days": 50, "frequency": 5, "monetary_value": 500.0},
            {"customer_id": "C_Worst", "recency_days": 300, "frequency": 1, "monetary_value": 20.0},
        ]
    )
    scored = assign_rfm_scores(df, n_bins=3)

    best = scored[scored["customer_id"] == "C_Best"].iloc[0]
    worst = scored[scored["customer_id"] == "C_Worst"].iloc[0]

    assert best["r_score"] > worst["r_score"], "Fewer recency days must receive a higher score."
    assert best["f_score"] > worst["f_score"], "Higher order frequency must receive a higher score."
    assert best["m_score"] > worst["m_score"], "Higher monetary spend must receive a higher score."


def test_score_quantiles_constant_values():
    """Quantile scoring on constant or low distinct count values must not crash."""
    series = pd.Series([10, 10, 10, 10, 10])
    scores = score_quantiles(series, n_bins=5)
    assert len(scores) == 5
    assert (scores == 3).all()  # Median bucket assignment
