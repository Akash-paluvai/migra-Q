"""Unit tests verifying the 4 required mock provider scenarios and phase boundary isolation."""


from backend.translator.models import (
    CandidateValidationStatus,
    TranslationRequest,
    TranslationStatus,
)
from backend.translator.service import TranslationService


def test_mock_scenario_1_good():
    """Scenario 1: MOCK_GOOD -> SUCCESS, VALID_SYNTAX."""
    req = TranslationRequest(
        source_sql="SELECT customer_id FROM transactions WHERE amount > 500;",
        source_dialect="teradata",
        target_dialect="bigquery",
    )
    res = TranslationService.translate(request=req, mock_mode="MOCK_GOOD")

    assert res.status == TranslationStatus.SUCCESS
    assert res.candidate_validation_status == CandidateValidationStatus.VALID_SYNTAX
    assert res.validation_summary == "Candidate SQL syntactically valid"


def test_mock_scenario_2_boundary_bug():
    """Scenario 2: MOCK_BOUNDARY_BUG (> 500 -> >= 500).

    MUST return SUCCESS in Phase 6 because candidate SQL is syntactically valid.
    Phase 6 DOES NOT judge semantic correctness (Phase 4/5 will detect the boundary error).
    """
    req = TranslationRequest(
        source_sql="SELECT customer_id FROM transactions WHERE amount > 500;",
        source_dialect="teradata",
        target_dialect="bigquery",
    )
    res = TranslationService.translate(request=req, mock_mode="MOCK_BOUNDARY_BUG")

    # Phase 6 succeeds!
    assert res.status == TranslationStatus.SUCCESS
    assert res.candidate_validation_status == CandidateValidationStatus.VALID_SYNTAX
    assert res.validation_summary == "Candidate SQL syntactically valid"
    assert ">= 500.00" in res.response.target_sql

    # Crucial assertion: Phase 6 NEVER claims correctness or equivalence!
    assert res.validation_summary != "Migration valid"
    assert not hasattr(res.response, "equivalence")


def test_mock_scenario_3_hallucinated_column():
    """Scenario 3: MOCK_HALLUCINATED_COLUMN -> SCHEMA_MISMATCH / FAILED."""
    from backend.translator.models import ColumnSchemaDef, SchemaContext, TableSchema

    schema = SchemaContext(
        tables=[
            TableSchema(
                name="transactions",
                columns=[ColumnSchemaDef(name="customer_id", type="STRING")],
            )
        ]
    )

    req = TranslationRequest(
        source_sql="SELECT customer_id FROM transactions;",
        source_dialect="teradata",
        target_dialect="bigquery",
        schema=schema,
    )
    res = TranslationService.translate(request=req, mock_mode="MOCK_HALLUCINATED_COLUMN")

    assert res.status == TranslationStatus.FAILED
    assert res.candidate_validation_status == CandidateValidationStatus.SCHEMA_MISMATCH
    assert "nonexistent_column" in res.validation_summary


def test_mock_scenario_4_unsafe_sql():
    """Scenario 4: MOCK_UNSAFE_SQL (DROP TABLE) -> REJECTED, UNSAFE_SQL."""
    req = TranslationRequest(
        source_sql="SELECT customer_id FROM transactions;",
        source_dialect="teradata",
        target_dialect="bigquery",
    )
    res = TranslationService.translate(request=req, mock_mode="MOCK_UNSAFE_SQL")

    assert res.status == TranslationStatus.REJECTED
    assert res.candidate_validation_status == CandidateValidationStatus.UNSAFE_SQL
    assert "TARGET_SQL_NOT_READ_ONLY" in res.metadata.error_code
