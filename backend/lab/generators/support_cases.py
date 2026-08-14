"""Support case entity generator — produces customer service case logs."""

from datetime import datetime, timezone

import numpy as np
import pandas as pd
from faker import Faker

from backend.lab.config import DatasetProfile


def generate_support_cases(
    customers_df: pd.DataFrame,
    profile: DatasetProfile,
    rng: np.random.RandomState,
    fake: Faker,
) -> pd.DataFrame:
    """Generate synthetic support_cases DataFrame referencing valid customers."""
    n = profile.num_support_cases
    cust_ids = customers_df["customer_id"].values

    case_ids = [f"CASE-{i + 1:08d}" for i in range(n)]

    # Assign cases to customers
    assigned_cust_ids = rng.choice(cust_ids, size=n)

    categories = rng.choice(
        ["PAYMENT", "ACCOUNT", "TRANSACTION", "CARD", "FRAUD", "LOGIN", "OTHER"],
        size=n,
        p=[0.25, 0.20, 0.25, 0.10, 0.05, 0.10, 0.05],
    )

    priorities = rng.choice(
        ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        size=n,
        p=[0.50, 0.35, 0.12, 0.03],
    )

    statuses = rng.choice(
        ["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"],
        size=n,
        p=[0.05, 0.10, 0.45, 0.40],
    )

    channels = rng.choice(
        ["PHONE", "EMAIL", "CHAT", "WEB"],
        size=n,
        p=[0.35, 0.30, 0.25, 0.10],
    )

    desc_classes = rng.choice(
        ["DISPUTE", "INQUIRY", "TECHNICAL_ISSUE", "FEE_REVERSAL", "COMPLAINT"],
        size=n,
    )

    base_date = datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp()
    end_date = datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp()
    opened_ts = rng.uniform(base_date, end_date, size=n)
    opened_at = [pd.Timestamp(ts, unit="s", tz="UTC").isoformat() for ts in opened_ts]

    closed_at = []
    resolution_hours = []
    satisfaction_scores = []

    for i in range(n):
        st = statuses[i]
        if st in ("RESOLVED", "CLOSED"):
            # Resolution time: 0.5 to 120 hours
            res_h = round(float(rng.exponential(scale=18.0) + 0.5), 1)
            resolution_hours.append(res_h)

            c_ts = opened_ts[i] + (res_h * 3600)
            closed_at.append(pd.Timestamp(c_ts, unit="s", tz="UTC").isoformat())

            # 1 to 5 score
            satisfaction_scores.append(
                int(rng.choice([1, 2, 3, 4, 5], p=[0.08, 0.12, 0.20, 0.35, 0.25]))
            )
        else:
            closed_at.append(None)
            resolution_hours.append(None)
            satisfaction_scores.append(None)

    df = pd.DataFrame(
        {
            "case_id": case_ids,
            "customer_id": assigned_cust_ids,
            "opened_at": opened_at,
            "closed_at": closed_at,
            "category": categories,
            "priority": priorities,
            "status": statuses,
            "resolution_time_hours": resolution_hours,
            "channel": channels,
            "description_class": desc_classes,
            "satisfaction_score": satisfaction_scores,
        }
    )

    return df
