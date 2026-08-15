"""Business Rule Validator — compares structured SQLAnalysis AST abstractions from Phase 1."""

import time

from backend.analyzer.ast_diff import compare_analyses
from backend.validation.context import ValidationContext
from backend.validation.models import (
    VALIDATOR_VERSION,
    EvidenceItem,
    EvidenceType,
    ValidationCheckStatus,
    ValidationResult,
    ValidationSeverity,
)
from backend.validation.validators.base import BaseValidator


class BusinessRuleValidator(BaseValidator):
    """Validator for comparing structural SQL analysis (filters, joins, aggregations, rules)."""

    name = "BusinessRuleValidator"

    def validate(self, context: ValidationContext) -> ValidationResult:
        start_time = time.perf_counter()

        src_ana = context.source_analysis
        tgt_ana = context.target_analysis

        if not src_ana or not tgt_ana:
            return ValidationResult(
                check_name=self.name,
                validator_version=VALIDATOR_VERSION,
                status=ValidationCheckStatus.SKIPPED,
                severity=ValidationSeverity.INFO,
                score=1.0,
                summary="SQL analysis missing for source or target query.",
                duration_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
            )

        struct_diff = compare_analyses(src_ana, tgt_ana)
        diffs = struct_diff.diffs

        evidence_items: list[EvidenceItem] = []
        mismatch_count = len(diffs)

        for diff in diffs:
            if len(evidence_items) < context.config.max_evidence_items:
                evidence_items.append(
                    EvidenceItem(
                        type=EvidenceType.RULE_MISMATCH,
                        category=diff.category.value
                        if hasattr(diff.category, "value")
                        else str(diff.category),
                        source_value=diff.source_value,
                        target_value=diff.target_value,
                        detail=diff.detail,
                    )
                )

        score = 1.0 if mismatch_count == 0 else max(0.0, 1.0 - (mismatch_count * 0.2))
        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        status = ValidationCheckStatus.PASS if mismatch_count == 0 else ValidationCheckStatus.FAIL

        return ValidationResult(
            check_name=self.name,
            validator_version=VALIDATOR_VERSION,
            status=status,
            severity=ValidationSeverity.HIGH if mismatch_count > 0 else ValidationSeverity.INFO,
            score=round(score, 4),
            summary=(
                "Business rules: source and target SQL analysis are structurally equivalent."
                if status == ValidationCheckStatus.PASS
                else f"Business rule mismatch detected: {mismatch_count} structural diff(s)."
            ),
            expected={
                "rule_count": len(src_ana.business_rules),
                "filter_count": len(src_ana.filters),
            },
            actual={
                "rule_count": len(tgt_ana.business_rules),
                "filter_count": len(tgt_ana.filters),
            },
            mismatch_count=mismatch_count,
            evidence=evidence_items,
            evidence_truncated=mismatch_count > len(evidence_items),
            metadata={"diff_categories": [d.category for d in diffs]},
            duration_ms=duration_ms,
        )
