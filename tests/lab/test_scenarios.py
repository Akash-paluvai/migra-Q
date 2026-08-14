"""Tests for scenario generators and scenario registry."""

from backend.lab.scenarios.registry import BENCHMARK_SCENARIOS, get_scenario, list_all_scenarios


def test_scenario_registry_has_20_scenarios():
    scenarios = list_all_scenarios()
    assert len(scenarios) == 20
    assert "BOUNDARY_REFUND_001" in BENCHMARK_SCENARIOS


def test_flagship_boundary_refund_scenario():
    scen = get_scenario("BOUNDARY_REFUND_001")
    dfs = scen.generate(seed=42, profile_name="dev")
    tx_df = dfs["transactions"]

    refund_amounts = set(tx_df[tx_df["is_refund"]]["amount"].dropna())
    assert 499.99 in refund_amounts
    assert 500.00 in refund_amounts
    assert 500.01 in refund_amounts


def test_null_scenario_contains_nulls():
    scen = get_scenario("NULL_REFUND_001")
    dfs = scen.generate(seed=42, profile_name="dev")
    tx_df = dfs["transactions"]

    null_cnt = tx_df["amount"].isna().sum()
    assert null_cnt > 0


def test_missing_reference_scenario():
    scen = get_scenario("MISSING_REF_001")
    dfs = scen.generate(seed=42, profile_name="dev")
    tx_df = dfs["transactions"]

    assert "ACCT-ORPHAN-99999" in tx_df["account_id"].values


def test_duplicate_key_scenario():
    scen = get_scenario("DUPLICATE_KEY_001")
    dfs = scen.generate(seed=42, profile_name="dev")
    cust_df = dfs["customers"]

    assert not cust_df["customer_id"].is_unique


def test_all_20_scenarios_run_cleanly():
    for scenario_id in BENCHMARK_SCENARIOS.keys():
        scen = get_scenario(scenario_id)
        dfs = scen.generate(seed=42, profile_name="test")
        assert "customers" in dfs
        assert "accounts" in dfs
        assert "transactions" in dfs
        assert "support_cases" in dfs
