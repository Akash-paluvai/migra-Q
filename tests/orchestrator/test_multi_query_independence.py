"""Non-negotiable acceptance test for multi-query workflow independence."""

from __future__ import annotations

from backend.orchestrator.models import PipelineRunRequest
from backend.orchestrator.service import MigrationOrchestrator


def test_four_queries_produce_distinct_migration_artifacts():
    orchestrator = MigrationOrchestrator()

    sql_a = "SELECT customer_id, amount FROM transactions WHERE amount > 500"
    sql_b = "SELECT customer_id, amount FROM transactions WHERE amount > 700"
    sql_c = "SELECT COUNT(*) AS total_tx FROM transactions"
    sql_d = "SELECT customer_id, SUM(amount) AS total_amt FROM transactions GROUP BY customer_id"

    res_a = orchestrator.run(PipelineRunRequest(source_sql=sql_a, source_dialect="teradata", target_dialect="bigquery", dataset_id="customer_risk"))
    res_b = orchestrator.run(PipelineRunRequest(source_sql=sql_b, source_dialect="teradata", target_dialect="bigquery", dataset_id="customer_risk"))
    res_c = orchestrator.run(PipelineRunRequest(source_sql=sql_c, source_dialect="teradata", target_dialect="bigquery", dataset_id="customer_risk"))
    res_d = orchestrator.run(PipelineRunRequest(source_sql=sql_d, source_dialect="teradata", target_dialect="bigquery", dataset_id="customer_risk"))

    # 1. Distinct migration IDs
    ids = {res_a.migration_id, res_b.migration_id, res_c.migration_id, res_d.migration_id}
    assert len(ids) == 4, "All 4 query runs must yield unique migration IDs"

    # 2. Distinct source SQL hashes
    hashes = {
        res_a.migration_record.source_sql_hash,
        res_b.migration_record.source_sql_hash,
        res_c.migration_record.source_sql_hash,
        res_d.migration_record.source_sql_hash,
    }
    assert len(hashes) == 4, "All 4 query runs must yield unique source SQL hashes"

    # 3. Downstream assurance report uniqueness
    report_ids = {
        res_a.assurance_report.migration_id,
        res_b.assurance_report.migration_id,
        res_c.assurance_report.migration_id,
        res_d.assurance_report.migration_id,
    }
    assert len(report_ids) == 4, "All 4 query runs must yield unique assurance report migration IDs"
