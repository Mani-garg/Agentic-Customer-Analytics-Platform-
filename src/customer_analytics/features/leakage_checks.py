"""Integrity checks to guard against future information leakage in feature tables."""

import logging
from datetime import date, datetime
from typing import Tuple, Union

import pandas as pd

from customer_analytics.features.build_features import build_customer_feature_table
from customer_analytics.utils.dates import parse_date

logger = logging.getLogger(__name__)


def verify_temporal_leakage_safety(
    transactions_df: pd.DataFrame,
    observation_cutoff: Union[date, datetime],
    churn_horizon_days: int = 90,
) -> Tuple[bool, str]:
    """Test feature generation to verify that future transactions do not bleed into historical features.

    Method:
      1. Compute feature table at cutoff T on original data.
      2. Inject simulated future transactions occurring strictly after T.
      3. Recompute feature table at cutoff T.
      4. Assert that all predictive feature values for all customers are bit-identical.
    """
    cutoff_d = parse_date(observation_cutoff)

    # 1. Base features at cutoff T (features only, no horizon labels needed for leakage check)
    base_features = build_customer_feature_table(
        transactions_df=transactions_df,
        observation_cutoff=cutoff_d,
        churn_horizon_days=None,
    )

    if base_features.empty:
        return True, "No historical transactions found at cutoff date."

    # 2. Fabricate future transactions for existing customers strictly after cutoff T
    sample_customers = base_features["customer_id"].head(20).tolist()
    future_records = []
    has_gross = "line_gross_revenue" in transactions_df.columns
    for i, cid in enumerate(sample_customers):
        rec = {
            "order_id": f"FUTURE-LEAK-TEST-{i}",
            "customer_id": cid,
            "order_date": f"{cutoff_d.year + 1}-01-01 12:00:00",
            "product_id": "TEST-PROD",
            "category": "Electronics",
            "quantity": 2,
            "unit_price": 50.0,
            "discount": 0.0,
            "country": "US",
            "order_status": "completed",
            "currency": "USD",
        }
        if has_gross:
            rec["line_gross_revenue"] = 100.0
            rec["line_net_revenue"] = 100.0
        future_records.append(rec)

    future_df = pd.concat([transactions_df, pd.DataFrame(future_records)], ignore_index=True)

    # 3. Rebuild features at cutoff T with future records present in dataset
    post_future_features = build_customer_feature_table(
        transactions_df=future_df,
        observation_cutoff=cutoff_d,
        churn_horizon_days=None,
    )

    # 4. Compare feature columns
    feature_cols = [
        "recency_days",
        "frequency",
        "monetary_value",
        "average_order_value",
        "customer_tenure_days",
        "days_since_first_purchase",
        "purchase_gap_mean",
        "purchase_gap_std",
    ]

    base_subset = base_features.set_index("customer_id")[feature_cols].sort_index()
    post_subset = post_future_features.set_index("customer_id")[feature_cols].sort_index()

    # Re-index to common customers
    common_idx = base_subset.index.intersection(post_subset.index)
    diff = (base_subset.loc[common_idx] - post_subset.loc[common_idx]).abs().max().max()

    if diff > 1e-6:
        err = f"Temporal leakage detected! Feature discrepancy across future injection: max diff = {diff}"
        logger.error(err)
        return False, err

    logger.info(
        "Temporal leakage test passed: future transactions do not leak into historical features."
    )
    return True, "Temporal feature isolation verified. Zero future leakage."
