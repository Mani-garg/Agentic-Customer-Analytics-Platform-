"""Date and timestamp utility functions."""

from datetime import date, datetime, timezone
from typing import Union

import pandas as pd


def parse_datetime(val: Union[str, datetime, date, pd.Timestamp]) -> datetime:
    """Parse various datetime representations into a timezone-aware UTC datetime."""
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val.astimezone(timezone.utc)
    if isinstance(val, pd.Timestamp):
        dt = val.to_pydatetime()
        res: datetime = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
        return res
    if isinstance(val, date):
        return datetime(val.year, val.month, val.day, tzinfo=timezone.utc)
    if isinstance(val, str):
        parsed = pd.to_datetime(val)
        dt = parsed.to_pydatetime() if isinstance(parsed, pd.Timestamp) else datetime.fromisoformat(val)
        res_str: datetime = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
        return res_str
    raise ValueError(f"Unsupported datetime value: {val}")


def parse_date(val: Union[str, datetime, date, pd.Timestamp]) -> date:
    """Extract standard calendar date from input."""
    dt = parse_datetime(val)
    return dt.date()


def calculate_days_between(
    start_date: Union[date, datetime], end_date: Union[date, datetime]
) -> int:
    """Calculate integer days between two dates (end_date - start_date)."""
    d1 = (
        start_date
        if isinstance(start_date, date) and not isinstance(start_date, datetime)
        else parse_date(start_date)
    )
    d2 = (
        end_date
        if isinstance(end_date, date) and not isinstance(end_date, datetime)
        else parse_date(end_date)
    )
    return (d2 - d1).days
