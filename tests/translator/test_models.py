"""Unit tests for Phase 6 Translation Engine domain & schema models."""


from backend.translator.models import (
    CandidateValidationStatus,
    ColumnSchemaDef,
    SchemaContext,
    StructuredRule,
    TableSchema,
    TranslationMetadata,
    TranslationRequest,
    TranslationResponse,
    TranslationResult,
    TranslationStatus,
)


def test_column_schema_def():
    col = ColumnSchemaDef(name="customer_id", type="STRING")
    assert col.name == "customer_id"
    assert col.type == "STRING"


def test_table_schema_and_context():
    col1 = ColumnSchemaDef(name="customer_id", type="STRING")
    col2 = ColumnSchemaDef(name="amount", type="DECIMAL(18,2)")
    t = TableSchema(name="transactions", columns=[col1, col2])
    ctx = SchemaContext(tables=[t])

    assert "transactions" in ctx.get_table_names()
    assert "customer_id" in ctx.get_column_names("transactions")
    assert "amount" in ctx.get_column_names("transactions")
    assert "nonexistent" not in ctx.get_column_names("transactions")


def test_translation_request_model():
    req = TranslationRequest(
        source_sql="SELECT 1;",
        source_dialect="teradata",
        target_dialect="bigquery",
    )
    assert req.source_sql == "SELECT 1;"
    assert req.source_dialect == "teradata"
    assert req.target_dialect == "bigquery"
    assert req.schema_context is None


def test_translation_response_structured_rule():
    rule = StructuredRule(
        source_path="business_rules[0]",
        source_expression="t.amount > 500",
        target_expression="t.amount > 500",
        rule_type="comparison",
    )
    resp = TranslationResponse(
        target_sql="SELECT * FROM t WHERE amount > 500;",
        assumptions=["Standard BigQuery syntax"],
        potential_risks=["Check float precision"],
        translated_rules=[rule],
    )
    assert len(resp.translated_rules) == 1
    assert resp.translated_rules[0].source_expression == "t.amount > 500"
    # Ensure NO equivalence boolean field exists!
    assert not hasattr(resp, "equivalence")
    assert not hasattr(resp, "is_equivalent")


def test_candidate_validation_status_enum():
    assert CandidateValidationStatus.VALID_SYNTAX.value == "VALID_SYNTAX"
    assert CandidateValidationStatus.INVALID_SYNTAX.value == "INVALID_SYNTAX"
    assert CandidateValidationStatus.UNSAFE_SQL.value == "UNSAFE_SQL"
    assert CandidateValidationStatus.SCHEMA_MISMATCH.value == "SCHEMA_MISMATCH"


def test_translation_status_enum():
    assert TranslationStatus.SUCCESS.value == "SUCCESS"
    assert TranslationStatus.FAILED.value == "FAILED"
    assert TranslationStatus.REJECTED.value == "REJECTED"
    assert TranslationStatus.INVALID_OUTPUT.value == "INVALID_OUTPUT"
    assert TranslationStatus.UNSUPPORTED_DIALECT.value == "UNSUPPORTED_DIALECT"
    assert TranslationStatus.TIMEOUT.value == "TIMEOUT"
    assert TranslationStatus.PROVIDER_ERROR.value == "PROVIDER_ERROR"


def test_translation_metadata_hash_fields():
    meta = TranslationMetadata(
        translation_id="trans-123",
        request_id="req-123",
        provider="mock",
        model="mock-model",
        source_dialect="teradata",
        target_dialect="bigquery",
        source_sql_hash="a1b2c3d4",
        translation_context_hash="e5f6g7h8",
        prompt_hash="i9j0k1l2",
        created_at="2026-08-15T00:00:00Z",
    )
    assert meta.translation_id == "trans-123"
    assert meta.source_sql_hash == "a1b2c3d4"
    assert meta.translation_context_hash == "e5f6g7h8"
    assert meta.prompt_hash == "i9j0k1l2"


def test_translation_result_container():
    meta = TranslationMetadata(
        translation_id="trans-123",
        request_id="req-123",
        provider="mock",
        model="mock-model",
        source_dialect="teradata",
        target_dialect="bigquery",
        source_sql_hash="a1b2c3d4",
        translation_context_hash="e5f6g7h8",
        prompt_hash="i9j0k1l2",
        created_at="2026-08-15T00:00:00Z",
    )
    res = TranslationResult(
        metadata=meta,
        status=TranslationStatus.SUCCESS,
        candidate_validation_status=CandidateValidationStatus.VALID_SYNTAX,
        validation_summary="Candidate SQL syntactically valid",
    )
    assert res.status == TranslationStatus.SUCCESS
    assert res.candidate_validation_status == CandidateValidationStatus.VALID_SYNTAX
