"""Transaction entity generator — optimized for high-volume (1M+ rows) vectorized generation."""

from datetime import datetime, timezone

import numpy as np
import pandas as pd
from faker import Faker

from backend.lab.config import DatasetProfile


def generate_transactions(
    accounts_df: pd.DataFrame,
    customers_df: pd.DataFrame,
    profile: DatasetProfile,
    rng: np.random.RandomState,
    fake: Faker,
) -> pd.DataFrame:
    """Generate synthetic transaction DataFrame.

    Ensures transaction.customer_id == account.customer_id for all normal records.
    Uses vectorized NumPy operations for speed.
    """
    n = profile.num_transactions

    # Sample account indices for all transactions
    num_accts = len(accounts_df)
    acct_indices = rng.randint(0, num_accts, size=n)

    acct_ids = accounts_df["account_id"].values[acct_indices]
    cust_ids = accounts_df["customer_id"].values[acct_indices]

    tx_ids = [f"TX-{i + 1:010d}" for i in range(n)]

    # Transaction types
    tx_types = rng.choice(
        ["PURCHASE", "REFUND", "TRANSFER", "WITHDRAWAL", "DEPOSIT", "PAYMENT", "FEE"],
        size=n,
        p=[0.55, 0.08, 0.10, 0.12, 0.08, 0.05, 0.02],
    )

    is_refund = tx_types == "REFUND"

    # Amounts: purchases ($5 - $800), refunds ($10 - $600), transfers/deposits ($50 - $3000)
    amounts = np.zeros(n)
    for i in range(n):
        ttype = tx_types[i]
        if ttype == "PURCHASE":
            amounts[i] = round(float(rng.exponential(scale=45.0) + 2.50), 2)
        elif ttype == "REFUND":
            amounts[i] = round(float(rng.uniform(10.0, 600.0)), 2)
        elif ttype in ("TRANSFER", "DEPOSIT", "PAYMENT"):
            amounts[i] = round(float(rng.uniform(50.0, 2500.0)), 2)
        else:
            amounts[i] = round(float(rng.uniform(2.0, 150.0)), 2)

    channels = rng.choice(
        ["ONLINE", "MOBILE", "ATM", "BRANCH", "POS"],
        size=n,
        p=[0.40, 0.35, 0.10, 0.05, 0.10],
    )

    statuses = rng.choice(
        ["COMPLETED", "PENDING", "FAILED", "REVERSED"],
        size=n,
        p=[0.90, 0.05, 0.03, 0.02],
    )

    merchant_cats = [
        "RETAIL",
        "GROCERY",
        "RESTAURANT",
        "TRAVEL",
        "ENTERTAINMENT",
        "UTILITIES",
        "DIGITAL_GOODS",
    ]
    merch_cat_array = rng.choice(merchant_cats, size=n)
    merch_ids = [f"MERCH-{rng.randint(1000, 9999)}" for _ in range(n)]

    # Timestamps between 2022-01-01 and 2024-01-01
    base_date = datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp()
    end_date = datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp()
    timestamps_raw = rng.uniform(base_date, end_date, size=n)
    tx_timestamps = [pd.Timestamp(ts, unit="s", tz="UTC").isoformat() for ts in timestamps_raw]

    # Original tx ids for refunds (link to a random earlier tx_id if possible)
    original_tx_ids = [None] * n
    for i in range(n):
        if is_refund[i] and i > 0:
            ref_idx = rng.randint(0, i)
            original_tx_ids[i] = tx_ids[ref_idx]

    df = pd.DataFrame(
        {
            "transaction_id": tx_ids,
            "account_id": acct_ids,
            "customer_id": cust_ids,
            "transaction_timestamp": tx_timestamps,
            "transaction_type": tx_types,
            "amount": amounts,
            "currency": ["USD"] * n,
            "merchant_category": merch_cat_array,
            "merchant_id": merch_ids,
            "channel": channels,
            "status": statuses,
            "is_refund": is_refund,
            "original_transaction_id": original_tx_ids,
        }
    )

    return df
