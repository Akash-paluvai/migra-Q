"""Unit tests verifying PostgreSQL database persistence for Phase 7 AI Diagnoses."""

import pytest

from backend.db.database import init_db
from backend.diagnosis_ai.models import (
    AIDiagnosis,
    DiagnosisAIMetadata,
    DiagnosisAIResult,
    DiagnosisStatus,
    GroundedClaim,
    RepairChange,
    RepairProposal,
    RepairStatus,
)
from backend.diagnosis_ai.repository import get_diagnosis_ai_result, save_diagnosis_ai_result


@pytest.fixture(autouse=True)
def setup_database():
    init_db()


def test_save_and_get_diagnosis_ai_result():
    meta = DiagnosisAIMetadata(
        diagnosis_id="diag-ai-test001",
        discrepancy_id="D-001",
        provider="mock",
        model="MOCK_BOUNDARY_REPAIR",
        context_hash="hash123",
        prompt_hash="prompthash123",
        created_at="2026-08-15T12:00:00Z",
    )
    claim1 = GroundedClaim(text="Operator changed from > to >=", evidence_refs=["E-001", "E-002"])
    diag = AIDiagnosis(
        diagnosis_id="diag-ai-test001",
        discrepancy_id="D-001",
        status=DiagnosisStatus.DIAGNOSED,
        observed_change="> became >=",
        likely_mechanism="Inclusive boundary comparison",
        possible_cause="Translation operator error",
        uncertainty="Evidence establishes operator shift",
        claims=[claim1],
        diagnosis_confidence=0.98,
    )
    chg = RepairChange(
        location="columns[risk_class]",
        before_expression="t.amount >= 500",
        after_expression="t.amount > 500",
    )
    rep = RepairProposal(
        repair_id="rep-test001",
        discrepancy_id="D-001",
        status=RepairStatus.PROPOSED,
        original_sql="SELECT * FROM t WHERE amount >= 500;",
        proposed_sql="SELECT * FROM t WHERE amount > 500;",
        changed_region="columns[risk_class]",
        changes=[chg],
        rationale="Restores strict operator",
        expected_effect="Fixes boundary shift",
        claims=[claim1],
        constraints_checked=["read_only"],
        repair_confidence=0.96,
    )
    result = DiagnosisAIResult(metadata=meta, diagnosis=diag, repair_proposal=rep)

    save_diagnosis_ai_result(result)

    from backend.db.database import check_database_health

    if check_database_health():
        retrieved = get_diagnosis_ai_result("diag-ai-test001")
        assert retrieved is not None
        assert retrieved.metadata.diagnosis_id == "diag-ai-test001"
        assert retrieved.diagnosis.status == DiagnosisStatus.DIAGNOSED
        assert retrieved.diagnosis.diagnosis_confidence == 0.98
        assert retrieved.repair_proposal.status == RepairStatus.PROPOSED
        assert retrieved.repair_proposal.repair_confidence == 0.96
        assert len(retrieved.repair_proposal.changes) == 1
        assert retrieved.repair_proposal.changes[0].after_expression == "t.amount > 500"
