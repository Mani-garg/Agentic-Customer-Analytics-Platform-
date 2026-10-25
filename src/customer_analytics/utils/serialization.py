"""Custom JSON serialization utilities for NumPy, Pandas, Dates, and Pydantic."""

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel


class PlatformJSONEncoder(json.JSONEncoder):
    """JSON encoder supporting domain models, numpy types, and datetimes."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        return super().default(obj)


def to_json(obj: Any, indent: int = 2) -> str:
    """Serialize object to formatted JSON string."""
    return json.dumps(obj, cls=PlatformJSONEncoder, indent=indent)
