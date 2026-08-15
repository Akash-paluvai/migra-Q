"""Unit tests for Translator Service orchestration."""


from backend.translator.models import (
    CandidateValidationStatus,
    TranslationRequest,
    TranslationStatus,
)
from backend.translator.service import TranslationService


def test_service_successful_translation():
    req = TranslationRequest(
        source_sql=(
            "SELECT customer_id, SUM(amount) FROM transactions "
            "WHERE amount > 500 GROUP BY customer_id;"
        ),
        source_dialect="teradata",
        target_dialect="bigquery",
    )
    res = TranslationService.translate(request=req, mock_mode="MOCK_GOOD")

    assert res.status == TranslationStatus.SUCCESS
    assert res.candidate_validation_status == CandidateValidationStatus.VALID_SYNTAX
    assert res.validation_summary == "Candidate SQL syntactically valid"
    assert res.response is not None
    assert "HIGH_RISK" in res.response.target_sql or "SELECT" in res.response.target_sql


def test_service_unsupported_dialect():
    req = TranslationRequest(
        source_sql="SELECT 1;",
        source_dialect="unknown_dialect",
        target_dialect="bigquery",
    )
    res = TranslationService.translate(request=req)

    assert res.status == TranslationStatus.UNSUPPORTED_DIALECT
    assert res.metadata.error_code == "UNSUPPORTED_DIALECT_PAIR"


def test_service_invalid_source_sql():
    req = TranslationRequest(
        source_sql="SELECT FROM WHERE;",
        source_dialect="teradata",
        target_dialect="bigquery",
    )
    res = TranslationService.translate(request=req)

    assert res.status == TranslationStatus.FAILED
    assert res.metadata.error_code == "INVALID_SOURCE_SQL"


def test_service_mock_unsafe_sql_rejected():
    req = TranslationRequest(
        source_sql="SELECT * FROM customers;",
        source_dialect="teradata",
        target_dialect="bigquery",
    )
    res = TranslationService.translate(request=req, mock_mode="MOCK_UNSAFE_SQL")

    assert res.status == TranslationStatus.REJECTED
    assert res.candidate_validation_status == CandidateValidationStatus.UNSAFE_SQL


def test_service_mock_invalid_json():
    req = TranslationRequest(
        source_sql="SELECT * FROM customers;",
        source_dialect="teradata",
        target_dialect="bigquery",
    )
    res = TranslationService.translate(request=req, mock_mode="MOCK_INVALID_JSON")

    assert res.status == TranslationStatus.INVALID_OUTPUT


def test_service_does_not_invoke_phase3_or_phase4():
    """Verify Phase 6 ends at candidate result and does NOT invoke Phase 3/4/5!"""
    req = TranslationRequest(
        source_sql="SELECT customer_id FROM transactions;",
        source_dialect="teradata",
        target_dialect="bigquery",
    )
    res = TranslationService.translate(request=req, mock_mode="MOCK_GOOD")

    # Has metadata and response, but NO execution_id or validation_id
    assert not hasattr(res, "execution_id")
    assert not hasattr(res, "validation_id")
    assert not hasattr(res, "discrepancies")
