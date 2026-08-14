"""Tests for integrity validator and data profiler."""

from backend.lab.generators.dataset_builder import build_base_dataset
from backend.lab.validation.integrity import compute_dataset_profile, validate_dataset_integrity


def test_validate_dataset_integrity_pass():
    dfs = build_base_dataset(seed=42, profile_name="dev")
    res = validate_dataset_integrity(dfs)

    assert res["is_valid"] is True
    assert len(res["violations"]) == 0


def test_compute_dataset_profile():
    dfs = build_base_dataset(seed=42, profile_name="dev")
    stats = compute_dataset_profile("dev_42", dfs)

    assert stats.dataset_id == "dev_42"
    assert "customers" in stats.table_stats
    assert stats.table_stats["customers"].row_count == 10000
    assert "credit_score" in stats.table_stats["customers"].column_stats
    col_stat = stats.table_stats["customers"].column_stats["credit_score"]
    assert col_stat.min_val >= 300
    assert col_stat.max_val <= 850
