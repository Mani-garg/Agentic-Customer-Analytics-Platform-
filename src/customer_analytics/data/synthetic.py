"""Realistic synthetic e-commerce transaction dataset generator."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Union

import numpy as np
import pandas as pd

CATEGORIES = [
    "Electronics",
    "Apparel",
    "Home & Kitchen",
    "Books",
    "Health & Beauty",
    "Sports & Outdoors",
]

COUNTRIES = ["US", "CA", "GB", "DE", "FR", "AU"]


def generate_synthetic_transactions(
    n_customers: int = 1000,
    seed: int = 42,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> pd.DataFrame:
    """Generate a realistic transactional dataset with repeat orders and realistic recency/frequency distributions."""
    rng = np.random.default_rng(seed)

    if start_date is None:
        start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    if end_date is None:
        end_date = datetime(2026, 9, 30, tzinfo=timezone.utc)

    total_days = max(30, (end_date - start_date).days)
    records: List[dict] = []
    order_counter = 1

    # Customer archetypes: high-frequency loyal, regular, and low-frequency / at-risk
    for cid in range(1, n_customers + 1):
        customer_id = f"CUST-{cid:05d}"

        # Assign customer tenure: when did they first join?
        first_order_day = int(rng.integers(0, max(1, total_days - 60)))
        start_date + timedelta(days=first_order_day)

        # Customer archetype probability
        archetype = rng.choice(
            ["loyal", "regular", "churn_prone", "one_and_done"],
            p=[0.20, 0.40, 0.25, 0.15],
        )

        country = rng.choice(COUNTRIES, p=[0.60, 0.10, 0.10, 0.08, 0.07, 0.05])

        if archetype == "one_and_done":
            n_orders = 1
        elif archetype == "loyal":
            n_orders = int(rng.integers(6, 25))
        elif archetype == "regular":
            n_orders = int(rng.integers(2, 8))
        else:  # churn_prone
            n_orders = int(rng.integers(1, 4))

        # Generate timestamps for customer's orders
        if n_orders == 1:
            order_days = [first_order_day]
        else:
            if archetype == "churn_prone":
                # Concentrated early, no recent orders
                max_span = min(total_days // 2, total_days - first_order_day)
                offsets = rng.integers(0, max(2, max_span), size=n_orders)
            else:
                # Spread out through customer's active lifetime
                remaining_span = max(10, total_days - first_order_day)
                offsets = rng.integers(0, remaining_span, size=n_orders)
            offsets.sort()
            order_days = [first_order_day + int(off) for off in offsets]

        for o_day in order_days:
            # Bound date within dataset range
            clamped_day = min(total_days - 1, o_day)
            order_dt = start_date + timedelta(
                days=clamped_day,
                hours=int(rng.integers(0, 24)),
                minutes=int(rng.integers(0, 60)),
            )

            order_id = f"ORD-{order_counter:07d}"
            order_counter += 1

            # Order can have 1 to 3 line items
            n_items = int(rng.choice([1, 2, 3], p=[0.70, 0.22, 0.08]))

            for _item_idx in range(n_items):
                category = str(rng.choice(CATEGORIES))
                product_id = f"PROD-{category[:3].upper()}-{rng.integers(100, 999)}"
                quantity = int(rng.choice([1, 2, 3, 4], p=[0.75, 0.18, 0.05, 0.02]))

                # Log-normal price distribution per category
                base_price = {
                    "Electronics": 120.0,
                    "Apparel": 45.0,
                    "Home & Kitchen": 65.0,
                    "Books": 20.0,
                    "Health & Beauty": 35.0,
                    "Sports & Outdoors": 55.0,
                }.get(category, 50.0)

                unit_price = round(float(rng.lognormal(mean=np.log(base_price), sigma=0.4)), 2)
                unit_price = max(5.0, min(1500.0, unit_price))

                # Occasional discount
                has_discount = rng.random() < 0.25
                discount = (
                    round(float(rng.choice([0.05, 0.10, 0.15, 0.20])), 2) if has_discount else 0.0
                )

                # Status: 95% completed, 3% cancelled/refunded
                order_status = rng.choice(
                    ["completed", "shipped", "cancelled", "refunded"],
                    p=[0.88, 0.08, 0.02, 0.02],
                )

                records.append(
                    {
                        "order_id": order_id,
                        "customer_id": customer_id,
                        "order_date": order_dt.strftime("%Y-%m-%d %H:%M:%S"),
                        "product_id": product_id,
                        "category": category,
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "discount": discount,
                        "country": country,
                        "order_status": order_status,
                        "currency": "USD",
                    }
                )

    df = pd.DataFrame(records)
    # Sort chronologically
    df["order_date"] = pd.to_datetime(df["order_date"])
    df = df.sort_values("order_date").reset_index(drop=True)
    return df


def save_synthetic_data(
    df: pd.DataFrame,
    output_path: Union[str, Path],
) -> Path:
    """Save synthetic dataframe to CSV with parent directory creation."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    return out
