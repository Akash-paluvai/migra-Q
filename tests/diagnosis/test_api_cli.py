"""Unit tests for Phase 5 API endpoints and CLI commands."""

import pytest
from fastapi.testclient import TestClient

from backend.diagnosis.cli import main as cli_main
from backend.diagnosis.helpers import format_discrepancy_summary
from backend.main import app

client = TestClient(app)


def test_format_discrepancy_summary_formatting():
    report_dict = {
        "diagnosis_id": "diag-101",
        "validation_id": "val-101",
        "classifier_version": "0.1.0",
        "discrepancies": [
            {
                "discrepancy_id": "D-001",
                "category": "BOUNDARY_CONDITION",
                "severity": "HIGH",
                "classification_confidence": 1.0,
                "classification_method": "COMBINED_DETERMINISTIC",
                "source_expression": "refund_amount > 500",
                "target_expression": "refund_amount >= 500",
                "analysis_path": "business_rules[0].condition.operator",
                "affected_row_count": 229,
                "evidence": [{"detail": "Boundary value: 500.00"}],
                "classification_reason": "Operator changed > to >=",
            }
        ],
    }
    fmt = format_discrepancy_summary(report_dict)
    assert "MIGRA-Q DISCREPANCY ANALYSIS" in fmt
    assert "D-001" in fmt
    assert "BOUNDARY_CONDITION" in fmt
    assert "refund_amount > 500" in fmt
    assert "229 affected rows" in fmt


def test_api_diagnose_not_found():
    res = client.post("/api/v1/diagnoses", json={"validation_id": "non-existent-val-id"})
    assert res.status_code == 404


def test_api_get_diagnosis_not_found():
    res = client.get("/api/v1/diagnoses/non-existent-diag-id")
    assert res.status_code == 404


def test_cli_help(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["cli.py", "--help"])
    with pytest.raises(SystemExit):
        cli_main()
    captured = capsys.readouterr()
    assert "MIGRA-Q Discrepancy Classification CLI" in captured.out
