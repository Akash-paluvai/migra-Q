"""Tests for account generator."""

import numpy as np
from faker import Faker

from backend.lab.config import get_profile
from backend.lab.generators.accounts import generate_accounts
from backend.lab.generators.customers import generate_customers


def test_account_generator_relationships():
    profile = get_profile("dev")
    rng = np.random.RandomState(42)
    fake = Faker()
    fake.seed_instance(42)

    cust_df = generate_customers(profile, rng, fake)
    acct_df = generate_accounts(cust_df, profile, rng, fake)

    assert len(acct_df) == 40000
    assert acct_df["account_id"].is_unique

    # All customer references must exist
    cust_set = set(cust_df["customer_id"])
    acct_cust_set = set(acct_df["customer_id"])
    assert acct_cust_set.issubset(cust_set)

    allowed_types = {"CHECKING", "SAVINGS", "CREDIT", "INVESTMENT"}
    assert set(acct_df["account_type"].unique()).issubset(allowed_types)
