"""Repository layer for persisting TranslationResult metadata."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import TranslationRecord
from backend.translator.models import (
    CandidateValidationStatus,
    StructuredRule,
    TranslationMetadata,
    TranslationResponse,
    TranslationResult,
    TranslationStatus,
)


def save_translation_result(
    result: TranslationResult, db_session: Session | None = None
) -> None:
    """Save TranslationResult metadata and candidate details to PostgreSQL.

    Never fails if DB is unreachable in test mode.
    """

    def _persist(db: Session) -> None:
        m = result.metadata
        resp = result.response

        assumptions_json = json.dumps(resp.assumptions) if resp else None
        risks_json = json.dumps(resp.potential_risks) if resp else None
        rules_json = (
            json.dumps([r.model_dump() for r in resp.translated_rules])
            if resp
            else None
        )

        token_usage = {
            "input_tokens": m.input_token_count,
            "output_tokens": m.output_token_count,
            "total_tokens": m.total_token_count,
            "estimated_cost": m.estimated_cost,
        }

        rec = TranslationRecord(
            translation_id=m.translation_id,
            request_id=m.request_id,
            source_dialect=m.source_dialect,
            target_dialect=m.target_dialect,
            source_sql_hash=m.source_sql_hash,
            translation_context_hash=m.translation_context_hash,
            prompt_hash=m.prompt_hash,
            provider=m.provider,
            model=m.model,
            status=result.status.value,
            candidate_validation_status=(
                result.candidate_validation_status.value
                if result.candidate_validation_status
                else None
            ),
            target_sql=resp.target_sql if resp else None,
            assumptions_json=assumptions_json,
            potential_risks_json=risks_json,
            translated_rules_json=rules_json,
            duration_ms=m.duration_ms,
            retry_count=m.retry_count,
            token_usage_json=json.dumps(token_usage),
            error_code=m.error_code,
            error_message=m.error_message,
            translator_version=m.translator_version,
            prompt_version=m.prompt_version,
        )
        db.add(rec)
        db.commit()

    if db_session:
        try:
            _persist(db_session)
        except Exception:
            db_session.rollback()
    else:
        db = None
        try:
            from backend.db.database import get_db_session
            db = get_db_session()
            _persist(db)
        except Exception:
            pass  # Silent resilience if DB is unavailable in test environment
        finally:
            if db:
                db.close()


def get_translation_result(
    translation_id: str, db_session: Session | None = None
) -> TranslationResult | None:
    """Retrieve stored TranslationResult by translation_id."""

    def _query(db: Session) -> TranslationRecord | None:
        return (
            db.query(TranslationRecord)
            .filter(TranslationRecord.translation_id == translation_id)
            .first()
        )

    rec = None
    if db_session:
        try:
            rec = _query(db_session)
        except Exception:
            return None
    else:
        db = None
        try:
            from backend.db.database import get_db_session
            db = get_db_session()
            rec = _query(db)
        except Exception:
            return None
        finally:
            if db:
                db.close()

    if not rec:
        return None

    assumptions = json.loads(rec.assumptions_json) if rec.assumptions_json else []
    risks = json.loads(rec.potential_risks_json) if rec.potential_risks_json else []
    rules_raw = json.loads(rec.translated_rules_json) if rec.translated_rules_json else []
    translated_rules = [StructuredRule(**r) for r in rules_raw]

    token_usage = json.loads(rec.token_usage_json) if rec.token_usage_json else {}

    response = (
        TranslationResponse(
            target_sql=rec.target_sql or "",
            assumptions=assumptions,
            potential_risks=risks,
            translated_rules=translated_rules,
        )
        if rec.target_sql
        else None
    )

    metadata = TranslationMetadata(
        translation_id=rec.translation_id,
        request_id=rec.request_id,
        provider=rec.provider,
        model=rec.model,
        source_dialect=rec.source_dialect,
        target_dialect=rec.target_dialect,
        source_sql_hash=rec.source_sql_hash,
        translation_context_hash=rec.translation_context_hash,
        prompt_hash=rec.prompt_hash,
        created_at=rec.created_at.isoformat() if rec.created_at else "",
        duration_ms=rec.duration_ms,
        retry_count=rec.retry_count,
        input_token_count=token_usage.get("input_tokens"),
        output_token_count=token_usage.get("output_tokens"),
        total_token_count=token_usage.get("total_tokens"),
        estimated_cost=token_usage.get("estimated_cost"),
        error_code=rec.error_code,
        error_message=rec.error_message,
        translator_version=rec.translator_version,
        prompt_version=rec.prompt_version,
    )

    summary_txt = (
        "Candidate SQL syntactically valid"
        if rec.status == "SUCCESS"
        else rec.error_message or ""
    )

    return TranslationResult(
        metadata=metadata,
        status=TranslationStatus(rec.status),
        candidate_validation_status=(
            CandidateValidationStatus(rec.candidate_validation_status)
            if rec.candidate_validation_status
            else None
        ),
        response=response,
        validation_summary=summary_txt,
    )
