"""API integration tests for Phase 8 repair verification endpoints."""

from fastapi.testclient import TestClient

from backend.core.config import settings
from backend.diagnosis_ai.models import (
    AIDiagnosis,
    DiagnosisAIMetadata,
    DiagnosisAIResult,
    DiagnosisStatus,
    RepairProposal,
    RepairStatus,
)
from backend.diagnosis_ai.repository import save_diagnosis_ai_result
from backend.main import app
from backend.repair_verification.models import (
    DiscrepancyOutcomeStatus,
    RepairOutcome,
    RepairVerificationResult,
    VerificationMetadata,
    VerificationStatus,
)
from backend.repair_verification.repository import save_verification_result

# Ensure test mode for persistence fallback
settings.APP_ENV = "test"
settings.PERSISTENCE_MODE = "memory"

client = TestClient(app)


def test_api_create_repair_verification_candidate_rejected():
    meta = DiagnosisAIMetadata(
        diagnosis_id="diag-ai-rep-api002",
        discrepancy_id="D-001",
        provider="mock",
        model="MOCK",
        context_hash="chash",
        prompt_hash="phash",
    )
    diag = AIDiagnosis(
        diagnosis_id="diag-ai-rep-api002",
        discrepancy_id="D-001",
        status=DiagnosisStatus.DIAGNOSED,
        observed_change="Shift",
    )
    # Unchanged proposed_sql -> triggers CANDIDATE_REJECTED
    rep = RepairProposal(
        repair_id="rep-api002",
        diagnosis_id="diag-ai-rep-api002",
        discrepancy_id="D-001",
        status=RepairStatus.PROPOSED,
        original_sql="SELECT * FROM t WHERE val >= 500;",
        proposed_sql="SELECT * FROM t WHERE val >= 500;",
    )
    save_diagnosis_ai_result(DiagnosisAIResult(metadata=meta, diagnosis=diag, repair_proposal=rep))

    payload = {
        "repair_id": "rep-api002",
        "discrepancy_id": "D-001",
        "target_dialect": "bigquery",
    }
    resp = client.post("/api/v1/repair-verifications", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "CANDIDATE_REJECTED"
    assert data["metadata"]["rejection_reason"] == "UNCHANGED_REPAIR_SQL"


def test_api_get_repair_verification_by_id():
    meta = VerificationMetadata(
        verification_id="ver-api-test001",
        repair_id="rep-001",
        discrepancy_id="D-001",
        validation_id_before="val-1",
        execution_id_before="exec-1",
        dataset_id="ds-1",
        dataset_hash_before="dshash",
        validation_config_hash_before="cfghash",
    )
    res = RepairVerificationResult(
        verification_id="ver-api-test001",
        repair_id="rep-001",
        discrepancy_id="D-001",
        validation_id_before="val-1",
        execution_id_before="exec-1",
        status=VerificationStatus.VERIFIED,
        metadata=meta,
        summary="Verified API Test",
    )
    save_verification_result(res)

    get_resp = client.get("/api/v1/repair-verifications/ver-api-test001")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["verification_id"] == "ver-api-test001"
    assert data["status"] == "VERIFIED"


def test_api_get_repair_outcomes():
    meta = VerificationMetadata(
        verification_id="ver-api-test002",
        repair_id="rep-002",
        discrepancy_id="D-001",
        validation_id_before="val-1",
        execution_id_before="exec-1",
        dataset_id="ds-1",
        dataset_hash_before="dshash",
        validation_config_hash_before="cfghash",
    )
    outcome = RepairOutcome(
        discrepancy_id_before="D-001",
        status=DiscrepancyOutcomeStatus.RESOLVED,
        affected_rows_before=10512,
        affected_rows_after=0,
        reduction_count=10512,
        reduction_percentage=100.0,
        summary="Resolved",
    )
    res = RepairVerificationResult(
        verification_id="ver-api-test002",
        repair_id="rep-002",
        discrepancy_id="D-001",
        validation_id_before="val-1",
        execution_id_before="exec-1",
        status=VerificationStatus.VERIFIED,
        outcomes=[outcome],
        metadata=meta,
        summary="Verified API Test",
    )
    save_verification_result(res)

    get_resp = client.get("/api/v1/repair-verifications/ver-api-test002/outcomes")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert len(data) == 1
    assert data[0]["status"] == "RESOLVED"


def test_api_get_nonexistent_verification_returns_404():
    resp = client.get("/api/v1/repair-verifications/ver-nonexistent-999")
    assert resp.status_code == 404
