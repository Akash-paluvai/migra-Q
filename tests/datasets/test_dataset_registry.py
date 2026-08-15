"""Unit tests for Phase 10.1 Dataset Registry."""

from __future__ import annotations

from backend.datasets.registry import DatasetRegistry


def test_dataset_registry_lists_builtin_datasets():
    registry = DatasetRegistry()
    summaries = registry.list_datasets()
    assert len(summaries) >= 6

    builtin_ids = {s.dataset_id for s in summaries if s.is_builtin}
    expected_builtins = {
        "customer_risk",
        "customer_aggregation",
        "null_semantics",
        "join_semantics",
        "date_semantics",
        "mixed_business_logic",
    }
    assert expected_builtins.issubset(builtin_ids)


def test_builtin_datasets_have_distinct_hashes():
    registry = DatasetRegistry()
    summaries = registry.list_datasets()
    builtin_summaries = [s for s in summaries if s.is_builtin]

    hashes = [s.dataset_hash for s in builtin_summaries]
    assert len(hashes) == len(set(hashes)), "Built-in datasets must have distinct content/schema hashes"


def test_dataset_schema_resolution():
    registry = DatasetRegistry()
    schema = registry.resolve_schema("customer_risk")
    assert len(schema) >= 4
    table_names = {t.table_name for t in schema}
    assert {"customers", "accounts", "transactions", "support_cases"}.issubset(table_names)


def test_dataset_preview_row_limit_enforcement():
    registry = DatasetRegistry()
    preview_10 = registry.resolve_preview("customer_risk", "transactions", limit=10)
    assert preview_10.returned_rows <= 10
    assert len(preview_10.rows) <= 10

    # Requesting over 100 limit must be capped at 100
    preview_200 = registry.resolve_preview("customer_risk", "transactions", limit=200)
    assert preview_200.returned_rows <= 100
    assert len(preview_200.rows) <= 100
