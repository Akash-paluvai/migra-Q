"""Unit tests for FastAPI validation endpoints."""

import pytest
from fastapi.testclient import TestClient

from backend.execution.models import ExecutionRequest
from backend.execution.service import ExecutionService
from backend.main import app
from backend.validation.service import ValidationService

client = TestClient(app)


@pytest.fixture
def test_dataset_id():
    import argparse

    from backend.lab.cli import cmd_generate

    out_dir = "datasets/generated/test_exec"
    cmd_generate(argparse.Namespace(profile="test", seed=42, out_dir=out_dir, csv=False))
    return "test_exec"


def test_api_create_validation_success(test_dataset_id):
    sql = "SELECT customer_id, first_name FROM customers LIMIT 5"
    e1 = ExecutionService.execute(ExecutionRequest(sql=sql, dataset_id=test_dataset_id))
    e2 = ExecutionService.execute(ExecutionRequest(sql=sql, dataset_id=test_dataset_id))

    payload = {
        "source_execution_id": e1.execution_id,
        "target_execution_id": e2.execution_id,
    }

    resp = client.post("/api/v1/validations", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["overall_status"] == "PASS"
    assert "validation_id" in data


def test_api_get_validation_success(test_dataset_id):
    sql = "SELECT customer_id FROM customers LIMIT 3"
    e1 = ExecutionService.execute(ExecutionRequest(sql=sql, dataset_id=test_dataset_id))
    e2 = ExecutionService.execute(ExecutionRequest(sql=sql, dataset_id=test_dataset_id))

    report = ValidationService.validate_executions(e1.execution_id, e2.execution_id)

    resp = client.get(f"/api/v1/validations/{report.validation_id}")
    assert resp.status_code == 200
    assert resp.json()["validation_id"] == report.validation_id


def test_api_get_validation_not_found():
    resp = client.get("/api/v1/validations/non_existent_val_id_999")
    assert resp.status_code == 404


def test_api_create_validation_invalid_execution_id():
    payload = {
        "source_execution_id": "invalid_src",
        "target_execution_id": "invalid_tgt",
    }
    resp = client.post("/api/v1/validations", json=payload)
    assert resp.status_code == 400


def test_api_create_validation_with_custom_config(test_dataset_id):
    sql = "SELECT customer_id FROM customers LIMIT 2"
    e1 = ExecutionService.execute(ExecutionRequest(sql=sql, dataset_id=test_dataset_id))
    e2 = ExecutionService.execute(ExecutionRequest(sql=sql, dataset_id=test_dataset_id))

    payload = {
        "source_execution_id": e1.execution_id,
        "target_execution_id": e2.execution_id,
        "config": {
            "comparison_key": ["customer_id"],
            "numeric_absolute_tolerance": 1e-4,
        },
    }

    resp = client.post("/api/v1/validations", json=payload)
    assert resp.status_code == 200
    assert resp.json()["overall_status"] == "PASS"
