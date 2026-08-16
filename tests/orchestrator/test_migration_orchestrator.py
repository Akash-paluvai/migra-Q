"""Tests for Phase 10.1 Generic Migration Orchestrator."""

from __future__ import annotations

import pytest

from backend.assurance.models import MigrationFinalStatus
from backend.orchestrator.models import PipelineRunRequest
from backend.orchestrator.service import MigrationOrchestrator


@pytest.fixture
def orchestrator():
    return MigrationOrchestrator()


def test_orchestrator_custom_query_execution(orchestrator):
    """Test dynamic execution of custom SQL query through MigrationOrchestrator."""
    custom_sql = """
    SELECT
        account_id,
        customer_id,
        balance
    FROM accounts
    WHERE balance > 2000;
    """.strip()

    req = PipelineRunRequest(
        source_sql=custom_sql,
        source_dialect="teradata",
        target_dialect="bigquery",
        dataset_id="customer_risk",
        mock_mode="DIRECT_PASS",
    )

    result = orchestrator.run(req)

    assert result.migration_id.startswith("MIG-")
    assert result.migration_record.source_dialect == "teradata"
    assert result.migration_record.target_dialect == "bigquery"
    assert result.assurance_report.score.evidence_score >= 50.0, (
        f"Evidence score {result.assurance_report.score.evidence_score} below minimum threshold"
    )
    assert result.assurance_report.lineage.is_complete is True


def test_orchestrator_flagship_mock_mode_execution(orchestrator):
    """Test orchestrator execution with mock mode boundary bug & repair."""
    flagship_sql = """
    SELECT
        c.customer_id,
        c.customer_segment,
        SUM(t.amount) AS total_amount,
        CASE
            WHEN t.amount > 500
            THEN 'HIGH_RISK'
            ELSE 'NORMAL'
        END AS risk_class
    FROM transactions AS t
    INNER JOIN customers AS c
        ON t.customer_id = c.customer_id
    WHERE t.status = 'COMPLETED'
    GROUP BY c.customer_id, c.customer_segment, t.amount;
    """.strip()

    req = PipelineRunRequest(
        source_sql=flagship_sql,
        source_dialect="teradata",
        target_dialect="bigquery",
        dataset_id="customer_risk",
        mock_mode="MOCK_BOUNDARY_BUG",
        migration_id="MIG-TEST-ORCH-001",
    )

    result = orchestrator.run(req)

    assert result.migration_id == "MIG-TEST-ORCH-001"
    assert result.migration_record.final_status == MigrationFinalStatus.VERIFIED
    assert result.assurance_report.score.evidence_score == 100.0
    assert result.assurance_report.gate_evaluation.all_passed is True
    assert result.assurance_report.lineage.verification_path.value == "REPAIRED_PASS"
