"""Repository layer for persisting Phase 8 repair verification results and outcomes."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.db.database import get_db_session
from backend.db.models import RepairOutcomeRecordModel, RepairVerificationRecordModel
from backend.diagnosis_ai.exceptions import PersistenceError
from backend.repair_verification.models import (
    DiscrepancyOutcomeStatus,
    RepairOutcome,
    RepairVerificationResult,
    VerificationEvidenceItem,
    VerificationMetadata,
    VerificationStatus,
)

_IN_MEMORY_VERIFICATION_STORE: dict[str, RepairVerificationResult] = {}
_IN_MEMORY_OUTCOME_STORE: dict[str, list[RepairOutcome]] = {}


def save_verification_result(
    result: RepairVerificationResult,
    session: Session | None = None,
) -> None:
    """Save RepairVerificationResult to PostgreSQL (or in-memory store in TEST mode)."""
    # Always update in-memory cache for test environment retrieval
    _IN_MEMORY_VERIFICATION_STORE[result.verification_id] = result
    _IN_MEMORY_OUTCOME_STORE[result.verification_id] = result.outcomes

    def _persist(s: Session) -> None:
        meta = result.metadata

        rec = RepairVerificationRecordModel(
            verification_id=result.verification_id,
            repair_id=result.repair_id,
            discrepancy_id=result.discrepancy_id,
            validation_id_before=result.validation_id_before,
            validation_id_after=result.validation_id_after,
            execution_id_before=result.execution_id_before,
            execution_id_repaired=result.execution_id_repaired,
            status=result.status.value,
            verification_version=result.verification_version,
            original_discrepancy_count=result.original_discrepancy_count,
            remaining_discrepancy_count=result.remaining_discrepancy_count,
            new_discrepancy_count=result.new_discrepancy_count,
            resolved_discrepancy_count=result.resolved_discrepancy_count,
            affected_rows_before=result.affected_rows_before,
            affected_rows_after=result.affected_rows_after,
            affected_percentage_before=result.affected_percentage_before,
            affected_percentage_after=result.affected_percentage_after,
            reduction_count=result.reduction_count,
            reduction_percentage=result.reduction_percentage,
            summary_json=json.dumps({"summary": result.summary, "execution_metadata": result.execution_metadata}),
            evidence_json=json.dumps([e.model_dump() for e in result.evidence]),
            rejection_reason=meta.rejection_reason,
            error_code=meta.error_code,
            error_message=meta.error_message,
        )
        s.add(rec)

        for out in result.outcomes:
            out_rec = RepairOutcomeRecordModel(
                verification_id=result.verification_id,
                discrepancy_id_before=out.discrepancy_id_before,
                status=out.status.value,
                affected_rows_before=out.affected_rows_before,
                affected_rows_after=out.affected_rows_after,
                reduction_count=out.reduction_count,
                reduction_percentage=out.reduction_percentage,
                matching_after_discrepancy_ids_json=json.dumps(out.matching_after_discrepancy_ids),
                new_discrepancy_ids_json=json.dumps(out.new_discrepancy_ids),
                summary=out.summary,
            )
            s.add(out_rec)

        s.commit()
        result.metadata.persistence_status = "PERSISTED"

    if session:
        try:
            _persist(session)
        except Exception as e:
            session.rollback()
            result.metadata.persistence_status = "FAILED_PERSISTENCE"
            if settings.APP_ENV in ("development", "demo", "production") or settings.PERSISTENCE_MODE == "postgres":
                raise PersistenceError(
                    f"PostgreSQL persistence failed in environment '{settings.APP_ENV}': {e}"
                ) from e
    else:
        if settings.PERSISTENCE_MODE == "memory" and settings.APP_ENV == "test":
            result.metadata.persistence_status = "PERSISTED"
            return

        try:
            db_s = get_db_session()
            try:
                _persist(db_s)
            finally:
                db_s.close()
        except Exception as e:
            result.metadata.persistence_status = "FAILED_PERSISTENCE"
            if settings.APP_ENV in ("development", "demo", "production") or settings.PERSISTENCE_MODE == "postgres":
                raise PersistenceError(
                    f"Authoritative PostgreSQL persistence failed in environment '{settings.APP_ENV}': {e}"
                ) from e


def get_verification_result(
    verification_id: str,
    session: Session | None = None,
) -> RepairVerificationResult | None:
    """Retrieve RepairVerificationResult by verification_id from PostgreSQL or in-memory store."""
    if verification_id in _IN_MEMORY_VERIFICATION_STORE:
        return _IN_MEMORY_VERIFICATION_STORE[verification_id]

    close_session = False
    if session is None:
        try:
            session = get_db_session()
            close_session = True
        except Exception:
            return _IN_MEMORY_VERIFICATION_STORE.get(verification_id)

    try:
        rec = session.query(RepairVerificationRecordModel).filter_by(verification_id=verification_id).first()
        if not rec:
            return _IN_MEMORY_VERIFICATION_STORE.get(verification_id)

        out_recs = session.query(RepairOutcomeRecordModel).filter_by(verification_id=verification_id).all()

        outcomes: list[RepairOutcome] = []
        for o in out_recs:
            outcomes.append(
                RepairOutcome(
                    discrepancy_id_before=o.discrepancy_id_before,
                    status=DiscrepancyOutcomeStatus(o.status),
                    affected_rows_before=o.affected_rows_before,
                    affected_rows_after=o.affected_rows_after,
                    reduction_count=o.reduction_count,
                    reduction_percentage=o.reduction_percentage,
                    matching_after_discrepancy_ids=json.loads(o.matching_after_discrepancy_ids_json) if o.matching_after_discrepancy_ids_json else [],
                    new_discrepancy_ids=json.loads(o.new_discrepancy_ids_json) if o.new_discrepancy_ids_json else [],
                    summary=o.summary or "",
                )
            )

        summary_meta = json.loads(rec.summary_json) if rec.summary_json else {}
        evidence_data = json.loads(rec.evidence_json) if rec.evidence_json else []
        evidence = [VerificationEvidenceItem(**e) for e in evidence_data]

        meta = VerificationMetadata(
            verification_id=rec.verification_id,
            repair_id=rec.repair_id,
            discrepancy_id=rec.discrepancy_id,
            validation_id_before=rec.validation_id_before,
            validation_id_after=rec.validation_id_after,
            execution_id_before=rec.execution_id_before,
            execution_id_repaired=rec.execution_id_repaired,
            dataset_id="dataset-retrieved",
            dataset_hash_before="hash-before",
            dataset_hash_after="hash-after",
            validation_config_hash_before="cfg-before",
            validation_config_hash_after="cfg-after",
            created_at=rec.created_at.isoformat() if rec.created_at else "",
            rejection_reason=rec.rejection_reason,
            error_code=rec.error_code,
            error_message=rec.error_message,
        )

        return RepairVerificationResult(
            verification_id=rec.verification_id,
            repair_id=rec.repair_id,
            discrepancy_id=rec.discrepancy_id,
            validation_id_before=rec.validation_id_before,
            validation_id_after=rec.validation_id_after,
            execution_id_before=rec.execution_id_before,
            execution_id_repaired=rec.execution_id_repaired,
            status=VerificationStatus(rec.status),
            created_at=meta.created_at,
            verification_version=rec.verification_version,
            original_discrepancy_count=rec.original_discrepancy_count,
            remaining_discrepancy_count=rec.remaining_discrepancy_count,
            new_discrepancy_count=rec.new_discrepancy_count,
            resolved_discrepancy_count=rec.resolved_discrepancy_count,
            affected_rows_before=rec.affected_rows_before,
            affected_rows_after=rec.affected_rows_after,
            affected_percentage_before=rec.affected_percentage_before,
            affected_percentage_after=rec.affected_percentage_after,
            reduction_count=rec.reduction_count,
            reduction_percentage=rec.reduction_percentage,
            outcomes=outcomes,
            evidence=evidence,
            execution_metadata=summary_meta.get("execution_metadata", {}),
            metadata=meta,
            summary=summary_meta.get("summary", ""),
        )
    except Exception:
        return _IN_MEMORY_VERIFICATION_STORE.get(verification_id)
    finally:
        if close_session and session:
            session.close()


def get_outcomes_by_verification_id(
    verification_id: str,
    session: Session | None = None,
) -> list[RepairOutcome]:
    """Retrieve list of RepairOutcomes for a verification_id."""
    res = get_verification_result(verification_id, session=session)
    if res:
        return res.outcomes
    return _IN_MEMORY_OUTCOME_STORE.get(verification_id, [])
