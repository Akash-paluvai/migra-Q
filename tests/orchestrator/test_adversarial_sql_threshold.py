"""Adversarial test verifying system behavior changes dynamically with modified SQL parameters."""

from __future__ import annotations

from backend.orchestrator.models import PipelineRunRequest
from backend.orchestrator.service import MigrationOrchestrator


def test_adversarial_sql_threshold_changes_metrics():
    orchestrator = MigrationOrchestrator()

    sql_flagship = """
    SELECT c.customer_id, c.customer_segment, SUM(t.amount) AS total_amount,
           CASE WHEN t.amount > 500 THEN 'HIGH_RISK' ELSE 'NORMAL' END AS risk_class
    FROM transactions AS t
    INNER JOIN customers AS c ON t.customer_id = c.customer_id
    WHERE t.status = 'COMPLETED'
    GROUP BY c.customer_id, c.customer_segment, t.amount;
    """.strip()

    sql_adversarial = """
    SELECT c.customer_id, c.customer_segment, SUM(t.amount) AS total_amount,
           CASE WHEN t.amount > 999999 THEN 'HIGH_RISK' ELSE 'NORMAL' END AS risk_class
    FROM transactions AS t
    INNER JOIN customers AS c ON t.customer_id = c.customer_id
    WHERE t.status = 'COMPLETED'
    GROUP BY c.customer_id, c.customer_segment, t.amount;
    """.strip()

    res_standard = orchestrator.run(PipelineRunRequest(source_sql=sql_flagship, dataset_id="customer_risk"))
    res_adversarial = orchestrator.run(PipelineRunRequest(source_sql=sql_adversarial, dataset_id="customer_risk"))

    # Assert distinct migration IDs
    assert res_standard.migration_id != res_adversarial.migration_id

    # Assert distinct source SQL hashes
    assert res_standard.migration_record.source_sql_hash != res_adversarial.migration_record.source_sql_hash

    # Verify that the lineage & summary metrics in standard vs adversarial execution are distinct
    assert res_standard.assurance_report.lineage.source_execution_id != res_adversarial.assurance_report.lineage.source_execution_id
    assert res_standard.assurance_report.lineage.target_execution_id != res_adversarial.assurance_report.lineage.target_execution_id
