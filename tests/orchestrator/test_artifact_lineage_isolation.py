"""Unit tests verifying complete artifact lineage isolation between migration runs."""

from __future__ import annotations

from backend.orchestrator.models import PipelineRunRequest
from backend.orchestrator.service import MigrationOrchestrator


def test_concurrent_runs_never_share_artifact_ids():
    orchestrator = MigrationOrchestrator()

    sql_1 = "SELECT customer_id, balance FROM accounts WHERE balance > 100"
    sql_2 = "SELECT customer_id, balance FROM accounts WHERE balance > 200"

    res_1 = orchestrator.run(PipelineRunRequest(source_sql=sql_1, dataset_id="customer_risk"))
    res_2 = orchestrator.run(PipelineRunRequest(source_sql=sql_2, dataset_id="customer_risk"))

    assert res_1.migration_id != res_2.migration_id
    assert res_1.assurance_report.migration_id != res_2.assurance_report.migration_id
    assert res_1.assurance_report.lineage.source_execution_id != res_2.assurance_report.lineage.source_execution_id
    assert res_1.assurance_report.lineage.target_execution_id != res_2.assurance_report.lineage.target_execution_id
    assert res_1.assurance_report.lineage.validation_id != res_2.assurance_report.lineage.validation_id
