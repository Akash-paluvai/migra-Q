"""Translation service layer — main entry point for Phase 6 Translation Engine."""

from __future__ import annotations

import datetime
import time
import uuid

from sqlalchemy.orm import Session

from backend.analyzer.service import analyze
from backend.core.config import settings
from backend.translator.context_builder import build_translation_context
from backend.translator.diff_preview import generate_diff_preview
from backend.translator.models import (
    CandidateValidationStatus,
    TranslationMetadata,
    TranslationRequest,
    TranslationResponse,
    TranslationResult,
    TranslationStatus,
)
from backend.translator.prompts import build_translation_prompt
from backend.translator.provider import LLMProvider, get_llm_provider
from backend.translator.repository import save_translation_result
from backend.translator.validator import validate_candidate_sql

SUPPORTED_DIALECTS = {
    "teradata",
    "bigquery",
    "postgres",
    "duckdb",
    "snowflake",
    "sqlite",
    "oracle",
    "mysql",
    "netezza",
}


class TranslationService:
    """Orchestrates AI SQL translation context building, prompt execution, and validation."""

    @classmethod
    def translate(
        cls,
        request: TranslationRequest,
        provider: LLMProvider | None = None,
        db_session: Session | None = None,
        mock_mode: str | None = None,
    ) -> TranslationResult:
        """Execute translation request and return structured TranslationResult."""
        start_time = time.perf_counter()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        translation_id = f"trans-{uuid.uuid4().hex[:12]}"
        request_id = request.request_id or f"req-{uuid.uuid4().hex[:12]}"

        source_dialect = request.source_dialect.lower()
        target_dialect = request.target_dialect.lower()

        # 1. Dialect support check
        SUPPORTED_DIALECTS = {
            "teradata",
            "bigquery",
            "postgres",
            "duckdb",
            "snowflake",
            "sqlite",
            "oracle",
            "mysql",
            "netezza",
        }

        if source_dialect not in SUPPORTED_DIALECTS or target_dialect not in SUPPORTED_DIALECTS:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            meta = TranslationMetadata(
                translation_id=translation_id,
                request_id=request_id,
                provider=settings.LLM_PROVIDER,
                model=settings.LLM_MODEL,
                source_dialect=request.source_dialect,
                target_dialect=request.target_dialect,
                source_sql_hash="",
                translation_context_hash="",
                prompt_hash="",
                created_at=created_at,
                duration_ms=duration_ms,
                error_code="UNSUPPORTED_DIALECT_PAIR",
                error_message=(
                    f"Unsupported dialect pair: {request.source_dialect} "
                    f"-> {request.target_dialect}"
                ),
            )
            res = TranslationResult(
                metadata=meta,
                status=TranslationStatus.UNSUPPORTED_DIALECT,
                validation_summary="Unsupported dialect pair",
            )
            save_translation_result(res, db_session)
            return res

        # 2. Phase 1 SQL Analysis of Source SQL (Passes source_dialect into analyzer!)
        try:
            source_analysis = analyze(sql=request.source_sql, dialect=request.source_dialect)
            source_sql_hash = source_analysis.sql_hash
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            meta = TranslationMetadata(
                translation_id=translation_id,
                request_id=request_id,
                provider=settings.LLM_PROVIDER,
                model=settings.LLM_MODEL,
                source_dialect=request.source_dialect,
                target_dialect=request.target_dialect,
                source_sql_hash="",
                translation_context_hash="",
                prompt_hash="",
                created_at=created_at,
                duration_ms=duration_ms,
                error_code="INVALID_SOURCE_SQL",
                error_message=f"Source SQL could not be analyzed: {e}",
            )
            res = TranslationResult(
                metadata=meta,
                status=TranslationStatus.FAILED,
                validation_summary="Invalid source SQL",
            )
            save_translation_result(res, db_session)
            return res

        # 3. Build Translation Context & Prompts
        context = build_translation_context(request)
        system_prompt, user_prompt, prompt_hash = build_translation_prompt(context)

        # 4. Resolve Provider
        if provider is None:
            provider = get_llm_provider(mock_mode=mock_mode)

        provider_name = getattr(provider, "name", provider.__class__.__name__)
        model_name = getattr(provider, "model", settings.LLM_MODEL or "mock-model")

        provider_attempts = 1
        raw_resp = None
        last_error_code = None
        last_error_msg = None
        try:
            raw_resp = provider.generate_translation(context, system_prompt, user_prompt)
            provider_attempts = raw_resp.provider_attempts
        except Exception as e:
            if type(e).__name__ == "ProviderTokenExhaustionError":
                last_error_code = "PROVIDER_TOKEN_EXHAUSTED"
            elif type(e).__name__ == "ProviderExecutionTimeoutError":
                last_error_code = "PROVIDER_TIMEOUT"
            elif type(e).__name__ == "NonRetryableProviderError":
                if "AUTH_ERROR" in str(e):
                    last_error_code = "LLM_AUTH_ERROR"
                elif "json_validate_failed" in str(e):
                    last_error_code = "INVALID_STRUCTURED_OUTPUT"
                else:
                    last_error_code = "LLM_PROVIDER_ERROR"
            elif type(e).__name__ == "RateLimitError":
                last_error_code = "LLM_RATE_LIMIT"
            elif type(e).__name__ == "TransientProviderError":
                last_error_code = "LLM_TRANSIENT_ERROR"
            else:
                last_error_code = "LLM_PROVIDER_ERROR"
            
            last_error_msg = str(e)

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        if raw_resp is None:
            status = (
                TranslationStatus.TIMEOUT
                if last_error_code == "LLM_TIMEOUT"
                else TranslationStatus.PROVIDER_ERROR
            )
            meta = TranslationMetadata(
                translation_id=translation_id,
                request_id=request_id,
                provider=provider_name,
                model=model_name,
                source_dialect=request.source_dialect,
                target_dialect=request.target_dialect,
                source_sql_hash=source_sql_hash,
                translation_context_hash=context.context_hash,
                prompt_hash=prompt_hash,
                created_at=created_at,
                duration_ms=duration_ms,
                retry_count=provider_attempts - 1 if provider_attempts > 0 else 0,
                error_code=last_error_code,
                error_message=last_error_msg,
            )
            res = TranslationResult(
                metadata=meta,
                status=status,
                validation_summary=last_error_msg or "Provider execution failed",
            )
            save_translation_result(res, db_session)
            return res

        # 6. Parse Structured Output Pydantic Schema
        try:
            parsed_response = TranslationResponse.model_validate_json(raw_resp.raw_json)
        except Exception as e:
            meta = TranslationMetadata(
                translation_id=translation_id,
                request_id=request_id,
                provider=provider_name,
                model=model_name,
                source_dialect=request.source_dialect,
                target_dialect=request.target_dialect,
                source_sql_hash=source_sql_hash,
                translation_context_hash=context.context_hash,
                prompt_hash=prompt_hash,
                created_at=created_at,
                duration_ms=duration_ms,
                retry_count=provider_attempts - 1 if provider_attempts > 0 else 0,
                input_token_count=raw_resp.input_tokens,
                output_token_count=raw_resp.output_tokens,
                total_token_count=raw_resp.total_tokens,
                error_code="INVALID_STRUCTURED_OUTPUT",
                error_message=f"LLM output could not be parsed into TranslationResponse: {e}",
            )
            res = TranslationResult(
                metadata=meta,
                status=TranslationStatus.INVALID_OUTPUT,
                validation_summary="Invalid structured response format",
            )
            save_translation_result(res, db_session)
            return res

        # 7. Candidate Target SQL Safety & Integrity Validation
        cand_status, err_code, val_msg = validate_candidate_sql(
            target_sql=parsed_response.target_sql,
            target_dialect=request.target_dialect,
            schema_context=request.schema_context,
            source_tables=context.tables,
            source_columns=context.columns,
        )

        overall_status = TranslationStatus.SUCCESS
        if cand_status == CandidateValidationStatus.UNSAFE_SQL:
            overall_status = TranslationStatus.REJECTED
        elif cand_status in (
            CandidateValidationStatus.INVALID_SYNTAX,
            CandidateValidationStatus.SCHEMA_MISMATCH,
        ):
            overall_status = TranslationStatus.FAILED

        meta = TranslationMetadata(
            translation_id=translation_id,
            request_id=request_id,
            provider=provider_name,
            model=model_name,
            source_dialect=request.source_dialect,
            target_dialect=request.target_dialect,
            source_sql_hash=source_sql_hash,
            translation_context_hash=context.context_hash,
            prompt_hash=prompt_hash,
            created_at=created_at,
            duration_ms=duration_ms,
            retry_count=provider_attempts - 1 if provider_attempts > 0 else 0,
            input_token_count=raw_resp.input_tokens,
            output_token_count=raw_resp.output_tokens,
            total_token_count=raw_resp.total_tokens,
            error_code=err_code if err_code else None,
            error_message=val_msg if err_code else None,
        )

        # 8. Structural AST Diff Preview
        _, _, struct_diffs = generate_diff_preview(
            source_sql=request.source_sql,
            source_dialect=request.source_dialect,
            target_sql=parsed_response.target_sql,
            target_dialect=request.target_dialect,
        )

        result = TranslationResult(
            metadata=meta,
            status=overall_status,
            candidate_validation_status=cand_status,
            semantic_status="NOT_EVALUATED",
            response=parsed_response,
            validation_summary=val_msg,
            structural_differences=struct_diffs,
        )

        save_translation_result(result, db_session)
        return result
