"""Diagnosis Orchestrator for controlling the Phase 5 diagnostic pipeline."""

import uuid
from datetime import datetime, timezone

from backend.analyzer.models import SQLAnalysis
from backend.diagnosis import CLASSIFIER_VERSION
from backend.diagnosis.evidence import EvidenceConsolidator
from backend.diagnosis.extractor import SignalExtractor
from backend.diagnosis.models import DiscrepancyCategory, DiscrepancyReport
from backend.validation.models import ValidationReport


class DiagnosisOrchestrator:
    """Orchestrates Phase 5 discrepancy extraction, consolidation, and classification."""

    def __init__(self, consolidator: EvidenceConsolidator | None = None) -> None:
        self.consolidator = consolidator or EvidenceConsolidator()

    def diagnose(
        self,
        report: ValidationReport,
        source_analysis: SQLAnalysis | None = None,
        target_analysis: SQLAnalysis | None = None,
        total_output_rows: int = 0,
        max_evidence_items: int = 100,
    ) -> DiscrepancyReport:
        """Run complete diagnostic pipeline on ValidationReport and SQLAnalysis."""
        now_iso = datetime.now(timezone.utc).isoformat()
        diagnosis_id = str(uuid.uuid4())

        # Step 1: Signal Extraction
        signals = SignalExtractor.extract_signals(report, source_analysis, target_analysis)

        # Step 2: Evidence Consolidation & Classification
        discrepancies = self.consolidator.consolidate(
            validation_id=report.validation_id,
            signals=signals,
            total_output_rows=total_output_rows,
            max_evidence_items=max_evidence_items,
            created_at=now_iso,
        )

        # Step 3: Compute Summary Counts & Statistics
        category_counts: dict[str, int] = {cat.value: 0 for cat in DiscrepancyCategory}
        severity_counts: dict[str, int] = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
            "INFO": 0,
        }

        for d in discrepancies:
            category_counts[d.category.value] = category_counts.get(d.category.value, 0) + 1
            severity_counts[d.severity.value] = severity_counts.get(d.severity.value, 0) + 1

        summary_stats = {
            "discrepancy_count": len(discrepancies),
            "signals_extracted": len(signals),
            "affected_rows_total": sum((d.affected_row_count or 0) for d in discrepancies),
        }

        return DiscrepancyReport(
            diagnosis_id=diagnosis_id,
            validation_id=report.validation_id,
            created_at=now_iso,
            classifier_version=CLASSIFIER_VERSION,
            discrepancies=discrepancies,
            discrepancy_count=len(discrepancies),
            category_counts=category_counts,
            severity_counts=severity_counts,
            summary_statistics=summary_stats,
        )
