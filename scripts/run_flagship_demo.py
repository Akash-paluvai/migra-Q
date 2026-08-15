"""Flagship End-to-End Demo Script for MIGRA-Q.

Executes complete pipeline:
customer_risk_source.sql
        ↓
Phase 6 translation (candidate with >= 500)
        ↓
Phase 3 execution (DuckDB Sandbox)
        ↓
Phase 4 validation
        ↓
Phase 5: BOUNDARY_CONDITION (profile-derived affected rows)
        ↓
Phase 7: repair proposal (> 500)
        ↓
Phase 8: re-execute
        ↓
Phase 4: 0 affected
        ↓
Phase 5: 0 new discrepancies
        ↓
VERIFIED

Preserves and prints complete audit chain:
Translation ID -> Execution ID -> Validation ID -> Diagnosis ID -> Repair ID -> Verification ID
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.config import settings  # noqa: E402

settings.APP_ENV = "test"
settings.PERSISTENCE_MODE = "memory"

from backend.analyzer.service import AnalyzerService  # noqa: E402
from backend.diagnosis.orchestrator import DiagnosisOrchestrator  # noqa: E402
from backend.diagnosis_ai.service import DiagnosisAIService  # noqa: E402
from backend.execution.models import ExecutionMode, ExecutionRequest  # noqa: E402
from backend.execution.service import ExecutionService  # noqa: E402
from backend.lab.config import GENERATOR_VERSION, SCHEMA_VERSION  # noqa: E402
from backend.lab.exporters.parquet import export_to_parquet  # noqa: E402
from backend.lab.models import ALL_SCHEMAS, DatasetManifest  # noqa: E402
from backend.lab.scenarios.registry import get_scenario  # noqa: E402
from backend.assurance.service import MigrationAssuranceService  # noqa: E402
from backend.repair_verification.service import RepairVerificationService  # noqa: E402
from backend.translator.models import TranslationRequest  # noqa: E402
from backend.translator.service import TranslationService  # noqa: E402
from backend.validation.service import ValidationService  # noqa: E402


from backend.assurance.cli import format_report  # noqa: E402


def _print_assurance_report(report):
    """Print the final assurance report in the user-facing format."""
    print("")
    print(format_report(report))
    print("")



def run_flagship_demo(flagship_id: str = "MIG-FLAGSHIP-001"):
    print("=" * 85)
    print("MIGRA-Q FLAGSHIP END-TO-END DEMO & FULL AUDIT LINEAGE PROOF")
    print("=" * 85)

    dataset_dir = PROJECT_ROOT / "datasets" / "generated" / "customer_risk"
    profile_name = "test" if "--test-profile" in sys.argv else "dev"
    print(f"\n[STEP 0] Generating synthetic dataset 'customer_risk' (BOUNDARY_REFUND_001, profile={profile_name}) at:\n  {dataset_dir}")
    # Scenario boundary_rows will be set in metadata after generation.
    scen = get_scenario("BOUNDARY_REFUND_001")
    dfs = scen.generate(seed=42, profile_name=profile_name)
    file_names, checksums = export_to_parquet(dfs, dataset_dir)
    row_counts = {name: len(df) for name, df in dfs.items()}

    manifest = DatasetManifest(
        dataset_id="customer_risk",
        generator_version=GENERATOR_VERSION,
        schema_version=SCHEMA_VERSION,
        seed=42,
        profile=profile_name,
        generation_timestamp=datetime.now(timezone.utc).isoformat(),
        row_counts=row_counts,
        table_schemas=ALL_SCHEMAS,
        scenario_ids=["BOUNDARY_REFUND_001"],
        file_names=file_names,
        checksums=checksums,
    )
    manifest_path = dataset_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(manifest.model_dump_json(indent=2))

    boundary_rows = scen.metadata.scenario_params.get("boundary_rows", 0)
    print(f"  -> Generated {len(dfs)} tables: {list(file_names.keys())}")
    print(f"  -> Boundary-affected rows (profile={profile_name}): {boundary_rows:,}")
    print(f"  -> Manifest created: {manifest_path}")

    # Flagship Source SQL
    source_sql = """
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

    # Execute flagship demo using MigrationOrchestrator
    from backend.orchestrator import MigrationOrchestrator, PipelineRunRequest

    orchestrator = MigrationOrchestrator()
    result = orchestrator.run(
        PipelineRunRequest(
            source_sql=source_sql,
            source_dialect="teradata",
            target_dialect="bigquery",
            dataset_id="customer_risk",
            profile=profile_name,
            mock_mode="MOCK_BOUNDARY_BUG",
            migration_id=flagship_id,
        )
    )

    # Print the final assurance report
    _print_assurance_report(result.assurance_report)


if __name__ == "__main__":
    run_flagship_demo()

