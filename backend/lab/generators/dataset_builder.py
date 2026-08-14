"""Base dataset builder function for creating deterministic normal datasets."""

import numpy as np
import pandas as pd
from faker import Faker

from backend.lab.config import get_profile
from backend.lab.generators.accounts import generate_accounts
from backend.lab.generators.customers import generate_customers
from backend.lab.generators.support_cases import generate_support_cases
from backend.lab.generators.transactions import generate_transactions


def build_base_dataset(seed: int = 42, profile_name: str = "dev") -> dict[str, pd.DataFrame]:
    """Generate clean, base normal dataset given seed and profile."""
    profile = get_profile(profile_name)

    # Independent RNGs for reproducible generation across entities
    rng_cust = np.random.RandomState(seed)
    fake_cust = Faker()
    fake_cust.seed_instance(seed)

    rng_acct = np.random.RandomState(seed + 1)
    fake_acct = Faker()
    fake_acct.seed_instance(seed + 1)

    rng_tx = np.random.RandomState(seed + 2)
    fake_tx = Faker()
    fake_tx.seed_instance(seed + 2)

    rng_case = np.random.RandomState(seed + 3)
    fake_case = Faker()
    fake_case.seed_instance(seed + 3)

    cust_df = generate_customers(profile, rng_cust, fake_cust)
    acct_df = generate_accounts(cust_df, profile, rng_acct, fake_acct)
    tx_df = generate_transactions(acct_df, cust_df, profile, rng_tx, fake_tx)
    case_df = generate_support_cases(cust_df, profile, rng_case, fake_case)

    return {
        "customers": cust_df,
        "accounts": acct_df,
        "transactions": tx_df,
        "support_cases": case_df,
    }
