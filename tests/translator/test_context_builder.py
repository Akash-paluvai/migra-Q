"""Unit tests for context builder and Phase 1 AST integration."""


from backend.translator.context_builder import build_translation_context
from backend.translator.models import (
    ColumnSchemaDef,
    SchemaContext,
    TableSchema,
    TranslationRequest,
)


def test_build_translation_context_basic():
    req = TranslationRequest(
        source_sql="SELECT customer_id, amount FROM transactions WHERE amount > 500;",
        source_dialect="teradata",
        target_dialect="bigquery",
    )
    ctx = build_translation_context(req)

    assert ctx.source_sql == req.source_sql
    assert ctx.source_dialect == "teradata"
    assert ctx.target_dialect == "bigquery"
    assert ctx.normalized_sql is not None
    assert len(ctx.tables) > 0
    assert ctx.context_hash != ""


def test_build_translation_context_passes_source_dialect():
    req = TranslationRequest(
        source_sql="SELECT TOP 10 customer_id FROM transactions;",
        source_dialect="teradata",
        target_dialect="bigquery",
    )
    ctx = build_translation_context(req)
    # Teradata TOP 10 syntax recognized via dialect pass-through
    assert ctx.source_dialect == "teradata"


def test_build_translation_context_with_schema():
    schema = SchemaContext(
        tables=[
            TableSchema(
                name="transactions",
                columns=[
                    ColumnSchemaDef(name="customer_id", type="STRING"),
                    ColumnSchemaDef(name="amount", type="DECIMAL(18,2)"),
                ],
            )
        ]
    )
    req = TranslationRequest(
        source_sql="SELECT customer_id FROM transactions;",
        source_dialect="teradata",
        target_dialect="bigquery",
        schema=schema,
    )
    ctx = build_translation_context(req)
    assert ctx.schema_context is not None
    assert "transactions" in ctx.schema_context.get_table_names()


def test_translation_context_hash_reproducibility():
    req1 = TranslationRequest(
        source_sql="SELECT * FROM customers;",
        source_dialect="teradata",
        target_dialect="bigquery",
    )
    req2 = TranslationRequest(
        source_sql="SELECT * FROM customers;",
        source_dialect="teradata",
        target_dialect="bigquery",
    )
    ctx1 = build_translation_context(req1)
    ctx2 = build_translation_context(req2)
    assert ctx1.context_hash == ctx2.context_hash


def test_translation_context_hash_changes_with_dialect():
    req1 = TranslationRequest(
        source_sql="SELECT * FROM customers;",
        source_dialect="teradata",
        target_dialect="bigquery",
    )
    req2 = TranslationRequest(
        source_sql="SELECT * FROM customers;",
        source_dialect="oracle",
        target_dialect="bigquery",
    )
    ctx1 = build_translation_context(req1)
    ctx2 = build_translation_context(req2)
    assert ctx1.context_hash != ctx2.context_hash
