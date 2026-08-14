"""Account entity generator — produces realistic account records tied to customers."""

from datetime import datetime, timezone

import numpy as np
import pandas as pd
from faker import Faker

from backend.lab.config import DatasetProfile


def generate_accounts(
    customers_df: pd.DataFrame,
    profile: DatasetProfile,
    rng: np.random.RandomState,
    fake: Faker,
) -> pd.DataFrame:
    """Generate synthetic account DataFrame referencing valid customers."""
    n = profile.num_accounts
    cust_ids = customers_df["customer_id"].values

    account_ids = [f"ACCT-{i + 1:08d}" for i in range(n)]

    # Assign accounts to customers (each customer gets at least 1 account, then remaining assigned)
    num_cust = len(cust_ids)
    if n >= num_cust:
        assigned_cust_ids = list(cust_ids) + list(rng.choice(cust_ids, size=n - num_cust))
    else:
        assigned_cust_ids = list(rng.choice(cust_ids, size=n))

    # Shuffle assignment deterministically
    assigned_cust_ids = list(rng.permutation(assigned_cust_ids))

    account_types = rng.choice(
        ["CHECKING", "SAVINGS", "CREDIT", "INVESTMENT"],
        size=n,
        p=[0.45, 0.35, 0.15, 0.05],
    )

    statuses = rng.choice(["ACTIVE", "CLOSED", "FROZEN"], size=n, p=[0.85, 0.12, 0.03])

    base_date = datetime(2016, 1, 1, tzinfo=timezone.utc).timestamp()
    end_date = datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp()
    opened_ts = rng.uniform(base_date, end_date, size=n)
    opened_at = [pd.Timestamp(ts, unit="s", tz="UTC").isoformat() for ts in opened_ts]

    closed_at = []
    for i in range(n):
        if statuses[i] == "CLOSED":
            # closed between opened and 2024-01-01
            c_ts = rng.uniform(opened_ts[i], end_date)
            closed_at.append(pd.Timestamp(c_ts, unit="s", tz="UTC").isoformat())
        else:
            closed_at.append(None)

    balances = np.zeros(n)
    credit_limits = np.zeros(n)

    for i in range(n):
        atype = account_types[i]
        if atype == "CHECKING":
            balances[i] = round(float(rng.uniform(100, 15000)), 2)
            credit_limits[i] = 0.0
        elif atype == "SAVINGS":
            balances[i] = round(float(rng.uniform(500, 75000)), 2)
            credit_limits[i] = 0.0
        elif atype == "CREDIT":
            limit = float(rng.choice([1000, 2500, 5000, 10000, 20000]))
            credit_limits[i] = limit
            # balance is current debt
            balances[i] = round(float(rng.uniform(0, limit * 0.8)), 2)
        else:  # INVESTMENT
            balances[i] = round(float(rng.uniform(2000, 250000)), 2)
            credit_limits[i] = 0.0

    df = pd.DataFrame(
        {
            "account_id": account_ids,
            "customer_id": assigned_cust_ids,
            "account_type": account_types,
            "opened_at": opened_at,
            "closed_at": closed_at,
            "balance": balances,
            "credit_limit": credit_limits,
            "status": statuses,
            "currency": ["USD"] * n,
        }
    )

    return df
