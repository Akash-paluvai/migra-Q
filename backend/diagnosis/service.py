"""DiagnosisService facade handling diagnosis creation, retrieval, and persistence."""

import json

from backend.analyzer.service import AnalyzerService
from backend.db.database import SessionLocal
from backend.db.models import (
    DiagnosisRecord,
    DiscrepancyEvidenceRecordModel,
    DiscrepancyRecordModel,
)
from backend.diagnosis.models import DiscrepancyReport
from backend.diagnosis.orchestrator import DiagnosisOrchestrator
from backend.execution.service import ExecutionService
from backend.validation.service import ValidationService

_DIAGNOSIS_STORE: dict[str, DiscrepancyReport] = {}


class DiagnosisService:
    """Facade for triggering, retrieving, and persisting discrepancy diagnosis reports."""

    @staticmethod
    def diagnose_validation(
        validation_id: str,
        max_evidence_items: int = 100,
    ) -> DiscrepancyReport:
        """Run diagnosis pipeline for a given validation ID."""
        # 1. Fetch ValidationReport
        report = ValidationService.get_validation(validation_id)
        if not report:
            raise ValueError(f"Validation ID '{validation_id}' not found.")

        # 2. Retrieve execution results & SQL analyses if available
        src_exec = ExecutionService.get_execution(report.source_execution_id)
        tgt_exec = ExecutionService.get_execution(report.target_execution_id)

        total_rows = src_exec.row_count if src_exec else 0

        src_ana = None
        tgt_ana = None

        if src_exec and hasattr(src_exec, "metadata") and src_exec.metadata.get("sql"):
            try:
                src_dialect = src_exec.metadata.get("dialect", "teradata")
                src_ana = AnalyzerService.analyze(src_exec.metadata["sql"], dialect=src_dialect)
            except Exception:
                pass

        if tgt_exec and hasattr(tgt_exec, "metadata") and tgt_exec.metadata.get("sql"):
            try:
                tgt_dialect = tgt_exec.metadata.get("dialect", "bigquery")
                tgt_ana = AnalyzerService.analyze(tgt_exec.metadata["sql"], dialect=tgt_dialect)
            except Exception:
                pass

        # 3. Run Diagnosis Orchestrator
        orchestrator = DiagnosisOrchestrator()
        diag_report = orchestrator.diagnose(
            report=report,
            source_analysis=src_ana,
            target_analysis=tgt_ana,
            total_output_rows=total_rows,
            max_evidence_items=max_evidence_items,
        )

        # 4. Cache in memory
        _DIAGNOSIS_STORE[diag_report.diagnosis_id] = diag_report

        # 5. Persist to PostgreSQL if available
        try:
            with SessionLocal() as session:
                d_rec = DiagnosisRecord(
                    diagnosis_id=diag_report.diagnosis_id,
                    validation_id=diag_report.validation_id,
                    classifier_version=diag_report.classifier_version,
                    summary_json=json.dumps(diag_report.summary_statistics),
                )
                session.add(d_rec)

                for disc in diag_report.discrepancies:
                    disc_rec = DiscrepancyRecordModel(
                        diagnosis_id=diag_report.diagnosis_id,
                        discrepancy_id=disc.discrepancy_id,
                        category=disc.category.value,
                        subcategory=disc.subcategory,
                        severity=disc.severity.value,
                        classification_confidence=disc.classification_confidence,
                        source_location=disc.source_location,
                        target_location=disc.target_location,
                        source_expression=disc.source_expression,
                        target_expression=disc.target_expression,
                        affected_row_count=disc.affected_row_count,
                        affected_percentage=disc.affected_percentage,
                        status=disc.status,
                        reason=disc.classification_reason,
                        analysis_path=disc.analysis_path,
                        discrepancy_signature=disc.discrepancy_signature,
                    )
                    session.add(disc_rec)

                    for ev in disc.evidence:
                        ev_rec = DiscrepancyEvidenceRecordModel(
                            discrepancy_id=disc.discrepancy_id,
                            evidence_type=ev.type,
                            evidence_json=json.dumps(ev.model_dump()),
                            ordinal=ev.ordinal,
                        )
                        session.add(ev_rec)

                session.commit()
        except Exception:
            pass  # DB connection optional

        return diag_report

    @staticmethod
    def get_diagnosis(diagnosis_id: str) -> DiscrepancyReport | None:
        """Retrieve stored DiscrepancyReport by diagnosis_id."""
        if diagnosis_id in _DIAGNOSIS_STORE:
            return _DIAGNOSIS_STORE[diagnosis_id]
        return None
