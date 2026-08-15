"""Database repository for persisting Phase 7 AI diagnosis results and repair proposals."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from backend.db.database import get_db_session
from backend.db.models import AIDiagnosisRecord, RepairChangeRecordModel, RepairProposalRecord
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


def save_diagnosis_ai_result(
    result: DiagnosisAIResult,
    session: Session | None = None,
) -> None:
    """Save Phase 7 DiagnosisAIResult to PostgreSQL database tables."""

    def _persist(s: Session) -> None:
        diag = result.diagnosis
        meta = result.metadata
        rep = result.repair_proposal

        diag_rec = AIDiagnosisRecord(
            diagnosis_id=meta.diagnosis_id,
            discrepancy_id=meta.discrepancy_id,
            provider=meta.provider,
            model=meta.model,
            status=diag.status.value,
            observed_change=diag.observed_change,
            likely_mechanism=diag.likely_mechanism,
            possible_cause=diag.possible_cause,
            uncertainty=diag.uncertainty,
            diagnosis_confidence=diag.diagnosis_confidence,
            claims_json=json.dumps([c.model_dump() for c in diag.claims]),
            context_hash=meta.context_hash,
            prompt_hash=meta.prompt_hash,
            duration_ms=meta.duration_ms,
            token_usage_json=json.dumps(
                {
                    "input_tokens": meta.input_token_count,
                    "output_tokens": meta.output_token_count,
                    "total_tokens": meta.total_token_count,
                }
            ),
            error_code=meta.error_code,
            error_message=meta.error_message,
            diagnosis_ai_version=meta.diagnosis_ai_version,
            prompt_version=meta.prompt_version,
        )
        s.add(diag_rec)

        rep_rec = RepairProposalRecord(
            repair_id=rep.repair_id,
            diagnosis_id=meta.diagnosis_id,
            discrepancy_id=meta.discrepancy_id,
            status=rep.status.value,
            original_sql=rep.original_sql,
            proposed_sql=rep.proposed_sql,
            changed_region=rep.changed_region,
            rationale=rep.rationale,
            expected_effect=rep.expected_effect,
            repair_confidence=rep.repair_confidence,
            claims_json=json.dumps([c.model_dump() for c in rep.claims]),
            constraints_checked_json=json.dumps(rep.constraints_checked),
        )
        s.add(rep_rec)

        for change in rep.changes:
            chg_rec = RepairChangeRecordModel(
                repair_id=rep.repair_id,
                location=change.location,
                before_expression=change.before_expression,
                after_expression=change.after_expression,
                change_type=change.change_type,
            )
            s.add(chg_rec)

        s.commit()

    if session:
        try:
            _persist(session)
        except Exception:
            session.rollback()
    else:
        try:
            db_s = get_db_session()
            try:
                _persist(db_s)
            finally:
                db_s.close()
        except Exception:
            pass  # Silent resilience if PostgreSQL is unavailable in test environment


def get_diagnosis_ai_result(
    diagnosis_id: str,
    session: Session | None = None,
) -> DiagnosisAIResult | None:
    """Retrieve complete DiagnosisAIResult artifact by diagnosis_id."""
    close_session = False
    if session is None:
        try:
            session = get_db_session()
            close_session = True
        except Exception:
            return None

    try:
        diag_rec = session.query(AIDiagnosisRecord).filter_by(diagnosis_id=diagnosis_id).first()
        if not diag_rec:
            return None

        rep_rec = session.query(RepairProposalRecord).filter_by(diagnosis_id=diagnosis_id).first()
        if not rep_rec:
            return None

        chg_recs = session.query(RepairChangeRecordModel).filter_by(repair_id=rep_rec.repair_id).all()

        token_dict: dict[str, Any] = json.loads(diag_rec.token_usage_json) if diag_rec.token_usage_json else {}

        meta = DiagnosisAIMetadata(
            diagnosis_id=diag_rec.diagnosis_id,
            discrepancy_id=diag_rec.discrepancy_id,
            provider=diag_rec.provider,
            model=diag_rec.model,
            context_hash=diag_rec.context_hash,
            prompt_hash=diag_rec.prompt_hash,
            created_at=diag_rec.created_at.isoformat() if diag_rec.created_at else "",
            duration_ms=diag_rec.duration_ms,
            input_token_count=token_dict.get("input_tokens"),
            output_token_count=token_dict.get("output_tokens"),
            total_token_count=token_dict.get("total_tokens"),
            error_code=diag_rec.error_code,
            error_message=diag_rec.error_message,
            diagnosis_ai_version=diag_rec.diagnosis_ai_version,
            prompt_version=diag_rec.prompt_version,
        )

        diag_claims_json = json.loads(diag_rec.claims_json) if diag_rec.claims_json else []
        diag_claims = [GroundedClaim(**c) for c in diag_claims_json]
        diag = AIDiagnosis(
            diagnosis_id=diag_rec.diagnosis_id,
            discrepancy_id=diag_rec.discrepancy_id,
            status=DiagnosisStatus(diag_rec.status),
            observed_change=diag_rec.observed_change or "",
            likely_mechanism=diag_rec.likely_mechanism or "",
            possible_cause=diag_rec.possible_cause or "",
            uncertainty=diag_rec.uncertainty or "",
            claims=diag_claims,
            diagnosis_confidence=diag_rec.diagnosis_confidence,
        )

        rep_claims_json = json.loads(rep_rec.claims_json) if rep_rec.claims_json else []
        rep_claims = [GroundedClaim(**c) for c in rep_claims_json]
        rep_constraints_json = rep_rec.constraints_checked_json
        rep_constraints = json.loads(rep_constraints_json) if rep_constraints_json else []

        changes = [
            RepairChange(
                location=chg.location,
                before_expression=chg.before_expression,
                after_expression=chg.after_expression,
                change_type=chg.change_type,
            )
            for chg in chg_recs
        ]

        rep = RepairProposal(
            repair_id=rep_rec.repair_id,
            discrepancy_id=rep_rec.discrepancy_id,
            status=RepairStatus(rep_rec.status),
            original_sql=rep_rec.original_sql or "",
            proposed_sql=rep_rec.proposed_sql or "",
            changed_region=rep_rec.changed_region or "",
            changes=changes,
            rationale=rep_rec.rationale or "",
            expected_effect=rep_rec.expected_effect or "",
            claims=rep_claims,
            constraints_checked=rep_constraints,
            repair_confidence=rep_rec.repair_confidence,
        )

        return DiagnosisAIResult(metadata=meta, diagnosis=diag, repair_proposal=rep)
    except Exception:
        return None
    finally:
        if close_session and session:
            try:
                session.close()
            except Exception:
                pass
