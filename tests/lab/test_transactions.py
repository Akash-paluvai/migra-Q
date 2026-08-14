"""Tests for transaction generator."""

import numpy as np
from faker import Faker

from backend.lab.config import get_profile
from backend.lab.generators.accounts import generate_accounts
from backend.lab.generators.customers import generate_customers
from backend.lab.generators.transactions import generate_transactions


def test_transaction_generator_relationships():
    profile = get_profile("dev")
    rng = np.random.RandomState(42)
    fake = Faker()
    fake.seed_instance(42)

    cust_df = generate_customers(profile, rng, fake)
    acct_df = generate_accounts(cust_df, profile, rng, fake)
    tx_df = generate_transactions(acct_df, cust_df, profile, rng, fake)

    assert len(tx_df) == 200000
    assert tx_df["transaction_id"].is_unique

    # Verify transaction.customer_id == account.customer_id
    merged = tx_df.merge(
        acct_df[["account_id", "customer_id"]], on="account_id", suffixes=("_tx", "_acct")
    )
    assert (merged["customer_id_tx"] == merged["customer_id_acct"]).all()
