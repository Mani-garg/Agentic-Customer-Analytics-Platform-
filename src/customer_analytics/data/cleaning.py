"""Deterministic data cleaning and normalization for transaction records."""

import logging
from typing import Tuple

import pandas as pd

logger = logging.getLogger(__name__)


def clean_transactions(
    df: pd.DataFrame,
    filter_eligible_statuses_only: bool = True,
) -> Tuple[pd.DataFrame, dict]:
    """Clean and normalize accepted transactions according to documented business rules."""
    initial_rows = len(df)
    if initial_rows == 0:
        return df.copy(), {"initial_rows": 0, "final_rows": 0, "excluded_statuses": 0}

    cleaned = df.copy()

    # 1. Standardize types
    cleaned["order_id"] = cleaned["order_id"].astype(str).str.strip()
    cleaned["customer_id"] = cleaned["customer_id"].astype(str).str.strip()
    cleaned["order_date"] = pd.to_datetime(cleaned["order_date"])
    cleaned["quantity"] = cleaned["quantity"].astype(int)
    cleaned["unit_price"] = cleaned["unit_price"].astype(float).round(2)

    if "discount" in cleaned.columns:
        cleaned["discount"] = cleaned["discount"].fillna(0.0).astype(float).round(4)
    else:
        cleaned["discount"] = 0.0

    if "category" in cleaned.columns:
        cleaned["category"] = cleaned["category"].fillna("General").astype(str).str.strip()
    else:
        cleaned["category"] = "General"

    if "country" in cleaned.columns:
        cleaned["country"] = cleaned["country"].fillna("US").astype(str).str.strip().str.upper()
    else:
        cleaned["country"] = "US"

    if "order_status" in cleaned.columns:
        cleaned["order_status"] = cleaned["order_status"].astype(str).str.lower().str.strip()
    else:
        cleaned["order_status"] = "completed"

    if "currency" in cleaned.columns:
        cleaned["currency"] = cleaned["currency"].astype(str).str.upper().str.strip()
    else:
        cleaned["currency"] = "USD"

    # 2. Derive monetary metrics
    cleaned["line_gross_revenue"] = (cleaned["quantity"] * cleaned["unit_price"]).round(2)
    cleaned["line_net_revenue"] = (
        cleaned["line_gross_revenue"] * (1.0 - cleaned["discount"])
    ).round(2)

    # 3. Status eligibility filter: only completed or shipped count towards customer spend
    excluded_count = 0
    if filter_eligible_statuses_only:
        eligible_mask = cleaned["order_status"].isin(["completed", "shipped"])
        excluded_count = int((~eligible_mask).sum())
        cleaned = cleaned[eligible_mask].copy()

    # 4. Sort chronologically
    cleaned = cleaned.sort_values(["order_date", "order_id"]).reset_index(drop=True)

    summary = {
        "initial_rows": initial_rows,
        "final_rows": len(cleaned),
        "excluded_non_eligible_statuses": excluded_count,
    }

    logger.info(
        f"Cleaned transactions: {initial_rows} -> {len(cleaned)} rows "
        f"(excluded {excluded_count} cancelled/refunded/pending orders)"
    )

    return cleaned, summary
