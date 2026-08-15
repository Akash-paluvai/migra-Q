"""Regression tests enforcing MIGRA-Q explicit PostgreSQL persistence policy across environments."""

from unittest.mock import MagicMock, patch

import pytest

from backend.core.config import settings
from backend.diagnosis_ai.exceptions import PersistenceError
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
from backend.diagnosis_ai.repository import save_diagnosis_ai_result


def _build_dummy_result() -> DiagnosisAIResult:
    meta = DiagnosisAIMetadata(
        diagnosis_id="diag-policy-test01",
        discrepancy_id="D-POLICY-01",
        provider="mock",
        model="mock-model",
        context_hash="hash123",
        prompt_hash="prompthash123",
        created_at="2026-08-15T12:00:00Z",
    )
    diag = AIDiagnosis(
        diagnosis_id="diag-policy-test01",
        discrepancy_id="D-POLICY-01",
        status=DiagnosisStatus.DIAGNOSED,
        observed_change="Operator change",
        likely_mechanism="Inclusive comparison",
        possible_cause="Operator shift",
        uncertainty="High confidence",
        claims=[GroundedClaim(text="Operator changed", evidence_refs=["E-001"])],
        diagnosis_confidence=0.95,
    )
    chg = RepairChange(
        location="columns[risk_class]",
        before_expression=">= 500",
        after_expression="> 500",
    )
    rep = RepairProposal(
        repair_id="rep-policy-test01",
        discrepancy_id="D-POLICY-01",
        status=RepairStatus.PROPOSED,
        original_sql="SELECT * FROM t WHERE val >= 500;",
        proposed_sql="SELECT * FROM t WHERE val > 500;",
        changed_region="columns[risk_class]",
        changes=[chg],
        rationale="Fix operator",
        expected_effect="Restore strict threshold",
        claims=[GroundedClaim(text="Operator fixed", evidence_refs=["E-001"])],
        constraints_checked=["read_only"],
        repair_confidence=0.95,
    )
    return DiagnosisAIResult(metadata=meta, diagnosis=diag, repair_proposal=rep)


def test_persistence_policy_dev_env_postgres_down_raises_error():
    result = _build_dummy_result()
    with patch.object(settings, "APP_ENV", "development"):
        with patch("backend.diagnosis_ai.repository.get_db_session", side_effect=Exception("PostgreSQL Connection Refused")):
            with pytest.raises(PersistenceError) as exc_info:
                save_diagnosis_ai_result(result)
            assert "development" in str(exc_info.value)
            assert result.metadata.persistence_status == "FAILED_PERSISTENCE"


def test_persistence_policy_demo_env_postgres_down_raises_error():
    result = _build_dummy_result()
    with patch.object(settings, "APP_ENV", "demo"):
        with patch("backend.diagnosis_ai.repository.get_db_session", side_effect=Exception("PostgreSQL Connection Refused")):
            with pytest.raises(PersistenceError) as exc_info:
                save_diagnosis_ai_result(result)
            assert "demo" in str(exc_info.value)
            assert result.metadata.persistence_status == "FAILED_PERSISTENCE"


def test_persistence_policy_prod_env_postgres_down_raises_error():
    result = _build_dummy_result()
    with patch.object(settings, "APP_ENV", "production"):
        with patch("backend.diagnosis_ai.repository.get_db_session", side_effect=Exception("PostgreSQL Connection Refused")):
            with pytest.raises(PersistenceError) as exc_info:
                save_diagnosis_ai_result(result)
            assert "production" in str(exc_info.value)
            assert result.metadata.persistence_status == "FAILED_PERSISTENCE"


def test_persistence_policy_test_env_allowed():
    result = _build_dummy_result()
    with patch.object(settings, "APP_ENV", "test"):
        with patch.object(settings, "PERSISTENCE_MODE", "memory"):
            with patch("backend.diagnosis_ai.repository.get_db_session", side_effect=Exception("PostgreSQL Connection Refused")):
                # Must not raise PersistenceError in test mode
                save_diagnosis_ai_result(result)
                assert result.metadata.persistence_status == "PERSISTED"


def test_persistence_policy_explicit_session_success():
    result = _build_dummy_result()
    mock_session = MagicMock()
    save_diagnosis_ai_result(result, session=mock_session)
    assert mock_session.add.call_count == 3
    assert mock_session.commit.called
    assert result.metadata.persistence_status == "PERSISTED"
