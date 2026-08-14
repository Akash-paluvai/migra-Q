"""Tests for relationship verification utility."""

from backend.lab.generators.dataset_builder import build_base_dataset
from backend.lab.generators.relationships import verify_referential_integrity


def test_normal_dataset_relationships():
    dfs = build_base_dataset(seed=42, profile_name="dev")
    results = verify_referential_integrity(
        dfs["customers"],
        dfs["accounts"],
        dfs["transactions"],
        dfs["support_cases"],
    )

    for check_name, is_ok in results.items():
        assert is_ok, f"Relationship check '{check_name}' failed for normal dataset"
