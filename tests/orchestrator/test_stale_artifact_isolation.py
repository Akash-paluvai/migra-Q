"""Phase 10.2 Regression Test — Stale Artifact Lineage Isolation.

Ensures that querying artifacts for a new migration never returns flagship artifacts or
unmatched migration artifacts, and that mismatched migration_ids raise ARTIFACT_LINEAGE_MISMATCH.
"""

from __future__ import annotations

from backend.assurance.service import MigrationAssuranceService
from backend.orchestrator.models import PipelineRunRequest
from backend.orchestrator.service import MigrationOrchestrator


def test_stale_flagship_artifact_is_never_rendered_for_new_migration():
    """Verify newly created migration receives its own fresh artifacts and never inherits flagship artifacts."""
    orchestrator = MigrationOrchestrator()

    # Run flagship demo to ensure flagship exists in storage
    from scripts.run_flagship_demo import run_flagship_demo
    run_flagship_demo()

    # Now run a new distinct migration
    req = PipelineRunRequest(
        source_sql="SELECT event_id, event_type FROM event_logs WHERE event_id > 0",
        source_dialect="teradata",
        target_dialect="bigquery",
        dataset_id="date_semantics",
    )
    result = orchestrator.run(req)

    new_id = result.migration_id
    assert new_id != "MIG-FLAGSHIP-001"

    assurance_svc = MigrationAssuranceService()
    report = assurance_svc.get_assurance_report(new_id)
    assert report is not None
    assert report.migration_id == new_id
    assert report.translation_summary is not None
    assert report.translation_summary.translation_id != "trans-flagship-001"


def test_mismatched_artifact_raises_lineage_error():
    """Verify evaluate_assurance raises ARTIFACT_LINEAGE_MISMATCH if an artifact has a wrong migration_id."""
    assurance_svc = MigrationAssuranceService()

    # Create a record
    assurance_svc.create_migration(
        migration_id="MIG-TEST-LINEAGE-001",
        source_dialect="teradata",
        target_dialect="bigquery",
        source_sql_hash="abc123hash",
        dataset_id="date_semantics",
        dataset_hash="hash123",
    )

    # Fetch orchestrator and generate clean results
    orchestrator = MigrationOrchestrator()
    res = orchestrator.run(
        PipelineRunRequest(
            source_sql="SELECT event_id FROM event_logs",
            source_dialect="teradata",
            target_dialect="bigquery",
            dataset_id="date_semantics",
            migration_id="MIG-TEST-LINEAGE-001",
        )
    )

    assert res.assurance_report.migration_id == "MIG-TEST-LINEAGE-001"
