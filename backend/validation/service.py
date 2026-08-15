"""ValidationService — orchestrates validation, persists results, and serves reports."""

import json
from pathlib import Path
from typing import Any

from backend.analyzer.models import SQLAnalysis
from backend.db.database import get_db
from backend.db.models import ValidationRecord, ValidationResultRecord
from backend.execution.service import ExecutionService
from backend.validation.context import ValidationContext
from backend.validation.exceptions import ValidationError
from backend.validation.models import ValidationConfig, ValidationReport
from backend.validation.orchestrator import ValidationOrchestrator


class ValidationService:
    """Service facade for semantic validation execution and retrieval."""

    @classmethod
    def validate_executions(
        cls,
        source_execution_id: str,
        target_execution_id: str,
        source_analysis: SQLAnalysis | dict[str, Any] | None = None,
        target_analysis: SQLAnalysis | dict[str, Any] | None = None,
        config: ValidationConfig | None = None,
        benchmark_scenario: dict[str, Any] | None = None,
        base_dir: Path | None = None,
    ) -> ValidationReport:
        """Run semantic validation between two completed Phase 3 executions."""
        src_exec = ExecutionService.get_execution(source_execution_id)
        if not src_exec:
            raise ValidationError(f"Source execution '{source_execution_id}' not found.")

        tgt_exec = ExecutionService.get_execution(target_execution_id)
        if not tgt_exec:
            raise ValidationError(f"Target execution '{target_execution_id}' not found.")

        if isinstance(source_analysis, dict):
            source_analysis = SQLAnalysis.model_validate(source_analysis)
        if isinstance(target_analysis, dict):
            target_analysis = SQLAnalysis.model_validate(target_analysis)

        if config is None:
            config = ValidationConfig()

        context = ValidationContext(
            source_execution=src_exec,
            target_execution=tgt_exec,
            source_analysis=source_analysis,
            target_analysis=target_analysis,
            config=config,
            benchmark_scenario=benchmark_scenario,
        )

        orchestrator = ValidationOrchestrator()
        report = orchestrator.validate(context)

        # Persist to disk artifact
        cls._persist_report_artifact(report, base_dir=base_dir)

        # Persist to PostgreSQL
        cls._persist_to_db(report)

        return report

    @classmethod
    def get_validation(
        cls, validation_id: str, base_dir: Path | None = None
    ) -> ValidationReport | None:
        """Retrieve a completed validation report by validation_id."""
        if base_dir is None:
            base_dir = Path.cwd() / "datasets" / "runtime_results" / "validations"

        artifact_path = base_dir / f"{validation_id}.json"
        if artifact_path.exists():
            with open(artifact_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return ValidationReport.model_validate(data)

        # Fallback to DB
        try:
            with get_db() as db:
                rec = (
                    db.query(ValidationRecord)
                    .filter(ValidationRecord.validation_id == validation_id)
                    .first()
                )
                if not rec:
                    return None

                results_recs = (
                    db.query(ValidationResultRecord)
                    .filter(ValidationResultRecord.validation_id == validation_id)
                    .all()
                )
                checks = []
                for r in results_recs:
                    checks.append(
                        {
                            "check_name": r.check_name,
                            "validator_version": rec.validator_version,
                            "status": r.status,
                            "severity": r.severity,
                            "score": r.score,
                            "summary": r.summary or "",
                            "mismatch_count": r.mismatch_count,
                            "evidence": json.loads(r.evidence_json) if r.evidence_json else [],
                            "metadata": json.loads(r.metadata_json) if r.metadata_json else {},
                            "duration_ms": r.duration_ms,
                        }
                    )

                return ValidationReport(
                    validation_id=rec.validation_id,
                    source_execution_id=rec.source_execution_id,
                    target_execution_id=rec.target_execution_id,
                    dataset_id=rec.dataset_id,
                    created_at=rec.created_at.isoformat() if rec.created_at else "",
                    validator_version=rec.validator_version,
                    checks=checks,
                    overall_status=rec.status,
                    summary=json.loads(rec.summary_json) if rec.summary_json else {},
                )
        except Exception:
            return None

    @classmethod
    def _persist_report_artifact(
        cls, report: ValidationReport, base_dir: Path | None = None
    ) -> None:
        """Write validation report JSON file to disk."""
        if base_dir is None:
            base_dir = Path.cwd() / "datasets" / "runtime_results" / "validations"

        base_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = base_dir / f"{report.validation_id}.json"

        with open(artifact_path, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))

    @classmethod
    def _persist_to_db(cls, report: ValidationReport) -> None:
        """Audit record persistence to PostgreSQL database."""
        try:
            with get_db() as db:
                val_rec = ValidationRecord(
                    validation_id=report.validation_id,
                    source_execution_id=report.source_execution_id,
                    target_execution_id=report.target_execution_id,
                    dataset_id=report.dataset_id,
                    status=report.overall_status,
                    validator_version=report.validator_version,
                    summary_json=json.dumps(report.summary),
                )
                db.add(val_rec)

                for check in report.checks:
                    res_rec = ValidationResultRecord(
                        validation_id=report.validation_id,
                        check_name=check.check_name,
                        status=check.status,
                        severity=check.severity,
                        score=check.score,
                        mismatch_count=check.mismatch_count,
                        summary=check.summary,
                        evidence_json=json.dumps([e.model_dump() for e in check.evidence]),
                        metadata_json=json.dumps(check.metadata),
                        duration_ms=check.duration_ms,
                    )
                    db.add(res_rec)

                db.commit()
        except Exception:
            pass  # PostgreSQL soft tolerance for local unconfigured environments
