"""Phase 10.2 Integration Test — Custom User Query (enterprise_metrics) with Snowflake target dialect.

Validates that arbitrary user SQL is parsed, executed, translated, and assigned clean explicit lineage
without falling back to flagship SQL or expressions (customer_id, t.amount > 500).
"""

from __future__ import annotations

import hashlib

from backend.orchestrator.models import PipelineRunRequest
from backend.orchestrator.service import MigrationOrchestrator

ENTERPRISE_METRICS_SQL = """
SELECT
    department,
    COUNT(*) AS total_metrics,
    SUM(CASE WHEN gate_status = 'PASS' THEN 1 ELSE 0 END) AS pass_count,
    SUM(CASE WHEN gate_status = 'FAIL' THEN 1 ELSE 0 END) AS fail_count,
    ROUND(AVG(score), 2) AS avg_score,
    MAX(score) AS max_score,
    MIN(score) AS min_score
FROM enterprise_metrics
GROUP BY department
ORDER BY department;
""".strip()


def test_enterprise_metrics_migration_lineage_and_isolation():
    """Verify custom enterprise_metrics query run maintains strict lineage and zero flagship fallback."""
    orchestrator = MigrationOrchestrator()

    req = PipelineRunRequest(
        source_sql=ENTERPRISE_METRICS_SQL,
        source_dialect="oracle",
        target_dialect="snowflake",
        dataset_id="mixed_business_logic",
        mock_mode="DIRECT_PASS",
    )

    result = orchestrator.run(req)

    # 1. Root migration identity assertion
    assert result.migration_id.startswith("MIG-")
    rec = result.migration_record
    assert rec.migration_id == result.migration_id
    assert rec.target_dialect == "snowflake"
    assert rec.source_dialect == "oracle"
    assert rec.dataset_id == "mixed_business_logic"

    # 2. SHA256 Hash Invariant assertion
    expected_hash = hashlib.sha256(ENTERPRISE_METRICS_SQL.encode()).hexdigest()[:16]
    assert rec.source_sql_hash == expected_hash

    report = result.assurance_report
    assert report.migration_id == result.migration_id

    # 3. Translation artifact assertion
    trans_summary = report.translation_summary
    assert trans_summary is not None
    assert trans_summary.source_dialect == "oracle"
    assert trans_summary.target_dialect == "snowflake"
    assert trans_summary.source_sql_hash == expected_hash

    # 4. Zero flagship content assertion
    # Must NOT contain customer_id, transactions, customers, or t.amount > 500
    candidate_sql = trans_summary.candidate_sql or ""
    flagship_markers = ["customer_id", "customer_segment", "t.amount > 500", "t.amount >= 500"]
    for marker in flagship_markers:
        assert marker not in candidate_sql, f"Flagship string '{marker}' found in translated target SQL!"

    # 5. Audit Lineage boundary check
    lineage = report.lineage
    assert lineage.is_complete is True
    assert lineage.translation_id.startswith("trans-")
    assert len(lineage.source_execution_id) > 0, "source_execution_id must be set"
    assert len(lineage.target_execution_id) > 0, "target_execution_id must be set"
    assert len(lineage.validation_id) > 0, "validation_id must be set"
