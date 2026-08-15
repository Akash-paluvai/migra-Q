"""Schema Validator — compares column counts, names, ordering, and data types."""

import time

from backend.validation.comparison.normalization import are_types_compatible, normalize_type_string
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


class SchemaValidator(BaseValidator):
    """Validator for comparing source and target result schemas."""

    name = "SchemaValidator"

    def validate(self, context: ValidationContext) -> ValidationResult:
        start_time = time.perf_counter()

        src_cols = context.source_execution.columns
        tgt_cols = context.target_execution.columns

        src_map = {c.name: c.type for c in src_cols}
        tgt_map = {c.name: c.type for c in tgt_cols}

        src_names = [c.name for c in src_cols]
        tgt_names = [c.name for c in tgt_cols]

        evidence_items: list[EvidenceItem] = []
        mismatch_count = 0

        # 1. Missing columns in target
        missing_cols = set(src_names) - set(tgt_names)
        for col in sorted(list(missing_cols)):
            mismatch_count += 1
            if len(evidence_items) < context.config.max_evidence_items:
                evidence_items.append(
                    EvidenceItem(
                        type=EvidenceType.SCHEMA_MISMATCH,
                        column=col,
                        source_value=src_map[col],
                        target_value=None,
                        category="COLUMN_MISSING",
                        detail=f"Column '{col}' present in source schema but missing in target.",
                    )
                )

        # 2. Extra columns in target
        extra_cols = set(tgt_names) - set(src_names)
        for col in sorted(list(extra_cols)):
            mismatch_count += 1
            if len(evidence_items) < context.config.max_evidence_items:
                evidence_items.append(
                    EvidenceItem(
                        type=EvidenceType.SCHEMA_MISMATCH,
                        column=col,
                        source_value=None,
                        target_value=tgt_map[col],
                        category="COLUMN_EXTRA",
                        detail=f"Column '{col}' present in target schema but missing in source.",
                    )
                )

        # 3. Type mismatches for common columns
        common_cols = set(src_names) & set(tgt_names)
        matched_type_count = 0
        for col in sorted(list(common_cols)):
            stype = src_map[col]
            ttype = tgt_map[col]
            if not are_types_compatible(stype, ttype):
                mismatch_count += 1
                if len(evidence_items) < context.config.max_evidence_items:
                    evidence_items.append(
                        EvidenceItem(
                            type=EvidenceType.SCHEMA_MISMATCH,
                            column=col,
                            source_value=stype,
                            target_value=ttype,
                            category="TYPE_CHANGED",
                            detail=(
                                f"Column '{col}' type changed from '{stype}' (norm: "
                                f"{normalize_type_string(stype)}) to '{ttype}' (norm: "
                                f"{normalize_type_string(ttype)})."
                            ),
                        )
                    )
            else:
                matched_type_count += 1

        # 4. Column ordering check (if enabled)
        if context.config.schema_column_order_matters and src_names != tgt_names:
            if not missing_cols and not extra_cols:
                mismatch_count += 1
                if len(evidence_items) < context.config.max_evidence_items:
                    evidence_items.append(
                        EvidenceItem(
                            type=EvidenceType.SCHEMA_MISMATCH,
                            category="COLUMN_ORDER_CHANGED",
                            source_value=src_names,
                            target_value=tgt_names,
                            detail="Column ordering differs between source and target schema.",
                        )
                    )

        total_cols = max(len(src_names), len(tgt_names))
        score = (matched_type_count / total_cols) if total_cols > 0 else 1.0
        score = max(0.0, min(1.0, score))

        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        status = ValidationCheckStatus.PASS if mismatch_count == 0 else ValidationCheckStatus.FAIL

        return ValidationResult(
            check_name=self.name,
            validator_version=VALIDATOR_VERSION,
            status=status,
            severity=ValidationSeverity.CRITICAL if mismatch_count > 0 else ValidationSeverity.INFO,
            score=round(score, 4),
            summary=(
                f"Schema comparison: {matched_type_count}/{total_cols} columns matched cleanly."
                if status == ValidationCheckStatus.PASS
                else f"Schema mismatch detected: {mismatch_count} schema discrepancy(ies)."
            ),
            expected={"columns": src_names, "types": src_map},
            actual={"columns": tgt_names, "types": tgt_map},
            mismatch_count=mismatch_count,
            evidence=evidence_items,
            evidence_truncated=mismatch_count > len(evidence_items),
            metadata={
                "source_col_count": len(src_names),
                "target_col_count": len(tgt_names),
                "missing_cols": list(missing_cols),
                "extra_cols": list(extra_cols),
            },
            duration_ms=duration_ms,
        )
