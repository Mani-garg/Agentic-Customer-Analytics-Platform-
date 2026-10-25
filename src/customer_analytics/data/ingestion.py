"""Data ingestion layer for raw e-commerce transaction files."""

import logging
from pathlib import Path
from typing import Union

import pandas as pd

from customer_analytics.data.schemas import REQUIRED_TRANSACTION_COLUMNS
from customer_analytics.exceptions import DataValidationException

logger = logging.getLogger(__name__)


def ingest_transactions_csv(
    file_path: Union[str, Path],
    encoding: str = "utf-8",
) -> pd.DataFrame:
    """Read e-commerce transactions from CSV file with boundary and existence validation."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Input transaction file does not exist: {path.resolve()}")
    if not path.is_file():
        raise ValueError(f"Path is not a regular file: {path.resolve()}")

    if path.stat().st_size == 0:
        raise DataValidationException(f"Input transaction file is empty: {path.resolve()}")

    logger.info(
        f"Ingesting transaction CSV from {path.resolve()} (size: {path.stat().st_size} bytes)"
    )

    try:
        df = pd.read_csv(
            path,
            encoding=encoding,
            dtype={
                "order_id": "string",
                "customer_id": "string",
                "product_id": "string",
                "category": "string",
                "country": "string",
                "order_status": "string",
                "currency": "string",
            },
        )
    except Exception as e:
        raise DataValidationException(f"Failed to parse CSV file: {str(e)}") from e

    if df.empty:
        raise DataValidationException(f"Transaction file contains no data rows: {path.resolve()}")

    # Check for missing required columns
    missing_cols = [c for c in REQUIRED_TRANSACTION_COLUMNS if c not in df.columns]
    if missing_cols:
        raise DataValidationException(
            f"Missing required columns in CSV: {missing_cols}",
            details={"missing_columns": missing_cols, "available_columns": list(df.columns)},
        )

    logger.info(f"Ingestion successful: loaded {len(df)} raw transaction rows from {path.name}")
    return df
