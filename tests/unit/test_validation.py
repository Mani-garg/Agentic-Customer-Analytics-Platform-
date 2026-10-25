"""Unit tests for data validation rules and rejected record handling."""

import pandas as pd
import pytest

from customer_analytics.data.validation import validate_transactions
from customer_analytics.exceptions import DataValidationException


def test_validate_clean_transactions(sample_transactions_df: pd.DataFrame):
    """Clean synthetic transactions must pass validation with 0 rejections."""
    accepted, rejected, report = validate_transactions(sample_transactions_df)
    assert report.checks_passed is True
    assert len(accepted) == len(sample_transactions_df)
    assert len(rejected) == 0
    assert report.rejection_rate == 0.0


def test_validate_null_order_id():
    """Rows with null order_id must be rejected."""
    df = pd.DataFrame(
        [
            {
                "order_id": None,
                "customer_id": "CUST-1",
                "order_date": "2026-01-01 12:00:00",
                "quantity": 1,
                "unit_price": 25.0,
            },
            {
                "order_id": "ORD-1",
                "customer_id": "CUST-1",
                "order_date": "2026-01-01 12:00:00",
                "quantity": 1,
                "unit_price": 25.0,
            },
        ]
    )
    accepted, rejected, report = validate_transactions(df)
    assert len(accepted) == 1
    assert len(rejected) == 1
    assert "NULL_ORDER_ID" in report.reasons_breakdown


def test_validate_invalid_quantity_and_price():
    """Negative or zero quantity and negative unit prices must be rejected."""
    df = pd.DataFrame(
        [
            {
                "order_id": "ORD-1",
                "customer_id": "CUST-1",
                "order_date": "2026-01-01 12:00:00",
                "quantity": 0,
                "unit_price": 10.0,
            },
            {
                "order_id": "ORD-2",
                "customer_id": "CUST-1",
                "order_date": "2026-01-01 12:00:00",
                "quantity": -2,
                "unit_price": 10.0,
            },
            {
                "order_id": "ORD-3",
                "customer_id": "CUST-1",
                "order_date": "2026-01-01 12:00:00",
                "quantity": 2,
                "unit_price": -5.0,
            },
        ]
    )
    accepted, rejected, report = validate_transactions(df)
    assert len(accepted) == 0
    assert len(rejected) == 3
    assert "INVALID_OR_NON_POSITIVE_QUANTITY" in report.reasons_breakdown
    assert "INVALID_OR_NEGATIVE_UNIT_PRICE" in report.reasons_breakdown


def test_validate_missing_required_column():
    """Dataframe missing mandatory columns must raise DataValidationException."""
    df = pd.DataFrame([{"order_id": "ORD-1", "quantity": 1}])
    with pytest.raises(DataValidationException):
        validate_transactions(df)


def test_validate_empty_dataset_raises():
    """Empty dataframe must raise DataValidationException when allow_empty=False."""
    with pytest.raises(DataValidationException):
        validate_transactions(pd.DataFrame())
