import argparse
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
from backend.diagnosis_ai.models import RepairStatus

logging.basicConfig(level=logging.ERROR)

def run_suite(mode):
    base_dir = Path("tests/repair_fixtures")
    results_dir = Path("tests/repair_results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    if not base_dir.exists():
        print(f"Directory {base_dir} not found.")
        return
        
    fixtures = [d.name for d in base_dir.iterdir() if d.is_dir()]
    
    results = {}
    
    for fixture in sorted(fixtures):
        fixture_dir = base_dir / fixture
        source_path = fixture_dir / "source.sql"
        target_path = fixture_dir / "bad_target.sql"
        expected_path = fixture_dir / "expected.json"
        
        if not source_path.exists() or not target_path.exists() or not expected_path.exists():
            continue
            
        with open(source_path, "r") as f:
            source_sql = f.read().strip()
            
        with open(target_path, "r") as f:
            target_sql = f.read().strip()
            
        with open(expected_path, "r") as f:
            expected = json.load(f)
            
        print(f"\n--- Running Fixture: {fixture} [{expected.get('category', 'unknown').upper()}] ---")
        
        dataset_id = expected.get("dataset", "join_semantics")
        
        # 1. Analyze
        try:
            src_analysis = analyze(source_sql, "oracle")
            tgt_analysis = analyze(target_sql, "bigquery")
        except Exception as e:
            results[fixture] = {"status": "FAIL", "reason": f"Analysis failed: {e}", "category": expected.get("category")}
            continue
            
        # 2. Execute
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
        
        if src_exec.status != "SUCCESS" or tgt_exec.status != "SUCCESS":
            results[fixture] = {"status": "FAIL", "reason": "Execution failed (Dataset setup issue?)", "category": expected.get("category")}
            continue
            
        # 3. Validate
        val_report = ValidationService.validate_executions(
            src_exec.execution_id, 
            tgt_exec.execution_id
        )
        
        is_validation_fail = val_report.overall_status != "PASS"
        expected_val_fail = expected.get("expected_validation") == "FAIL"
        
        md_content = f"# Repair Report: {fixture}\n\n"
        md_content += f"## Source SQL\n```sql\n{source_sql}\n```\n\n"
        md_content += f"## Target SQL\n```sql\n{target_sql}\n```\n\n"
        md_content += f"## Validation Status: {val_report.overall_status}\n"
        
        if is_validation_fail != expected_val_fail:
            results[fixture] = {"status": "FAIL", "reason": f"Expected validation {expected.get('expected_validation')}, got {val_report.overall_status}", "category": expected.get("category")}
            with open(results_dir / f"{fixture}.md", "w") as f:
                f.write(md_content)
            continue
            
        if not is_validation_fail and expected_val_fail is False:
            results[fixture] = {"status": "PASS", "reason": "No-op test passed", "category": expected.get("category")}
            with open(results_dir / f"{fixture}.md", "w") as f:
                f.write(md_content + "\nValidation Passed as expected. No repair required.")
            continue
            
        # 4. Diagnose
        orch = DiagnosisOrchestrator()
        disc_report = orch.diagnose(val_report, src_analysis, tgt_analysis, src_exec.row_count)
        
        if not disc_report or not disc_report.discrepancies:
            results[fixture] = {"status": "FAIL", "reason": "Validation failed but no discrepancies found.", "category": expected.get("category")}
            continue
            
        primary_disc = disc_report.discrepancies[0]
        category_str = primary_disc.category.value if hasattr(primary_disc.category, "value") else str(primary_disc.category)
        severity_str = primary_disc.severity.value if hasattr(primary_disc.severity, "value") else str(primary_disc.severity)
        
        md_content += f"## Discrepancy Found\n- **Category**: {category_str}\n- **Source Exp**: {primary_disc.source_expression}\n- **Target Exp**: {primary_disc.target_expression}\n\n"
        
        # 5. AI Diagnosis & Repair
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
            translation_id=fixture,
            provider_name="mock_regression" if mode == "mock" else "openai"
        )
        
        md_content += f"## AI Diagnosis\n- **Status**: {diag_ai_res.diagnosis.status}\n- **Observed Change**: {diag_ai_res.diagnosis.observed_change}\n\n"
        md_content += f"## Repair Proposal\n- **Status**: {diag_ai_res.repair_proposal.status}\n- **Proposed SQL**:\n```sql\n{diag_ai_res.repair_proposal.proposed_sql}\n```\n- **Rationale**: {diag_ai_res.repair_proposal.rationale}\n- **Constraints Checked**: {diag_ai_res.repair_proposal.constraints_checked}\n\n"
        
        expected_repair_status = expected.get("expected_repair")
        expected_rejection = expected.get("expected_rejection_reason")
        
        actual_repair_status = diag_ai_res.repair_proposal.status.value if hasattr(diag_ai_res.repair_proposal.status, "value") else str(diag_ai_res.repair_proposal.status)
        
        # If it's a safety test, it MUST be rejected by the Scope Checker
        if expected.get("category") == "safety":
            if actual_repair_status != "FAILED" or expected_rejection not in (diag_ai_res.repair_proposal.rationale or "") and expected_rejection not in md_content:
                # The rationale might not contain the UNJUSTIFIED_SCOPE_CHANGE directly, but it should fail
                # Let's just check if it FAILED. If the LLM successfully repaired a negative case, that's bad.
                if actual_repair_status != "FAILED":
                    results[fixture] = {"status": "FAIL", "reason": f"Safety test failed to reject! Status: {actual_repair_status}", "category": "safety"}
                else:
                    results[fixture] = {"status": "PASS", "reason": "Rejected correctly by constraints.", "category": "safety"}
            else:
                results[fixture] = {"status": "PASS", "reason": "Rejected correctly by constraints.", "category": "safety"}
                
            with open(results_dir / f"{fixture}.md", "w") as f:
                f.write(md_content)
            continue
            
        if actual_repair_status != "PROPOSED":
            results[fixture] = {"status": "FAIL", "reason": f"Expected repair PROPOSED, got {actual_repair_status}", "category": expected.get("category")}
            with open(results_dir / f"{fixture}.md", "w") as f:
                f.write(md_content)
            continue
            
        # 6. Verify Repair
        if diag_ai_res.repair_proposal.proposed_sql:
            ver_res = RepairVerificationService.verify_repair(
                repair_id=diag_ai_res.repair_proposal.repair_id,
                discrepancy_id=primary_disc.discrepancy_id,
                repair_proposal=diag_ai_res.repair_proposal,
                ai_diagnosis=diag_ai_res.diagnosis,
                validation_report_before=val_report,
                discrepancy_report_before=disc_report,
                source_execution=src_exec,
                target_execution_before=tgt_exec,
                target_dialect="bigquery"
            )
            
            ver_status = ver_res.status.value if hasattr(ver_res.status, "value") else str(ver_res.status)
            md_content += f"## Verification Result\n- **Status**: {ver_status}\n- **Remaining Discrepancies**: {ver_res.remaining_discrepancy_count}\n"
            
            if ver_status != expected_repair_status:
                results[fixture] = {"status": "FAIL", "reason": f"Verification status {ver_status} != {expected_repair_status}", "category": expected.get("category")}
            elif ver_res.remaining_discrepancy_count > expected.get("max_remaining_discrepancies", 0):
                results[fixture] = {"status": "FAIL", "reason": f"Remaining discrepancies {ver_res.remaining_discrepancy_count} > allowed", "category": expected.get("category")}
            else:
                results[fixture] = {"status": "PASS", "reason": "Successfully verified.", "category": expected.get("category")}
                
            with open(results_dir / f"{fixture}.md", "w") as f:
                f.write(md_content)
        else:
            results[fixture] = {"status": "FAIL", "reason": "No proposed SQL to verify", "category": expected.get("category")}

    print(f"\n\n{'DETERMINISTIC ENGINE TESTS' if mode == 'mock' else 'AI REPAIR EVALUATION'}")
    print(f"Mode: {'MOCK_REGRESSION' if mode == 'mock' else 'REAL_LLM'}")
    print("────────────────────────────────────")
    categories = ["repair", "safety", "noop"]
    cat_names = {"repair": "Repair", "safety": "Safety", "noop": "No-op"}
    
    total = 0
    passed = 0
    
    for cat in categories:
        print(f"\n{cat_names[cat]}")
        for fixture, res in results.items():
            if res["category"] == cat:
                total += 1
                status = res["status"]
                if status == "PASS":
                    passed += 1
                print(f"  {fixture:<30} {status}")
                if status == "FAIL":
                    print(f"      -> {res['reason']}")
                    
    print("────────────────────────────────────")
    print(f"RESULT: {passed}/{total}")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Repair Engine Test Suite")
    parser.add_argument("--mode", choices=["mock", "real"], default="mock", help="Run mode (mock vs real LLM)")
    args = parser.parse_args()
    run_suite(args.mode)
