"""Integration Test for Netezza to Snowflake Migration.

Validates that Netezza SQL is parsed correctly using the Postgres-derived 
compatibility layer, and the pipeline executes successfully against the 
date_semantics dataset.
"""

from __future__ import annotations

import hashlib

from backend.analyzer.parser import parse_sql
from backend.orchestrator.models import PipelineRunRequest
from backend.orchestrator.service import MigrationOrchestrator
from backend.assurance.models import MigrationFinalStatus

NETEZZA_DATE_SQL = """
SELECT
    event_id,
    user_id,
    event_date,
    event_time,
    DATE_TRUNC('month', event_date) AS event_month,
    DATE_TRUNC('day', event_time) AS event_day,
    EXTRACT(YEAR FROM event_date) AS event_year,
    EXTRACT(MONTH FROM event_date) AS event_month_num,
    EXTRACT(DAY FROM event_date) AS event_day_num
FROM event_logs
WHERE event_date >= DATE '2026-01-01'
  AND event_date < DATE '2027-01-01'
ORDER BY event_date, event_id;
""".strip()

def test_netezza_parser_recognition():
    """Verify that the parser properly recognizes the netezza dialect and parses valid SQL."""
    # This should NOT raise "Unknown dialect 'netezza'"
    parsed = parse_sql(NETEZZA_DATE_SQL, dialect="netezza")
    assert parsed is not None
    assert "event_logs" in parsed.sql()

def test_netezza_to_snowflake_migration():
    """Verify that a full Netezza to Snowflake pipeline runs successfully."""
    orchestrator = MigrationOrchestrator()

    req = PipelineRunRequest(
        source_sql=NETEZZA_DATE_SQL,
        source_dialect="netezza",
        target_dialect="snowflake",
        dataset_id="date_semantics",
        mock_mode="DIRECT_PASS",
        migration_id="MIG-NETEZZA-001"
    )

    result = orchestrator.run(req)

    # 1. Identity assertion
    rec = result.migration_record
    assert rec.source_dialect == "netezza"
    assert rec.target_dialect == "snowflake"
    assert rec.dataset_id == "date_semantics"

    # 2. Assurance assertion
    report = result.assurance_report
    assert report.final_status == MigrationFinalStatus.VERIFIED
    
    # Check that translation summary shows correct dialects
    trans_summary = report.translation_summary
    assert trans_summary is not None
    assert trans_summary.source_dialect == "netezza"
    assert trans_summary.target_dialect == "snowflake"
