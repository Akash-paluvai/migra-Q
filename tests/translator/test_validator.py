"""Unit tests for candidate target SQL safety and integrity validator."""


from backend.translator.models import (
    CandidateValidationStatus,
    ColumnSchemaDef,
    SchemaContext,
    TableSchema,
)
from backend.translator.validator import validate_candidate_sql


def test_validate_empty_sql():
    status, code, msg = validate_candidate_sql("")
    assert status == CandidateValidationStatus.INVALID_SYNTAX
    assert code == "EMPTY_SQL"


def test_validate_valid_select_query():
    sql = "SELECT customer_id, SUM(amount) FROM transactions GROUP BY customer_id;"
    status, code, msg = validate_candidate_sql(sql, target_dialect="bigquery")
    assert status == CandidateValidationStatus.VALID_SYNTAX
    assert msg == "Candidate SQL syntactically valid"
    assert code == ""


def test_validate_mutating_drop_table_rejected():
    sql = "DROP TABLE customers;"
    status, code, msg = validate_candidate_sql(sql, target_dialect="bigquery")
    assert status == CandidateValidationStatus.UNSAFE_SQL
    assert code == "TARGET_SQL_NOT_READ_ONLY"


def test_validate_mutating_insert_rejected():
    sql = "INSERT INTO customers (id) VALUES ('1');"
    status, code, msg = validate_candidate_sql(sql, target_dialect="bigquery")
    assert status == CandidateValidationStatus.UNSAFE_SQL
    assert code == "TARGET_SQL_NOT_READ_ONLY"


def test_validate_mutating_delete_rejected():
    sql = "DELETE FROM customers WHERE id = 1;"
    status, code, msg = validate_candidate_sql(sql, target_dialect="bigquery")
    assert status == CandidateValidationStatus.UNSAFE_SQL
    assert code == "TARGET_SQL_NOT_READ_ONLY"


def test_validate_unparseable_sql():
    sql = "SELECT FROM WHERE GROUP BY;"
    status, code, msg = validate_candidate_sql(sql, target_dialect="bigquery")
    assert status == CandidateValidationStatus.INVALID_SYNTAX
    assert code == "UNPARSEABLE_SQL"


def test_validate_schema_consistency_unknown_table():
    schema = SchemaContext(
        tables=[
            TableSchema(
                name="transactions",
                columns=[ColumnSchemaDef(name="amount", type="FLOAT")],
            )
        ]
    )
    sql = "SELECT * FROM non_existent_table;"
    status, code, msg = validate_candidate_sql(
        sql, target_dialect="bigquery", schema_context=schema
    )
    assert status == CandidateValidationStatus.SCHEMA_MISMATCH
    assert code == "UNKNOWN_TABLE"
    assert "non_existent_table" in msg


def test_validate_schema_consistency_unknown_column():
    schema = SchemaContext(
        tables=[
            TableSchema(
                name="transactions",
                columns=[ColumnSchemaDef(name="amount", type="FLOAT")],
            )
        ]
    )
    sql = "SELECT nonexistent_col FROM transactions;"
    status, code, msg = validate_candidate_sql(
        sql, target_dialect="bigquery", schema_context=schema
    )
    assert status == CandidateValidationStatus.SCHEMA_MISMATCH
    assert code == "UNKNOWN_COLUMN"
    assert "nonexistent_col" in msg
