import os
import json
import logging
from pathlib import Path

from backend.execution.models import ExecutionRequest, ExecutionMode
from backend.execution.service import ExecutionService
from backend.validation.service import ValidationService
from backend.diagnosis_ai.service import DiagnosisAIService
from backend.analyzer.service import analyze
from backend.repair_verification.service import RepairVerificationService
from backend.diagnosis.orchestrator import DiagnosisOrchestrator

logging.basicConfig(level=logging.INFO)

def run_fixture(fixture):
    base_dir = Path("tests/repair_fixtures")
    fixture_dir = base_dir / fixture
    source_path = fixture_dir / "source.sql"
    target_path = fixture_dir / "bad_target.sql"
    expected_path = fixture_dir / "expected.json"
    
    with open(source_path, "r") as f:
        source_sql = f.read().strip()
        
    with open(target_path, "r") as f:
        target_sql = f.read().strip()
        
    with open(expected_path, "r") as f:
        expected = json.load(f)
        
    print(f"\n--- Running Fixture: {fixture} [{expected.get('category', 'unknown').upper()}] ---")
    
    dataset_id = expected.get("dataset", "join_semantics")
    
    src_analysis = analyze(source_sql, "oracle")
    tgt_analysis = analyze(target_sql, "bigquery")
    
    src_exec = ExecutionService.execute(
        ExecutionRequest(
            sql=source_sql, 
            dialect="oracle", 
            dataset_id=dataset_id, 
            execution_mode=ExecutionMode.SOURCE
        )
    )
    tgt_exec = ExecutionService.execute(
        ExecutionRequest(
            sql=target_sql, 
            dialect="bigquery", 
            dataset_id=dataset_id, 
            execution_mode=ExecutionMode.TARGET
        )
    )
    
    val_report = ValidationService.validate_executions(
        src_exec.execution_id, 
        tgt_exec.execution_id
    )
    
    print(f"Validation Status: {val_report.overall_status}")
    if val_report.overall_status == "PASS":
        return
        
    orch = DiagnosisOrchestrator()
    disc_report = orch.diagnose(val_report, src_analysis, tgt_analysis, src_exec.row_count)
    
    primary_disc = disc_report.discrepancies[0]
    category_str = primary_disc.category.value if hasattr(primary_disc.category, "value") else str(primary_disc.category)
    severity_str = primary_disc.severity.value if hasattr(primary_disc.severity, "value") else str(primary_disc.severity)
    
    print(f"Discrepancy Found: {category_str}")
    print(f"Source Exp: {primary_disc.source_expression}")
    print(f"Target Exp: {primary_disc.target_expression}")
    
    diag_ai_res = DiagnosisAIService.diagnose_discrepancy(
        discrepancy_id=primary_disc.discrepancy_id,
        category=category_str,
        severity=severity_str,
        source_sql=source_sql,
        target_sql=target_sql,
        source_dialect="oracle",
        target_dialect="bigquery",
        source_expression=primary_disc.source_expression,
        target_expression=primary_disc.target_expression,
        affected_row_count=primary_disc.affected_row_count,
        affected_percentage=primary_disc.affected_percentage,
        affected_columns=primary_disc.affected_output_columns,
        analysis_path=getattr(primary_disc, "analysis_path", "") or ",".join(primary_disc.affected_output_columns),
        validation_id=val_report.validation_id,
        translation_id="test-trans",
        provider_name="openai"
    )
    
    print(f"Repair Status: {diag_ai_res.repair_proposal.status}")
    print(f"Proposed SQL: {diag_ai_res.repair_proposal.proposed_sql}")
    print(f"Rationale: {diag_ai_res.repair_proposal.rationale}")

if __name__ == "__main__":
    import sys
    run_fixture(sys.argv[1])
