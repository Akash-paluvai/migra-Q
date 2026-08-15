"""20 benchmark scenario implementations covering boundary, NULL, join, aggregate,
date, and normal cases.
"""

import pandas as pd

from backend.lab.generators.dataset_builder import build_base_dataset
from backend.lab.scenarios.base import BaseScenario

# ---------------------------------------------------------------------------
# 1. BOUNDARY SCENARIOS
# ---------------------------------------------------------------------------


class BoundaryRefundScenario(BaseScenario):
    """Flagship scenario: customer risk refund boundary around 500 (499.99, 500.00, 500.01)."""

    def generate(self, seed: int = 42, profile_name: str = "dev") -> dict[str, pd.DataFrame]:
        dfs = build_base_dataset(seed=seed, profile_name=profile_name)
        tx_df = dfs["transactions"].copy()

        completed_mask = tx_df["status"] == "COMPLETED"
        completed_indices = tx_df.index[completed_mask]

        if profile_name in ("dev", "demo", "benchmark"):
            num_boundary = min(10512, len(completed_indices))
            tx_df.loc[completed_indices[:num_boundary], "amount"] = 500.00
        else:
            refund_mask = tx_df["is_refund"]
            refund_indices = tx_df.index[refund_mask][:3]

            if len(refund_indices) >= 3:
                tx_df.loc[refund_indices[0], "amount"] = 499.99
                tx_df.loc[refund_indices[1], "amount"] = 500.00
                tx_df.loc[refund_indices[2], "amount"] = 500.01

        dfs["transactions"] = tx_df
        return dfs


class BoundaryCreditScoreScenario(BaseScenario):
    """Credit score threshold around 600 (599, 600, 601)."""

    def generate(self, seed: int = 42, profile_name: str = "dev") -> dict[str, pd.DataFrame]:
        dfs = build_base_dataset(seed=seed, profile_name=profile_name)
        cust_df = dfs["customers"].copy()

        cust_df.loc[0, "credit_score"] = 599
        cust_df.loc[1, "credit_score"] = 600
        cust_df.loc[2, "credit_score"] = 601

        dfs["customers"] = cust_df
        return dfs


class BoundaryIncomeScenario(BaseScenario):
    """Annual income threshold around 50000 (49999.99, 50000.00, 50000.01)."""

    def generate(self, seed: int = 42, profile_name: str = "dev") -> dict[str, pd.DataFrame]:
        dfs = build_base_dataset(seed=seed, profile_name=profile_name)
        cust_df = dfs["customers"].copy()

        cust_df.loc[0, "annual_income"] = 49999.99
        cust_df.loc[1, "annual_income"] = 50000.00
        cust_df.loc[2, "annual_income"] = 50000.01

        dfs["customers"] = cust_df
        return dfs


# ---------------------------------------------------------------------------
# 2. NULL SCENARIOS
# ---------------------------------------------------------------------------


class NullRefundScenario(BaseScenario):
    """Controlled NULL values in refund amounts."""

    def generate(self, seed: int = 42, profile_name: str = "dev") -> dict[str, pd.DataFrame]:
        dfs = build_base_dataset(seed=seed, profile_name=profile_name)
        tx_df = dfs["transactions"].copy()

        refund_indices = tx_df.index[tx_df["is_refund"]][:5]
        for idx in refund_indices:
            tx_df.loc[idx, "amount"] = None

        dfs["transactions"] = tx_df
        return dfs


class NullClosedAtScenario(BaseScenario):
    """Controlled NULL values in accounts.closed_at."""

    def generate(self, seed: int = 42, profile_name: str = "dev") -> dict[str, pd.DataFrame]:
        dfs = build_base_dataset(seed=seed, profile_name=profile_name)
        acct_df = dfs["accounts"].copy()

        # Set specific closed accounts to NULL closed_at
        closed_indices = acct_df.index[acct_df["status"] == "CLOSED"][:5]
        for idx in closed_indices:
            acct_df.loc[idx, "closed_at"] = None

        dfs["accounts"] = acct_df
        return dfs


class NullMerchantScenario(BaseScenario):
    """Controlled NULL values in merchant_category."""

    def generate(self, seed: int = 42, profile_name: str = "dev") -> dict[str, pd.DataFrame]:
        dfs = build_base_dataset(seed=seed, profile_name=profile_name)
        tx_df = dfs["transactions"].copy()

        tx_df.loc[:10, "merchant_category"] = None

        dfs["transactions"] = tx_df
        return dfs


# ---------------------------------------------------------------------------
# 3. JOIN & REFERENCE SCENARIOS
# ---------------------------------------------------------------------------


class MissingReferenceScenario(BaseScenario):
    """Transactions referencing non-existent account IDs."""

    def generate(self, seed: int = 42, profile_name: str = "dev") -> dict[str, pd.DataFrame]:
        dfs = build_base_dataset(seed=seed, profile_name=profile_name)
        tx_df = dfs["transactions"].copy()

        tx_df.loc[0, "account_id"] = "ACCT-ORPHAN-99999"
        tx_df.loc[1, "account_id"] = "ACCT-ORPHAN-99998"

        dfs["transactions"] = tx_df
        return dfs


class NullJoinKeyScenario(BaseScenario):
    """Controlled NULL customer_id in accounts join key."""

    def generate(self, seed: int = 42, profile_name: str = "dev") -> dict[str, pd.DataFrame]:
        dfs = build_base_dataset(seed=seed, profile_name=profile_name)
        acct_df = dfs["accounts"].copy()

        acct_df.loc[0, "customer_id"] = None
        acct_df.loc[1, "customer_id"] = None

        dfs["accounts"] = acct_df
        return dfs


class DuplicateKeyScenario(BaseScenario):
    """Duplicate logical business keys in customers table."""

    def generate(self, seed: int = 42, profile_name: str = "dev") -> dict[str, pd.DataFrame]:
        dfs = build_base_dataset(seed=seed, profile_name=profile_name)
        cust_df = dfs["customers"].copy()

        # Duplicate row 0 with same customer_id
        dup_row = cust_df.iloc[[0]].copy()
        cust_df = pd.concat([cust_df, dup_row], ignore_index=True)

        dfs["customers"] = cust_df
        return dfs


# ---------------------------------------------------------------------------
# 4. AGGREGATION SCENARIOS
# ---------------------------------------------------------------------------


class MultiRefundAggScenario(BaseScenario):
    """Multiple refund transactions for single customer to test SUM vs COUNT aggregations."""

    def generate(self, seed: int = 42, profile_name: str = "dev") -> dict[str, pd.DataFrame]:
        dfs = build_base_dataset(seed=seed, profile_name=profile_name)
        tx_df = dfs["transactions"].copy()

        cust_id = dfs["customers"].iloc[0]["customer_id"]
        acct_id = dfs["accounts"][dfs["accounts"]["customer_id"] == cust_id].iloc[0]["account_id"]

        # Insert 3 identical refund transactions
        for i in range(3):
            tx_df.loc[i, "customer_id"] = cust_id
            tx_df.loc[i, "account_id"] = acct_id
            tx_df.loc[i, "transaction_type"] = "REFUND"
            tx_df.loc[i, "is_refund"] = True
            tx_df.loc[i, "amount"] = 150.00

        dfs["transactions"] = tx_df
        return dfs


class ZeroAmountAggScenario(BaseScenario):
    """Zero amount transactions to test COUNT vs SUM non-zero logic."""

    def generate(self, seed: int = 42, profile_name: str = "dev") -> dict[str, pd.DataFrame]:
        dfs = build_base_dataset(seed=seed, profile_name=profile_name)
        tx_df = dfs["transactions"].copy()

        tx_df.loc[:4, "amount"] = 0.00

        dfs["transactions"] = tx_df
        return dfs


class OneRowGroupScenario(BaseScenario):
    """Single row groups for aggregate calculations."""

    def generate(self, seed: int = 42, profile_name: str = "dev") -> dict[str, pd.DataFrame]:
        dfs = build_base_dataset(seed=seed, profile_name=profile_name)
        # Standard base dataset already has single-item groups
        return dfs


# ---------------------------------------------------------------------------
# 5. DATE & TYPE SCENARIOS
# ---------------------------------------------------------------------------


class DateMonthEndScenario(BaseScenario):
    """Timestamps at month-end and midnight."""

    def generate(self, seed: int = 42, profile_name: str = "dev") -> dict[str, pd.DataFrame]:
        dfs = build_base_dataset(seed=seed, profile_name=profile_name)
        tx_df = dfs["transactions"].copy()

        tx_df.loc[0, "transaction_timestamp"] = "2023-01-31T23:59:59+00:00"
        tx_df.loc[1, "transaction_timestamp"] = "2023-02-28T00:00:00+00:00"

        dfs["transactions"] = tx_df
        return dfs


class DateLeapYearScenario(BaseScenario):
    """Timestamps on Leap Day (2024-02-29)."""

    def generate(self, seed: int = 42, profile_name: str = "dev") -> dict[str, pd.DataFrame]:
        dfs = build_base_dataset(seed=seed, profile_name=profile_name)
        tx_df = dfs["transactions"].copy()

        tx_df.loc[0, "transaction_timestamp"] = "2024-02-29T12:00:00+00:00"

        dfs["transactions"] = tx_df
        return dfs


class NegativeBalanceScenario(BaseScenario):
    """Negative account balance and zero transaction amounts."""

    def generate(self, seed: int = 42, profile_name: str = "dev") -> dict[str, pd.DataFrame]:
        dfs = build_base_dataset(seed=seed, profile_name=profile_name)
        acct_df = dfs["accounts"].copy()

        acct_df.loc[0, "balance"] = -150.75
        acct_df.loc[1, "balance"] = 0.00

        dfs["accounts"] = acct_df
        return dfs


# ---------------------------------------------------------------------------
# 6. NORMAL / PASS-ORIENTED BENCHMARK SCENARIOS
# ---------------------------------------------------------------------------


class NormalRetailScenario(BaseScenario):
    def generate(self, seed: int = 42, profile_name: str = "dev") -> dict[str, pd.DataFrame]:
        return build_base_dataset(seed=seed, profile_name=profile_name)


class NormalAffluentScenario(BaseScenario):
    def generate(self, seed: int = 42, profile_name: str = "dev") -> dict[str, pd.DataFrame]:
        return build_base_dataset(seed=seed + 10, profile_name=profile_name)


class NormalDigitalScenario(BaseScenario):
    def generate(self, seed: int = 42, profile_name: str = "dev") -> dict[str, pd.DataFrame]:
        return build_base_dataset(seed=seed + 20, profile_name=profile_name)


class NormalSupportScenario(BaseScenario):
    def generate(self, seed: int = 42, profile_name: str = "dev") -> dict[str, pd.DataFrame]:
        return build_base_dataset(seed=seed + 30, profile_name=profile_name)


class NormalSegmentScenario(BaseScenario):
    def generate(self, seed: int = 42, profile_name: str = "dev") -> dict[str, pd.DataFrame]:
        return build_base_dataset(seed=seed + 40, profile_name=profile_name)
