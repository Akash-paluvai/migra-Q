"""Relationship validation utilities for generated DataFrames."""

import pandas as pd


def verify_referential_integrity(
    customers_df: pd.DataFrame,
    accounts_df: pd.DataFrame,
    transactions_df: pd.DataFrame,
    support_cases_df: pd.DataFrame,
) -> dict[str, bool]:
    """Verify primary keys and foreign key relationships across normal generated data."""
    results = {}

    cust_ids = set(customers_df["customer_id"])
    acct_ids = set(accounts_df["account_id"])

    # 1. Accounts reference valid customers
    orphan_accts = set(accounts_df["customer_id"]) - cust_ids
    results["accounts_customer_fk"] = len(orphan_accts) == 0

    # 2. Transactions reference valid accounts
    orphan_tx_accts = set(transactions_df["account_id"]) - acct_ids
    results["transactions_account_fk"] = len(orphan_tx_accts) == 0

    # 3. Transactions customer_id matches account.customer_id
    merged_tx = transactions_df.merge(
        accounts_df[["account_id", "customer_id"]],
        on="account_id",
        suffixes=("_tx", "_acct"),
    )
    mismatched_cust = (merged_tx["customer_id_tx"] != merged_tx["customer_id_acct"]).sum()
    results["transactions_customer_consistency"] = bool(mismatched_cust == 0)

    # 4. Support cases reference valid customers
    orphan_cases = set(support_cases_df["customer_id"]) - cust_ids
    results["support_cases_customer_fk"] = len(orphan_cases) == 0

    # 5. Primary keys uniqueness
    results["customers_pk_unique"] = bool(customers_df["customer_id"].is_unique)
    results["accounts_pk_unique"] = bool(accounts_df["account_id"].is_unique)
    results["transactions_pk_unique"] = bool(transactions_df["transaction_id"].is_unique)
    results["support_cases_pk_unique"] = bool(support_cases_df["case_id"].is_unique)

    return results
