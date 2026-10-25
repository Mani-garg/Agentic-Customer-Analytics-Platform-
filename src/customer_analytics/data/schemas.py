"""Data contracts and schemas for raw e-commerce transactions and feature tables."""

from typing import Dict, List, Set

# Mandatory columns for raw transaction ingestion
REQUIRED_TRANSACTION_COLUMNS: List[str] = [
    "order_id",
    "customer_id",
    "order_date",
    "quantity",
    "unit_price",
]

# Optional transaction columns that enhance analytics when present
OPTIONAL_TRANSACTION_COLUMNS: List[str] = [
    "product_id",
    "category",
    "discount",
    "country",
    "order_status",
    "currency",
]

ALL_TRANSACTION_COLUMNS: List[str] = REQUIRED_TRANSACTION_COLUMNS + OPTIONAL_TRANSACTION_COLUMNS

# Column data type mappings for robust parsing
TRANSACTION_COLUMN_TYPES: Dict[str, str] = {
    "order_id": "string",
    "customer_id": "string",
    "order_date": "datetime64[ns]",
    "product_id": "string",
    "category": "string",
    "quantity": "int64",
    "unit_price": "float64",
    "discount": "float64",
    "country": "string",
    "order_status": "string",
    "currency": "string",
}

# Feature table columns required for model training and inference
REQUIRED_FEATURE_COLUMNS: List[str] = [
    "customer_id",
    "observation_date",
    "recency_days",
    "frequency",
    "monetary_value",
    "average_order_value",
    "customer_tenure_days",
    "days_since_first_purchase",
    "purchase_gap_mean",
    "purchase_gap_std",
    "historical_order_count",
    "historical_revenue",
]

MODEL_FEATURE_NAMES: List[str] = [
    "recency_days",
    "frequency",
    "monetary_value",
    "average_order_value",
    "customer_tenure_days",
    "days_since_first_purchase",
    "purchase_gap_mean",
    "purchase_gap_std",
    "historical_order_count",
    "historical_revenue",
]

ALLOWED_STATUSES: Set[str] = {"completed", "shipped", "pending", "cancelled", "refunded"}
ALLOWED_CURRENCIES: Set[str] = {"USD", "EUR", "GBP", "CAD", "AUD"}
