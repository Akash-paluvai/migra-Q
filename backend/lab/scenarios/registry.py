"""Scenario registry — central library of 20 benchmark dataset & scenario specifications."""

from backend.lab.scenarios.base import BaseScenario, ScenarioMetadata
from backend.lab.scenarios.cases.benchmark_cases import (
    BoundaryCreditScoreScenario,
    BoundaryIncomeScenario,
    BoundaryRefundScenario,
    DateLeapYearScenario,
    DateMonthEndScenario,
    DuplicateKeyScenario,
    MissingReferenceScenario,
    MultiRefundAggScenario,
    NegativeBalanceScenario,
    NormalAffluentScenario,
    NormalDigitalScenario,
    NormalRetailScenario,
    NormalSegmentScenario,
    NormalSupportScenario,
    NullClosedAtScenario,
    NullJoinKeyScenario,
    NullMerchantScenario,
    NullRefundScenario,
    OneRowGroupScenario,
    ZeroAmountAggScenario,
)

BENCHMARK_SCENARIOS: dict[str, ScenarioMetadata] = {
    # Flagship & Boundary Cases (3)
    "BOUNDARY_REFUND_001": ScenarioMetadata(
        scenario_id="BOUNDARY_REFUND_001",
        name="Customer Risk Refund Threshold Boundary",
        category="BOUNDARY",
        description=(
            "Flagship scenario testing refund amount threshold around 500 (499.99, 500.00, 500.01)."
        ),
        expected_behavior="Exposes migration logic changing > 500 to >= 500.",
        affected_tables=["transactions", "customers"],
        scenario_params={"threshold": 500.00},
    ),
    "BOUNDARY_CREDIT_001": ScenarioMetadata(
        scenario_id="BOUNDARY_CREDIT_001",
        name="Credit Score Threshold Boundary",
        category="BOUNDARY",
        description="Credit score threshold testing around 600 (599, 600, 601).",
        expected_behavior="Exposes credit rating boundary discrepancies.",
        affected_tables=["customers"],
        scenario_params={"threshold": 600},
    ),
    "BOUNDARY_INCOME_001": ScenarioMetadata(
        scenario_id="BOUNDARY_INCOME_001",
        name="Annual Income Threshold Boundary",
        category="BOUNDARY",
        description="Income classification boundary around 50000 (49999.99, 50000.00, 50000.01).",
        expected_behavior="Exposes income tier assignment boundary errors.",
        affected_tables=["customers"],
        scenario_params={"threshold": 50000.00},
    ),
    # NULL Cases (3)
    "NULL_REFUND_001": ScenarioMetadata(
        scenario_id="NULL_REFUND_001",
        name="Controlled NULL Refund Amounts",
        category="NULL",
        description="Controlled NULL values in transaction.amount for refund transactions.",
        expected_behavior="Tests SQL 3-valued logic in SUM/AVG aggregations.",
        affected_tables=["transactions"],
    ),
    "NULL_CLOSED_AT_001": ScenarioMetadata(
        scenario_id="NULL_CLOSED_AT_001",
        name="Controlled NULL Account Closed Timestamp",
        category="NULL",
        description="Controlled NULL values in accounts.closed_at for CLOSED status accounts.",
        expected_behavior="Tests COALESCE and NULL date filtering.",
        affected_tables=["accounts"],
    ),
    "NULL_MERCHANT_001": ScenarioMetadata(
        scenario_id="NULL_MERCHANT_001",
        name="Controlled NULL Merchant Category",
        category="NULL",
        description="Controlled NULL values in transactions.merchant_category.",
        expected_behavior="Tests GROUP BY behavior with NULL categories.",
        affected_tables=["transactions"],
    ),
    # Join & Reference Cases (3)
    "MISSING_REF_001": ScenarioMetadata(
        scenario_id="MISSING_REF_001",
        name="Orphan Transaction Account References",
        category="MISSING_REFERENCES",
        description="Transactions referencing non-existent account IDs.",
        expected_behavior="Tests INNER JOIN vs LEFT JOIN row drop semantics.",
        affected_tables=["transactions", "accounts"],
    ),
    "NULL_JOIN_KEY_001": ScenarioMetadata(
        scenario_id="NULL_JOIN_KEY_001",
        name="NULL Foreign Join Key",
        category="NULL_JOIN_KEYS",
        description="Accounts with NULL customer_id join key.",
        expected_behavior="Tests non-matching join key behavior in SQL joins.",
        affected_tables=["accounts", "customers"],
    ),
    "DUPLICATE_KEY_001": ScenarioMetadata(
        scenario_id="DUPLICATE_KEY_001",
        name="Duplicate Customer Primary Keys",
        category="DUPLICATE_KEYS",
        description="Duplicate customer records with identical customer_id.",
        expected_behavior="Tests row duplication and cardinality explosion in joins.",
        affected_tables=["customers"],
    ),
    # Aggregation Cases (3)
    "MULTI_REFUND_AGG_001": ScenarioMetadata(
        scenario_id="MULTI_REFUND_AGG_001",
        name="Multi-Refund Customer Grouping",
        category="AGGREGATION",
        description="Multiple refund transactions for a single customer.",
        expected_behavior="Exposes COUNT vs COUNT DISTINCT and SUM differences.",
        affected_tables=["transactions", "customers"],
    ),
    "ZERO_AMOUNT_AGG_001": ScenarioMetadata(
        scenario_id="ZERO_AMOUNT_AGG_001",
        name="Zero Amount Transactions in Aggregations",
        category="AGGREGATION",
        description="Transactions with amount = 0.00.",
        expected_behavior="Tests SUM vs COUNT > 0 aggregation behavior.",
        affected_tables=["transactions"],
    ),
    "ONE_ROW_GROUP_001": ScenarioMetadata(
        scenario_id="ONE_ROW_GROUP_001",
        name="Single-Row Aggregation Groups",
        category="AGGREGATION",
        description="Single transaction groups for customer aggregation.",
        expected_behavior="Tests edge case aggregation group handling.",
        affected_tables=["transactions"],
    ),
    # Date & Type Cases (3)
    "DATE_MONTH_END_001": ScenarioMetadata(
        scenario_id="DATE_MONTH_END_001",
        name="Month-End and Midnight Timestamps",
        category="DATE_EDGES",
        description="Timestamps on month boundaries and exact midnight.",
        expected_behavior="Tests date truncation and boundary filtering.",
        affected_tables=["transactions"],
    ),
    "DATE_LEAP_YEAR_001": ScenarioMetadata(
        scenario_id="DATE_LEAP_YEAR_001",
        name="Leap Year Timestamps",
        category="DATE_EDGES",
        description="Transactions occurring on 2024-02-29 (Leap Day).",
        expected_behavior="Tests date math and leap-year calendar handling.",
        affected_tables=["transactions"],
    ),
    "NEGATIVE_BALANCE_001": ScenarioMetadata(
        scenario_id="NEGATIVE_BALANCE_001",
        name="Negative Account Balances",
        category="ZERO_NEGATIVE",
        description="Accounts with negative balances.",
        expected_behavior="Tests sign assumptions in account metric calculations.",
        affected_tables=["accounts"],
    ),
    # Normal Pass-oriented Cases (5)
    "NORMAL_RETAIL_001": ScenarioMetadata(
        scenario_id="NORMAL_RETAIL_001",
        name="Standard Retail Banking Customer Flow",
        category="NORMAL",
        description="Baseline clean dataset representing normal retail banking activity.",
        expected_behavior="100% referential integrity and valid domain distributions.",
        affected_tables=["customers", "accounts", "transactions", "support_cases"],
    ),
    "NORMAL_AFFLUENT_001": ScenarioMetadata(
        scenario_id="NORMAL_AFFLUENT_001",
        name="Affluent Customer Segment Dataset",
        category="NORMAL",
        description="Baseline clean dataset for affluent customer cohort.",
        expected_behavior="100% referential integrity.",
        affected_tables=["customers", "accounts", "transactions", "support_cases"],
    ),
    "NORMAL_DIGITAL_001": ScenarioMetadata(
        scenario_id="NORMAL_DIGITAL_001",
        name="Digital First Channel Transaction Flow",
        category="NORMAL",
        description="Baseline clean dataset focusing on online/mobile channels.",
        expected_behavior="100% referential integrity.",
        affected_tables=["customers", "accounts", "transactions", "support_cases"],
    ),
    "NORMAL_SUPPORT_001": ScenarioMetadata(
        scenario_id="NORMAL_SUPPORT_001",
        name="Customer Support Resolution Flow",
        category="NORMAL",
        description="Baseline dataset with normal support case lifecycle.",
        expected_behavior="100% referential integrity.",
        affected_tables=["customers", "support_cases"],
    ),
    "NORMAL_SEGMENT_001": ScenarioMetadata(
        scenario_id="NORMAL_SEGMENT_001",
        name="Multi-Segment Enterprise Dataset",
        category="NORMAL",
        description="Baseline enterprise dataset across all customer segments.",
        expected_behavior="100% referential integrity.",
        affected_tables=["customers", "accounts", "transactions", "support_cases"],
    ),
}

_SCENARIO_CLASS_MAP = {
    "BOUNDARY_REFUND_001": BoundaryRefundScenario,
    "BOUNDARY_CREDIT_001": BoundaryCreditScoreScenario,
    "BOUNDARY_INCOME_001": BoundaryIncomeScenario,
    "NULL_REFUND_001": NullRefundScenario,
    "NULL_CLOSED_AT_001": NullClosedAtScenario,
    "NULL_MERCHANT_001": NullMerchantScenario,
    "MISSING_REF_001": MissingReferenceScenario,
    "NULL_JOIN_KEY_001": NullJoinKeyScenario,
    "DUPLICATE_KEY_001": DuplicateKeyScenario,
    "MULTI_REFUND_AGG_001": MultiRefundAggScenario,
    "ZERO_AMOUNT_AGG_001": ZeroAmountAggScenario,
    "ONE_ROW_GROUP_001": OneRowGroupScenario,
    "DATE_MONTH_END_001": DateMonthEndScenario,
    "DATE_LEAP_YEAR_001": DateLeapYearScenario,
    "NEGATIVE_BALANCE_001": NegativeBalanceScenario,
    "NORMAL_RETAIL_001": NormalRetailScenario,
    "NORMAL_AFFLUENT_001": NormalAffluentScenario,
    "NORMAL_DIGITAL_001": NormalDigitalScenario,
    "NORMAL_SUPPORT_001": NormalSupportScenario,
    "NORMAL_SEGMENT_001": NormalSegmentScenario,
}


def get_scenario(scenario_id: str) -> BaseScenario:
    """Instantiate a scenario generator by ID."""
    if scenario_id not in BENCHMARK_SCENARIOS:
        valid = ", ".join(BENCHMARK_SCENARIOS.keys())
        raise ValueError(f"Unknown scenario_id '{scenario_id}'. Available scenarios: {valid}")
    meta = BENCHMARK_SCENARIOS[scenario_id]
    cls = _SCENARIO_CLASS_MAP[scenario_id]
    return cls(meta)


def list_all_scenarios() -> list[ScenarioMetadata]:
    """Return list of metadata for all 20 registered benchmark scenarios."""
    return list(BENCHMARK_SCENARIOS.values())
