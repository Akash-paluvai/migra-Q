"""DiscrepancyDiffAnalyzer — hierarchical region-aware discrepancy comparison engine for Phase 8."""

from __future__ import annotations

import re

from backend.diagnosis.models import DiscrepancyRecord, DiscrepancyReport
from backend.repair_verification.models import DiscrepancyOutcome, DiscrepancyOutcomeStatus


class DiscrepancyDiffAnalyzer:
    """Analyzes BEFORE vs AFTER DiscrepancyReports using hierarchical region-aware matching."""

    @classmethod
    def normalize_expression(cls, expr: str | None) -> str:
        """Normalize SQL expressions for stable semantic comparison."""
        if not expr:
            return ""
        s = expr.lower().strip()
        s = re.sub(r"\s+", " ", s)
        s = s.replace(";", "")
        return s

    @classmethod
    def compute_semantic_signature(cls, rec: DiscrepancyRecord) -> str:
        """Compute normalized semantic signature for a discrepancy record."""
        cat = rec.category.value if hasattr(rec.category, "value") else str(rec.category)
        path = rec.analysis_path or ""
        src_e = cls.normalize_expression(rec.source_expression)
        tgt_e = cls.normalize_expression(rec.target_expression)

        if rec.discrepancy_signature:
            return rec.discrepancy_signature

        return f"{cat}|{path}|{src_e}|{tgt_e}"

    @classmethod
    def get_affected_region(cls, rec: DiscrepancyRecord) -> str:
        """Determine primary affected logical region (e.g. columns[risk_class], JOIN, GROUP BY)."""
        if rec.analysis_path:
            return rec.analysis_path.lower()
        if rec.affected_output_columns:
            cols = ",".join(sorted(rec.affected_output_columns))
            return f"columns[{cols}]".lower()
        if rec.source_location:
            return rec.source_location.lower()
        return "global"

    @classmethod
    def analyze_targeted_discrepancy(
        cls,
        target_d_before: DiscrepancyRecord,
        after_report: DiscrepancyReport,
    ) -> DiscrepancyOutcome:
        """Perform 5-step hierarchical region-aware resolution check for a targeted discrepancy.

        1. Exact semantic signature match in AFTER report -> PERSISTS
        2. Equivalent category + region match in AFTER report -> PERSISTS
        3. Replacement discrepancy in same affected logical region -> CHANGED / NOT RESOLVED
        4. No discrepancy affecting target region in AFTER report -> RESOLVED
        5. Unrelated new discrepancies introduced -> flagged separately in new_discrepancies
        """
        sig_before = cls.compute_semantic_signature(target_d_before)
        region_before = cls.get_affected_region(target_d_before)
        cat_before = target_d_before.category.value if hasattr(target_d_before.category, "value") else str(target_d_before.category)

        after_recs = after_report.discrepancies if after_report else []

        matching_ids: list[str] = []
        new_in_region_ids: list[str] = []

        for rec in after_recs:
            sig_after = cls.compute_semantic_signature(rec)
            region_after = cls.get_affected_region(rec)
            cat_after = rec.category.value if hasattr(rec.category, "value") else str(rec.category)

            # Step 1: Exact signature match
            if sig_before == sig_after:
                matching_ids.append(rec.discrepancy_id)
                rows_after = rec.affected_row_count
                red_count = max(0, target_d_before.affected_row_count - rows_after)
                red_pct = (
                    round((red_count / target_d_before.affected_row_count) * 100.0, 2)
                    if target_d_before.affected_row_count > 0
                    else 0.0
                )
                return DiscrepancyOutcome(
                    discrepancy_id_before=target_d_before.discrepancy_id,
                    category=cat_before,
                    analysis_path=target_d_before.analysis_path,
                    affected_region=region_before,
                    status=DiscrepancyOutcomeStatus.PERSISTS,
                    affected_rows_before=target_d_before.affected_row_count,
                    affected_rows_after=rows_after,
                    reduction_count=red_count,
                    reduction_percentage=red_pct,
                    matching_after_discrepancy_ids=[rec.discrepancy_id],
                    summary=f"Discrepancy '{target_d_before.discrepancy_id}' ({cat_before}) persists after repair ({rows_after} affected rows).",
                )

            # Step 2 & 3: Region match
            if region_before == region_after or (region_before != "global" and region_before in region_after):
                if cat_before == cat_after:
                    matching_ids.append(rec.discrepancy_id)
                else:
                    new_in_region_ids.append(rec.discrepancy_id)

        if matching_ids:
            rec = next(r for r in after_recs if r.discrepancy_id == matching_ids[0])
            rows_after = rec.affected_row_count
            red_count = max(0, target_d_before.affected_row_count - rows_after)
            red_pct = (
                round((red_count / target_d_before.affected_row_count) * 100.0, 2)
                if target_d_before.affected_row_count > 0
                else 0.0
            )
            return DiscrepancyOutcome(
                discrepancy_id_before=target_d_before.discrepancy_id,
                category=cat_before,
                analysis_path=target_d_before.analysis_path,
                affected_region=region_before,
                status=DiscrepancyOutcomeStatus.PERSISTS,
                affected_rows_before=target_d_before.affected_row_count,
                affected_rows_after=rows_after,
                reduction_count=red_count,
                reduction_percentage=red_pct,
                matching_after_discrepancy_ids=matching_ids,
                summary=f"Equivalent discrepancy in region '{region_before}' persists as '{matching_ids[0]}'.",
            )

        if new_in_region_ids:
            rec = next(r for r in after_recs if r.discrepancy_id == new_in_region_ids[0])
            cat_new = rec.category.value if hasattr(rec.category, "value") else str(rec.category)
            return DiscrepancyOutcome(
                discrepancy_id_before=target_d_before.discrepancy_id,
                category=cat_before,
                analysis_path=target_d_before.analysis_path,
                affected_region=region_before,
                status=DiscrepancyOutcomeStatus.CHANGED,
                affected_rows_before=target_d_before.affected_row_count,
                affected_rows_after=rec.affected_row_count,
                reduction_count=0,
                reduction_percentage=0.0,
                new_discrepancy_ids=new_in_region_ids,
                summary=f"Original discrepancy transformed into '{cat_new}' ({new_in_region_ids[0]}) in region '{region_before}'.",
            )

        # Step 4: Discrepancy absent in AFTER report -> RESOLVED
        return DiscrepancyOutcome(
            discrepancy_id_before=target_d_before.discrepancy_id,
            category=cat_before,
            analysis_path=target_d_before.analysis_path,
            affected_region=region_before,
            status=DiscrepancyOutcomeStatus.RESOLVED,
            affected_rows_before=target_d_before.affected_row_count,
            affected_rows_after=0,
            reduction_count=target_d_before.affected_row_count,
            reduction_percentage=100.0,
            summary=f"Targeted discrepancy '{target_d_before.discrepancy_id}' ({cat_before}) in region '{region_before}' resolved (0 affected rows).",
        )

    @classmethod
    def categorize_before_and_after_discrepancies(
        cls,
        before_report: DiscrepancyReport,
        after_report: DiscrepancyReport | None,
        target_discrepancy_id: str,
    ) -> tuple[DiscrepancyOutcome, list[str], list[str], list[str]]:
        """Categorize all discrepancies into targeted outcome, resolved, remaining, and new.

        Returns (target_outcome, resolved_ids, remaining_ids, new_ids).
        """
        before_recs = before_report.discrepancies if before_report else []
        after_recs = after_report.discrepancies if after_report else []

        target_before = next((r for r in before_recs if r.discrepancy_id == target_discrepancy_id), None)
        if not target_before and before_recs:
            target_before = before_recs[0]

        if not target_before:
            dummy_target = DiscrepancyRecord(
                discrepancy_id=target_discrepancy_id,
                validation_id=before_report.validation_id if before_report else "val-none",
                category="UNKNOWN",  # type: ignore[arg-type]
                severity="HIGH",  # type: ignore[arg-type]
                classification_confidence=1.0,
                classification_method="DETERMINISTIC_RULE",  # type: ignore[arg-type]
                classification_reason="Unknown target discrepancy",
                created_at="",
            )
            target_outcome = cls.analyze_targeted_discrepancy(dummy_target, after_report or DiscrepancyReport(diagnosis_id="", validation_id=""))
        else:
            target_outcome = cls.analyze_targeted_discrepancy(target_before, after_report or DiscrepancyReport(diagnosis_id="", validation_id=""))

        # Map signatures for BEFORE and AFTER
        before_sigs = {cls.compute_semantic_signature(r): r for r in before_recs}
        after_sigs = {cls.compute_semantic_signature(r): r for r in after_recs}

        resolved_ids: list[str] = []
        remaining_ids: list[str] = []
        new_ids: list[str] = []

        # Check BEFORE records
        for sig, r_before in before_sigs.items():
            if sig in after_sigs:
                remaining_ids.append(after_sigs[sig].discrepancy_id)
            else:
                # Region check: did it persist as a different signature in same region?
                reg = cls.get_affected_region(r_before)
                matched_after = [r for r in after_recs if cls.get_affected_region(r) == reg]
                if matched_after:
                    remaining_ids.append(matched_after[0].discrepancy_id)
                else:
                    resolved_ids.append(r_before.discrepancy_id)

        # Check AFTER records: if present in AFTER but NOT matching any BEFORE signature/region -> NEW (regression)
        for r_after in after_recs:
            sig = cls.compute_semantic_signature(r_after)
            reg = cls.get_affected_region(r_after)

            matched_before_sig = sig in before_sigs
            matched_before_reg = any(cls.get_affected_region(rb) == reg for rb in before_recs)

            if not (matched_before_sig or matched_before_reg):
                new_ids.append(r_after.discrepancy_id)

        return target_outcome, list(set(resolved_ids)), list(set(remaining_ids)), list(set(new_ids))
