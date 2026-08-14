"""Dataset integrity validation and profiling engine."""

from typing import Any

import pandas as pd

from backend.lab.models import ColumnProfileStats, DatasetProfileStats, TableProfileStats


def validate_dataset_integrity(dfs: dict[str, pd.DataFrame]) -> dict[str, Any]:
    """Perform integrity checks on a generated dataset.

    Returns dict of check results and list of violations.
    """
    violations = []
    checks = {}

    cust_df = dfs.get("customers")
    acct_df = dfs.get("accounts")
    tx_df = dfs.get("transactions")
    case_df = dfs.get("support_cases")

    # 1-4. Uniqueness of primary keys
    if cust_df is not None:
        checks["customers_pk_unique"] = bool(cust_df["customer_id"].is_unique)
        if not checks["customers_pk_unique"]:
            violations.append("Duplicate customer_id values found in customers table")

    if acct_df is not None:
        checks["accounts_pk_unique"] = bool(acct_df["account_id"].is_unique)
        if not checks["accounts_pk_unique"]:
            violations.append("Duplicate account_id values found in accounts table")

    if tx_df is not None:
        checks["transactions_pk_unique"] = bool(tx_df["transaction_id"].is_unique)
        if not checks["transactions_pk_unique"]:
            violations.append("Duplicate transaction_id values found in transactions table")

    if case_df is not None:
        checks["support_cases_pk_unique"] = bool(case_df["case_id"].is_unique)
        if not checks["support_cases_pk_unique"]:
            violations.append("Duplicate case_id values found in support_cases table")

    # 5. Accounts reference valid customers
    if acct_df is not None and cust_df is not None:
        valid_cust_ids = set(cust_df["customer_id"].dropna())
        acct_cust_ids = set(acct_df["customer_id"].dropna())
        orphans = acct_cust_ids - valid_cust_ids
        checks["accounts_customer_fk"] = len(orphans) == 0
        if len(orphans) > 0:
            violations.append(
                f"Accounts table contains {len(orphans)} orphan customer_id references"
            )

    # 6. Transactions reference valid accounts
    if tx_df is not None and acct_df is not None:
        valid_acct_ids = set(acct_df["account_id"].dropna())
        tx_acct_ids = set(tx_df["account_id"].dropna())
        orphans = tx_acct_ids - valid_acct_ids
        checks["transactions_account_fk"] = len(orphans) == 0
        if len(orphans) > 0:
            violations.append(
                f"Transactions table contains {len(orphans)} orphan account_id references"
            )

    # 7. Transaction customer_id matches Account customer_id
    if tx_df is not None and acct_df is not None:
        merged = tx_df.dropna(subset=["account_id", "customer_id"]).merge(
            acct_df[["account_id", "customer_id"]].dropna(),
            on="account_id",
            suffixes=("_tx", "_acct"),
        )
        mismatch_count = int((merged["customer_id_tx"] != merged["customer_id_acct"]).sum())
        checks["transactions_customer_consistency"] = mismatch_count == 0
        if mismatch_count > 0:
            violations.append(
                f"Transactions contain {mismatch_count} customer_id mismatches with account"
            )

    # 8. Support cases reference valid customers
    if case_df is not None and cust_df is not None:
        valid_cust_ids = set(cust_df["customer_id"].dropna())
        case_cust_ids = set(case_df["customer_id"].dropna())
        orphans = case_cust_ids - valid_cust_ids
        checks["support_cases_customer_fk"] = len(orphans) == 0
        if len(orphans) > 0:
            violations.append(f"Support cases contain {len(orphans)} orphan customer_id references")

    # 9-10. Domain constraints and categorical values
    if cust_df is not None:
        allowed_segments = {"MASS", "AFFLUENT", "PREMIUM"}
        invalid_segs = set(cust_df["customer_segment"].dropna()) - allowed_segments
        checks["customers_allowed_segments"] = len(invalid_segs) == 0
        if len(invalid_segs) > 0:
            violations.append(f"Invalid customer segments: {invalid_segs}")

    is_valid = len(violations) == 0

    return {
        "is_valid": is_valid,
        "checks": checks,
        "violations": violations,
    }


def compute_dataset_profile(dataset_id: str, dfs: dict[str, pd.DataFrame]) -> DatasetProfileStats:
    """Compute statistical profile metrics for all tables in a dataset."""
    table_stats = {}

    for table_name, df in dfs.items():
        col_stats = {}
        n = len(df)

        for col in df.columns:
            series = df[col]
            null_count = int(series.isna().sum())
            null_rate = round(float(null_count / n), 4) if n > 0 else 0.0
            distinct_cnt = int(series.nunique(dropna=True))

            min_val = None
            max_val = None
            cat_dist = {}

            if pd.api.types.is_numeric_dtype(series):
                valid_s = series.dropna()
                if not valid_s.empty:
                    min_val = float(valid_s.min())
                    max_val = float(valid_s.max())
            elif pd.api.types.is_string_dtype(series) or isinstance(
                series.dtype, pd.CategoricalDtype
            ):
                if distinct_cnt <= 20:
                    val_counts = series.value_counts(normalize=True, dropna=True)
                    cat_dist = {str(k): round(float(v), 4) for k, v in val_counts.items()}

            col_stats[col] = ColumnProfileStats(
                null_rate=null_rate,
                distinct_count=distinct_cnt,
                min_val=min_val,
                max_val=max_val,
                categorical_distribution=cat_dist,
            )

        table_stats[table_name] = TableProfileStats(
            row_count=n,
            column_stats=col_stats,
        )

    return DatasetProfileStats(
        dataset_id=dataset_id,
        table_stats=table_stats,
    )
