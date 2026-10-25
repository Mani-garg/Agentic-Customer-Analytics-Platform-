"""Data quality validation rules and observable quality reporting."""

import logging
from collections import Counter
from datetime import datetime, timezone
from typing import List, Tuple

import pandas as pd

from customer_analytics.data.schemas import (
    ALLOWED_CURRENCIES,
    ALLOWED_STATUSES,
    REQUIRED_TRANSACTION_COLUMNS,
)
from customer_analytics.domain.models import DataQualityReport
from customer_analytics.exceptions import DataValidationException

logger = logging.getLogger(__name__)


def validate_transactions(
    df: pd.DataFrame,
    dataset_name: str = "transactions_raw",
    allow_empty: bool = False,
) -> Tuple[pd.DataFrame, pd.DataFrame, DataQualityReport]:
    """Validate transaction dataset and split into accepted and rejected rows with reason codes."""
    if df is None or (df.empty and not allow_empty):
        raise DataValidationException("Transaction DataFrame is null or empty.")

    records_read = len(df)
    if records_read == 0:
        report = DataQualityReport(
            dataset_name=dataset_name,
            timestamp=datetime.now(timezone.utc),
            records_read=0,
            records_accepted=0,
            records_rejected=0,
            rejection_rate=0.0,
            reasons_breakdown={},
            checks_passed=True,
            warnings=["Dataset is empty."],
        )
        return df.copy(), pd.DataFrame(), report

    # Verify column presence
    missing_cols = [c for c in REQUIRED_TRANSACTION_COLUMNS if c not in df.columns]
    if missing_cols:
        raise DataValidationException(f"Missing mandatory columns: {missing_cols}")

    rejection_reasons: List[str] = [""] * records_read
    valid_mask = [True] * records_read
    warnings: List[str] = []

    # 1. Null identifiers
    null_order_id = df["order_id"].isna() | (df["order_id"].astype(str).str.strip() == "")
    null_customer_id = df["customer_id"].isna() | (df["customer_id"].astype(str).str.strip() == "")

    # 2. Duplicate records check
    duplicates = (
        df.duplicated(subset=["order_id", "product_id"], keep="first")
        if "product_id" in df.columns
        else df.duplicated(subset=["order_id"], keep="first")
    )

    # 3. Numeric conversions and range checks
    quantity_numeric = pd.to_numeric(df["quantity"], errors="coerce")
    invalid_quantity = quantity_numeric.isna() | (quantity_numeric <= 0)

    price_numeric = pd.to_numeric(df["unit_price"], errors="coerce")
    invalid_price = price_numeric.isna() | (price_numeric < 0.0)

    # 4. Discounts check
    if "discount" in df.columns:
        discount_numeric = pd.to_numeric(df["discount"], errors="coerce")
        invalid_discount = (
            discount_numeric.isna() | (discount_numeric < 0.0) | (discount_numeric > 1.0)
        )
    else:
        invalid_discount = pd.Series([False] * records_read, index=df.index)

    # 5. Dates check
    parsed_dates = pd.to_datetime(df["order_date"], errors="coerce")
    now_utc = pd.Timestamp.now(tz="UTC").tz_localize(None)
    min_plausible_date = pd.Timestamp("2000-01-01")
    max_plausible_date = now_utc + pd.Timedelta(days=1)
    invalid_date = (
        parsed_dates.isna()
        | (parsed_dates < min_plausible_date)
        | (parsed_dates > max_plausible_date)
    )

    # 6. Status check
    if "order_status" in df.columns:
        invalid_status = ~df["order_status"].astype(str).str.lower().isin(ALLOWED_STATUSES)
    else:
        invalid_status = pd.Series([False] * records_read, index=df.index)

    # 7. Currency check
    if "currency" in df.columns:
        invalid_currency = ~df["currency"].astype(str).str.upper().isin(ALLOWED_CURRENCIES)
    else:
        invalid_currency = pd.Series([False] * records_read, index=df.index)

    # Assign priority rejection reasons
    reason_counter: Counter = Counter()

    for i in range(records_read):
        reason = None
        if null_order_id.iloc[i]:
            reason = "NULL_ORDER_ID"
        elif null_customer_id.iloc[i]:
            reason = "NULL_CUSTOMER_ID"
        elif invalid_date.iloc[i]:
            reason = "INVALID_OR_IMPLAUSIBLE_DATE"
        elif invalid_quantity.iloc[i]:
            reason = "INVALID_OR_NON_POSITIVE_QUANTITY"
        elif invalid_price.iloc[i]:
            reason = "INVALID_OR_NEGATIVE_UNIT_PRICE"
        elif invalid_discount.iloc[i]:
            reason = "INVALID_DISCOUNT_OUT_OF_BOUNDS"
        elif invalid_status.iloc[i]:
            reason = "UNRECOGNIZED_ORDER_STATUS"
        elif invalid_currency.iloc[i]:
            reason = "UNSUPPORTED_CURRENCY"
        elif duplicates.iloc[i]:
            reason = "DUPLICATE_TRANSACTION_RECORD"

        if reason is not None:
            valid_mask[i] = False
            rejection_reasons[i] = reason
            reason_counter[reason] += 1

    accepted_df = df[valid_mask].copy()
    rejected_df = df[~pd.Series(valid_mask, index=df.index)].copy()
    rejected_df["rejection_reason"] = [r for r in rejection_reasons if r]

    records_accepted = len(accepted_df)
    records_rejected = len(rejected_df)
    rejection_rate = round(records_rejected / records_read, 4) if records_read > 0 else 0.0

    if records_accepted == 0 and records_read > 0:
        warnings.append("All input records failed validation checks.")

    if rejection_rate > 0.20:
        warnings.append(f"High rejection rate observed: {rejection_rate * 100:.1f}%")

    report = DataQualityReport(
        dataset_name=dataset_name,
        timestamp=datetime.now(timezone.utc),
        records_read=records_read,
        records_accepted=records_accepted,
        records_rejected=records_rejected,
        rejection_rate=rejection_rate,
        reasons_breakdown=dict(reason_counter),
        checks_passed=records_accepted > 0,
        warnings=warnings,
    )

    logger.info(
        f"Validation complete for {dataset_name}: {records_accepted} accepted, "
        f"{records_rejected} rejected ({rejection_rate * 100:.2f}%)"
    )

    return accepted_df, rejected_df, report
