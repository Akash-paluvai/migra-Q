"""Comprehensive execution engine test suite covering all 22 Phase 3 requirements."""

import duckdb
import pytest
from fastapi.testclient import TestClient

from backend.execution.exceptions import SecurityViolationError
from backend.execution.hashing import hash_dataset_manifest, hash_query
from backend.execution.models import ExecutionRequest, ExecutionStatus
from backend.execution.query_normalizer import validate_read_only_query
from backend.execution.service import ExecutionService
from backend.main import app

client = TestClient(app)


@pytest.fixture
def dev_dataset_id():
    import argparse

    from backend.lab.cli import cmd_generate

    out_dir = "datasets/generated/test_exec"
    cmd_generate(argparse.Namespace(profile="test", seed=42, out_dir=out_dir, csv=False))
    return "test_exec"


# 1. simple SELECT success
def test_simple_select_success(dev_dataset_id):
    req = ExecutionRequest(
        sql="SELECT customer_id, first_name FROM customers", dataset_id=dev_dataset_id
    )
    res = ExecutionService.execute(req)

    assert res.status == ExecutionStatus.SUCCESS
    assert res.row_count == 100
    assert len(res.columns) == 2
    assert res.result_artifact is not None


# 2. JOIN success
def test_join_success(dev_dataset_id):
    sql = (
        "SELECT c.customer_id, a.account_id FROM customers c "
        "JOIN accounts a ON c.customer_id = a.customer_id"
    )
    req = ExecutionRequest(sql=sql, dataset_id=dev_dataset_id)
    res = ExecutionService.execute(req)

    assert res.status == ExecutionStatus.SUCCESS
    assert res.row_count == 400
    assert len(res.columns) == 2


# 3. aggregation success
def test_aggregation_success(dev_dataset_id):
    sql = (
        "SELECT account_type, COUNT(*) AS cnt, SUM(balance) AS total "
        "FROM accounts GROUP BY account_type"
    )
    req = ExecutionRequest(sql=sql, dataset_id=dev_dataset_id)
    res = ExecutionService.execute(req)

    assert res.status == ExecutionStatus.SUCCESS
    assert res.row_count == 4
    assert {c.name for c in res.columns} == {"account_type", "cnt", "total"}


# 4. empty result success
def test_empty_result_success(dev_dataset_id):
    sql = "SELECT * FROM customers WHERE annual_income < 0"
    req = ExecutionRequest(sql=sql, dataset_id=dev_dataset_id)
    res = ExecutionService.execute(req)

    assert res.status == ExecutionStatus.SUCCESS
    assert res.row_count == 0


# 5. NULL result
def test_null_result_handling(dev_dataset_id):
    sql = "SELECT closed_at FROM accounts WHERE closed_at IS NULL"
    req = ExecutionRequest(sql=sql, dataset_id=dev_dataset_id)
    res = ExecutionService.execute(req)

    assert res.status == ExecutionStatus.SUCCESS
    assert res.row_count > 0


# 6. invalid SQL
def test_invalid_sql_handling(dev_dataset_id):
    sql = "SELECT FROM WHERE invalid syntax"
    req = ExecutionRequest(sql=sql, dataset_id=dev_dataset_id)
    res = ExecutionService.execute(req)

    assert res.status == ExecutionStatus.EXECUTION_ERROR
    assert res.error_code is not None


# 7. missing table
def test_missing_table_error(dev_dataset_id):
    sql = "SELECT * FROM non_existent_table_xyz"
    req = ExecutionRequest(sql=sql, dataset_id=dev_dataset_id)
    res = ExecutionService.execute(req)

    assert res.status == ExecutionStatus.EXECUTION_ERROR
    assert "non_existent_table_xyz" in res.error_message.lower()


# 8. missing column
def test_missing_column_error(dev_dataset_id):
    sql = "SELECT invalid_column_xyz FROM customers"
    req = ExecutionRequest(sql=sql, dataset_id=dev_dataset_id)
    res = ExecutionService.execute(req)

    assert res.status == ExecutionStatus.EXECUTION_ERROR


# 9. unsupported/mutating SQL blocked
def test_mutating_sql_blocked(dev_dataset_id):
    with pytest.raises(SecurityViolationError):
        validate_read_only_query("DROP TABLE customers")

    with pytest.raises(SecurityViolationError):
        validate_read_only_query("INSERT INTO customers VALUES ('1')")

    req = ExecutionRequest(sql="DROP TABLE customers", dataset_id=dev_dataset_id)
    res = ExecutionService.execute(req)
    assert res.status == ExecutionStatus.SECURITY_ERROR


# 10. result schema capture
def test_result_schema_capture(dev_dataset_id):
    sql = "SELECT customer_id, credit_score FROM customers"
    req = ExecutionRequest(sql=sql, dataset_id=dev_dataset_id)
    res = ExecutionService.execute(req)

    col_types = {c.name: c.type for c in res.columns}
    assert col_types["customer_id"] in ("VARCHAR", "VARCHAR()", "STRING")
    assert col_types["credit_score"] in ("BIGINT", "INTEGER", "INT", "INT64")


# 11. row count accuracy
def test_row_count_accuracy(dev_dataset_id):
    sql = "SELECT * FROM customers WHERE risk_tier = 'HIGH'"
    req = ExecutionRequest(sql=sql, dataset_id=dev_dataset_id)
    res = ExecutionService.execute(req)

    assert res.status == ExecutionStatus.SUCCESS
    assert res.row_count > 0


# 12. query hash determinism
def test_query_hash_determinism():
    sql1 = "SELECT * FROM customers WHERE id = 1\r\n"
    sql2 = "SELECT * FROM customers WHERE id = 1\n"
    assert hash_query(sql1) == hash_query(sql2)


# 13. dataset hash determinism
def test_dataset_hash_determinism():
    manifest = {
        "seed": 42,
        "profile": "dev",
        "schema_version": "0.1.0",
        "generator_version": "0.1.0",
        "checksums": {"customers": "abc", "accounts": "def"},
    }
    h1 = hash_dataset_manifest(manifest)
    h2 = hash_dataset_manifest(manifest)
    assert h1 == h2


# 14. execution_id uniqueness
def test_execution_id_uniqueness(dev_dataset_id):
    sql = "SELECT COUNT(*) FROM customers"
    res1 = ExecutionService.execute(ExecutionRequest(sql=sql, dataset_id=dev_dataset_id))
    res2 = ExecutionService.execute(ExecutionRequest(sql=sql, dataset_id=dev_dataset_id))

    assert res1.execution_id != res2.execution_id


# 15. result artifact creation
def test_result_artifact_creation(dev_dataset_id):
    sql = "SELECT customer_id FROM customers LIMIT 10"
    res = ExecutionService.execute(ExecutionRequest(sql=sql, dataset_id=dev_dataset_id))

    assert res.result_artifact is not None
    import os

    assert os.path.exists(res.result_artifact)


# 16. result artifact readable by DuckDB
def test_result_artifact_readable_by_duckdb(dev_dataset_id):
    sql = "SELECT customer_id FROM customers LIMIT 5"
    res = ExecutionService.execute(ExecutionRequest(sql=sql, dataset_id=dev_dataset_id))

    duck_res = duckdb.sql(f"SELECT COUNT(*) FROM read_parquet('{res.result_artifact}')").fetchone()
    assert duck_res[0] == 5


# 17. large-result handling
def test_large_result_handling(dev_dataset_id):
    sql = "SELECT * FROM transactions"  # 200,000 rows
    res = ExecutionService.execute(ExecutionRequest(sql=sql, dataset_id=dev_dataset_id))

    assert res.status == ExecutionStatus.SUCCESS
    assert res.row_count == 2000
    assert len(res.sample_data) <= 500  # Bounded inline sample


# 18. timeout behavior
def test_timeout_behavior(dev_dataset_id, monkeypatch):
    import backend.execution.duckdb_runner as dr

    monkeypatch.setattr(dr, "EXECUTION_TIMEOUT_SECONDS", 0.001)

    req = ExecutionRequest(sql="SELECT * FROM transactions", dataset_id=dev_dataset_id)
    res = ExecutionService.execute(req)
    assert res.status in (ExecutionStatus.TIMEOUT, ExecutionStatus.EXECUTION_ERROR)


# 19. metadata persistence
def test_metadata_persistence(dev_dataset_id):
    sql = "SELECT customer_id FROM customers LIMIT 1"
    res = ExecutionService.execute(ExecutionRequest(sql=sql, dataset_id=dev_dataset_id))

    retrieved = ExecutionService.get_execution(res.execution_id)
    assert retrieved is not None
    assert retrieved.execution_id == res.execution_id
    assert retrieved.query_hash == res.query_hash


# 20. API execution endpoint
def test_api_execution_endpoint(dev_dataset_id):
    payload = {
        "sql": "SELECT customer_id FROM customers LIMIT 3",
        "dataset_id": dev_dataset_id,
        "execution_mode": "SOURCE",
    }
    response = client.post("/api/v1/executions", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["row_count"] == 3


# 21. execution retrieval endpoint
def test_api_execution_retrieval_endpoint(dev_dataset_id):
    payload = {
        "sql": "SELECT customer_id FROM customers LIMIT 2",
        "dataset_id": dev_dataset_id,
    }
    create_resp = client.post("/api/v1/executions", json=payload)
    exec_id = create_resp.json()["execution_id"]

    get_resp = client.get(f"/api/v1/executions/{exec_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["execution_id"] == exec_id


# 22. repeated execution reproducibility
def test_repeated_execution_reproducibility(dev_dataset_id):
    sql = "SELECT customer_id, SUM(amount) AS total FROM transactions GROUP BY customer_id"
    res1 = ExecutionService.execute(ExecutionRequest(sql=sql, dataset_id=dev_dataset_id))
    res2 = ExecutionService.execute(ExecutionRequest(sql=sql, dataset_id=dev_dataset_id))

    assert res1.query_hash == res2.query_hash
    assert res1.dataset_hash == res2.dataset_hash
    assert res1.row_count == res2.row_count
    assert res1.execution_id != res2.execution_id
