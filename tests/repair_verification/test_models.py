"""Unit tests for Phase 8 repair verification domain models."""

from backend.repair_verification.models import (
    VERIFICATION_ENGINE_VERSION,
    DiscrepancyOutcome,
    DiscrepancyOutcomeStatus,
    RepairOutcome,
    RepairVerificationResult,
    VerificationEvidenceItem,
    VerificationMetadata,
    VerificationStatus,
)


def test_verification_status_enum_values():
    assert VerificationStatus.VERIFIED == "VERIFIED"
    assert VerificationStatus.FAILED_VERIFICATION == "FAILED_VERIFICATION"
    assert VerificationStatus.PARTIALLY_RESOLVED == "PARTIALLY_RESOLVED"
    assert VerificationStatus.NEW_DISCREPANCIES == "NEW_DISCREPANCIES"
    assert VerificationStatus.EXECUTION_FAILED == "EXECUTION_FAILED"
    assert VerificationStatus.CANDIDATE_REJECTED == "CANDIDATE_REJECTED"
    assert VerificationStatus.INSUFFICIENT_EVIDENCE == "INSUFFICIENT_EVIDENCE"


def test_discrepancy_outcome_status_enum_values():
    assert DiscrepancyOutcomeStatus.RESOLVED == "RESOLVED"
    assert DiscrepancyOutcomeStatus.PERSISTS == "PERSISTS"
    assert DiscrepancyOutcomeStatus.CHANGED == "CHANGED"
    assert DiscrepancyOutcomeStatus.UNABLE_TO_MATCH == "UNABLE_TO_MATCH"


def test_evidence_item_model_instantiation():
    ev = VerificationEvidenceItem(
        evidence_id="EV-001",
        evidence_type="BEFORE_VALIDATION_REF",
        description="Reference to validation ID",
        details={"val_id": "val-123"},
    )
    assert ev.evidence_id == "EV-001"
    assert ev.details["val_id"] == "val-123"


def test_discrepancy_outcome_model_instantiation():
    disc_out = DiscrepancyOutcome(
        discrepancy_id_before="D-001",
        category="BOUNDARY_CONDITION",
        analysis_path="where_clause",
        affected_region="columns[risk_class]",
        status=DiscrepancyOutcomeStatus.RESOLVED,
        affected_rows_before=10512,
        affected_rows_after=0,
        reduction_count=10512,
        reduction_percentage=100.0,
    )
    assert disc_out.discrepancy_id_before == "D-001"
    assert disc_out.status == DiscrepancyOutcomeStatus.RESOLVED
    assert disc_out.reduction_percentage == 100.0


def test_repair_outcome_model_instantiation():
    rep_out = RepairOutcome(
        discrepancy_id_before="D-001",
        status=DiscrepancyOutcomeStatus.RESOLVED,
        affected_rows_before=10512,
        affected_rows_after=0,
        reduction_count=10512,
        reduction_percentage=100.0,
        summary="Discrepancy D-001 resolved.",
    )
    assert rep_out.discrepancy_id_before == "D-001"
    assert rep_out.status == DiscrepancyOutcomeStatus.RESOLVED
    assert rep_out.reduction_count == 10512


def test_verification_metadata_defaults():
    meta = VerificationMetadata(
        verification_id="ver-001",
        repair_id="rep-001",
        discrepancy_id="D-001",
        validation_id_before="val-before",
        execution_id_before="exec-before",
        dataset_id="ds-test",
        dataset_hash_before="hash-before",
        validation_config_hash_before="cfg-before",
    )
    assert meta.verification_id == "ver-001"
    assert meta.verification_version == VERIFICATION_ENGINE_VERSION
    assert meta.persistence_status == "PERSISTED"
    assert meta.rejection_reason is None


def test_repair_verification_result_serialization():
    meta = VerificationMetadata(
        verification_id="ver-001",
        repair_id="rep-001",
        discrepancy_id="D-001",
        validation_id_before="val-before",
        execution_id_before="exec-before",
        dataset_id="ds-test",
        dataset_hash_before="hash-before",
        validation_config_hash_before="cfg-before",
    )
    res = RepairVerificationResult(
        verification_id="ver-001",
        repair_id="rep-001",
        discrepancy_id="D-001",
        validation_id_before="val-before",
        execution_id_before="exec-before",
        status=VerificationStatus.VERIFIED,
        original_discrepancy_count=1,
        remaining_discrepancy_count=0,
        new_discrepancy_count=0,
        resolved_discrepancy_count=1,
        affected_rows_before=10512,
        affected_rows_after=0,
        reduction_count=10512,
        reduction_percentage=100.0,
        original_target_sql="SELECT * FROM t WHERE amount >= 500;",
        repaired_target_sql="SELECT * FROM t WHERE amount > 500;",
        metadata=meta,
        summary="Verified",
    )
    dumped = res.model_dump()
    assert dumped["status"] == "VERIFIED"
    assert dumped["reduction_percentage"] == 100.0
    assert dumped["metadata"]["verification_id"] == "ver-001"


def test_forbidden_terms_not_used():
    """Verify that forbidden status terms (APPROVED, PRODUCTION_READY, SAFE, SUCCESSFUL) are not present in VerificationStatus."""
    invalid_terms = ["APPROVED", "PRODUCTION_READY", "SAFE", "SUCCESSFUL"]
    for term in invalid_terms:
        assert term not in [s.value for s in VerificationStatus]
