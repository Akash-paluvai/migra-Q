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



def run_flagship_demo():
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

    print("\n" + "-" * 85)
    print("[PHASE 1 & 6] SOURCE SQL + AI TRANSLATION ENGINE")
    print("-" * 85)
    print(f"Source SQL (Teradata baseline):\n{source_sql}\n")

    trans_req = TranslationRequest(
        source_sql=source_sql,
        source_dialect="teradata",
        target_dialect="bigquery",
        dataset_id="customer_risk",
    )
    trans_res = TranslationService.translate(trans_req, mock_mode="MOCK_BOUNDARY_BUG")
    translation_id = trans_res.metadata.translation_id
    candidate_sql = trans_res.response.target_sql if trans_res.response else ""

    print(f"-> Translation ID: {translation_id}")
    print(f"-> Migration Candidate SQL (BigQuery with '>=' boundary flaw):\n{candidate_sql}\n")

    print("-" * 85)
    print("[PHASE 3] DUCKDB EXECUTION SANDBOX")
    print("-" * 85)
    src_exec = ExecutionService.execute(
        ExecutionRequest(
            sql=source_sql,
            dialect="teradata",
            dataset_id="customer_risk",
            execution_mode=ExecutionMode.SOURCE,
        )
    )
    source_execution_id = src_exec.execution_id
    print(f"-> Source Execution ID:           {source_execution_id}")
    print(f"   Status: {src_exec.status.value:<10} | Rows: {src_exec.row_count:,} | Dataset Hash: {src_exec.dataset_hash[:16]}...")

    tgt_exec = ExecutionService.execute(
        ExecutionRequest(
            sql=candidate_sql,
            dialect="bigquery",
            dataset_id="customer_risk",
            execution_mode=ExecutionMode.TARGET,
        )
    )
    target_execution_id = tgt_exec.execution_id
    print(f"-> Target Candidate Execution ID: {target_execution_id}")
    print(f"   Status: {tgt_exec.status.value:<10} | Rows: {tgt_exec.row_count:,} | Dataset Hash: {tgt_exec.dataset_hash[:16]}...\n")

    print("-" * 85)
    print("[PHASE 4] MULTI-LAYER SEMANTIC VALIDATION ENGINE")
    print("-" * 85)
    val_report = ValidationService.validate_executions(
        source_execution_id=source_execution_id,
        target_execution_id=target_execution_id,
    )
    validation_id = val_report.validation_id
    print(f"-> Validation ID: {validation_id}")
    print(f"-> Overall Status: {val_report.overall_status}")
    for check in val_report.checks:
        print(f"   Check: {check.check_name:<25} Status: {check.status:<8} Mismatches: {check.mismatch_count}")

    print("\n" + "-" * 85)
    print("[PHASE 5] DISCREPANCY CLASSIFICATION & EVIDENCE CONSOLIDATION")
    print("-" * 85)
    src_ana = AnalyzerService.analyze(source_sql)
    tgt_ana = AnalyzerService.analyze(candidate_sql)
    orchestrator = DiagnosisOrchestrator()
    disc_report = orchestrator.diagnose(
        report=val_report,
        source_analysis=src_ana,
        target_analysis=tgt_ana,
        total_output_rows=src_exec.row_count,
    )
    diagnosis_id = disc_report.diagnosis_id
    print(f"-> Diagnosis ID: {diagnosis_id}")
    print(f"-> Total Discrepancies Classified: {len(disc_report.discrepancies)}")
    for d in disc_report.discrepancies:
        print(f"   ID: {d.discrepancy_id} | Category: {d.category.value:<20} | Affected Rows: {d.affected_row_count:,} | Severity: {d.severity.value}")
        print(f"   Reason: {d.classification_reason}")

    diag_rec = disc_report.discrepancies[0] if disc_report.discrepancies else None
    targeted_discrepancy_id = diag_rec.discrepancy_id if diag_rec else "D-001"

    print("\n" + "-" * 85)
    print("[PHASE 7] AI-GROUNDED DIAGNOSIS & REPAIR PROPOSAL ENGINE")
    print("-" * 85)
    actual_affected_rows = diag_rec.affected_row_count if diag_rec else 0
    actual_affected_pct = diag_rec.affected_percentage if diag_rec else 0.0
    diag_ai_res = DiagnosisAIService.diagnose_discrepancy(
        discrepancy_id=targeted_discrepancy_id,
        category="BOUNDARY_CONDITION",
        severity="HIGH",
        source_sql=source_sql,
        target_sql=candidate_sql,
        source_dialect="teradata",
        target_dialect="bigquery",
        source_expression="t.amount > 500",
        target_expression="t.amount >= 500",
        affected_row_count=actual_affected_rows,
        affected_percentage=actual_affected_pct,
        affected_columns=["risk_class"],
        representative_examples=[
            {"customer_id": "CUST-001", "amount": 500.00, "source_risk_class": "NORMAL", "target_risk_class": "HIGH_RISK"}
        ],
        validation_id=validation_id,
        translation_id=translation_id,
        mock_mode="MOCK_BOUNDARY_REPAIR",
    )
    diagnosis_ai_id = diag_ai_res.metadata.diagnosis_id
    repair_id = diag_ai_res.repair_proposal.repair_id
    repaired_sql = diag_ai_res.repair_proposal.proposed_sql

    print(f"-> AI Diagnosis ID:    {diagnosis_ai_id}")
    print(f"-> Repair Proposal ID:  {repair_id}")
    print(f"-> Observed Change:    {diag_ai_res.diagnosis.observed_change}")
    print(f"-> Likely Mechanism:   {diag_ai_res.diagnosis.likely_mechanism}")
    print(f"-> Proposed Repaired SQL:\n{repaired_sql}\n")

    print("-" * 85)
    print("[PHASE 8] REPAIR EXECUTION & DETERMINISTIC RE-VALIDATION ENGINE")
    print("-" * 85)
    ver_res = RepairVerificationService.verify_repair(
        repair_id=repair_id,
        discrepancy_id=targeted_discrepancy_id,
        target_dialect="bigquery",
        validation_report_before=val_report,
        source_execution=src_exec,
    )
    verification_id = ver_res.verification_id

    print(f"-> Verification ID:     {verification_id}")
    print(f"-> Final Proof Status:  {ver_res.status.value}")
    print(f"-> Summary:            {ver_res.summary}")
    print("\nItemized Discrepancy Outcomes:")
    for outcome in ver_res.outcomes:
        print(f"   Discrepancy: {outcome.discrepancy_id_before} | Status: {outcome.status.value} | Affected Rows: {outcome.affected_rows_before:,} -> {outcome.affected_rows_after:,} ({outcome.reduction_percentage:.1f}% reduction)")

    # ─────────────────────────────────────────────────────────────────────
    # PHASE 9: MIGRATION ASSURANCE & AUDIT DECISION LAYER
    # ─────────────────────────────────────────────────────────────────────
    print("\n" + "-" * 85)
    print("[PHASE 9] MIGRATION ASSURANCE & AUDIT DECISION LAYER")
    print("-" * 85)

    assurance_service = MigrationAssuranceService()

    # Create migration record
    import hashlib
    source_hash = hashlib.sha256(source_sql.encode()).hexdigest()[:16]
    migration = assurance_service.create_migration(
        source_dialect="teradata",
        target_dialect="bigquery",
        source_sql_hash=source_hash,
        dataset_id="customer_risk",
        dataset_hash=src_exec.dataset_hash,
    )

    # Evaluate assurance
    assurance_report = assurance_service.evaluate_assurance(
        migration_id=migration.migration_id,
        translation_result=trans_res,
        source_execution=src_exec,
        target_execution=tgt_exec,
        validation_report=val_report,
        discrepancy_report=disc_report,
        diagnosis_ai_result=diag_ai_res,
        repair_verification_result=ver_res,
    )

    # Inject profile metadata for display
    assurance_report.metadata["profile"] = profile_name

    # Print the final assurance report
    _print_assurance_report(assurance_report)


if __name__ == "__main__":
    run_flagship_demo()

