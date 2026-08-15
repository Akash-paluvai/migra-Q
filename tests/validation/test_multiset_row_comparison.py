"""Regression tests for non-unique row key multiset comparison safety."""

from backend.validation.comparison.relations import compare_relations


def test_same_multiset_reordered_rows_passes():
    """Same multiset of duplicate-key rows in different physical order returns PASS."""
    src_sample = [
        {"customer_id": "C1", "amount": 100.0, "status": "ACTIVE"},
        {"customer_id": "C1", "amount": 200.0, "status": "PENDING"},
    ]
    tgt_sample = [
        {"customer_id": "C1", "amount": 200.0, "status": "PENDING"},
        {"customer_id": "C1", "amount": 100.0, "status": "ACTIVE"},
    ]

    res = compare_relations(
        source_artifact=None,
        target_artifact=None,
        source_sample=src_sample,
        target_sample=tgt_sample,
        comparison_keys=["customer_id"],
    )

    assert res["mismatch_count"] == 0
    assert res["score"] == 1.0
    assert res["duplicate_key_warnings"] == 1
    # Check non-unique key warning was captured
    warns = [e for e in res["evidence"] if e.type == "DUPLICATE_KEY_WARNING"]
    assert len(warns) == 1
    assert "NON_UNIQUE_KEY_WARNING" in warns[0].category


def test_different_multiset_duplicate_keys_fails():
    """Different multiset for duplicate keys generates value mismatch evidence."""
    src_sample = [
        {"customer_id": "C1", "amount": 100.0, "status": "ACTIVE"},
        {"customer_id": "C1", "amount": 500.0, "status": "NORMAL"},
    ]
    tgt_sample = [
        {"customer_id": "C1", "amount": 100.0, "status": "ACTIVE"},
        {"customer_id": "C1", "amount": 500.0, "status": "HIGH_RISK"},
    ]

    res = compare_relations(
        source_artifact=None,
        target_artifact=None,
        source_sample=src_sample,
        target_sample=tgt_sample,
        comparison_keys=["customer_id"],
    )

    assert res["mismatch_count"] == 1
    assert res["duplicate_key_warnings"] == 1
    val_mismatches = [e for e in res["evidence"] if e.type == "VALUE_MISMATCH"]
    assert len(val_mismatches) == 1
    assert val_mismatches[0].column == "status"
    assert val_mismatches[0].source_value == "NORMAL"
    assert val_mismatches[0].target_value == "HIGH_RISK"


def test_overlapping_duplicate_keys_extra_missing_rows():
    """Target with extra duplicate row records missing source/target evidence."""
    src_sample = [
        {"customer_id": "C1", "amount": 100.0},
    ]
    tgt_sample = [
        {"customer_id": "C1", "amount": 100.0},
        {"customer_id": "C1", "amount": 200.0},
    ]

    res = compare_relations(
        source_artifact=None,
        target_artifact=None,
        source_sample=src_sample,
        target_sample=tgt_sample,
        comparison_keys=["customer_id"],
    )

    assert res["mismatch_count"] == 1
    extra_ev = [e for e in res["evidence"] if e.type == "MISSING_SOURCE_ROW"]
    assert len(extra_ev) == 1
