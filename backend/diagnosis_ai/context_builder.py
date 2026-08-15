"""Diagnosis context and EvidencePack builder for Phase 7 AI Diagnosis Engine."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from backend.diagnosis_ai.models import (
    DiagnosisContext,
    EvidenceItem,
    EvidencePack,
)


def build_evidence_pack(
    discrepancy_id: str,
    category: str,
    severity: str,
    classification_confidence: float = 1.0,
    source_expression: str | None = None,
    target_expression: str | None = None,
    analysis_path: str | None = None,
    affected_row_count: int = 0,
    affected_percentage: float = 0.0,
    affected_columns: list[str] | None = None,
    representative_examples: list[dict[str, Any]] | None = None,
    structural_differences: list[str] | None = None,
) -> EvidencePack:
    """Build bounded EvidencePack with stable evidence IDs (E-001, E-002, E-003, ...)."""
    items: list[EvidenceItem] = []
    aff_cols = affected_columns or []
    examples = representative_examples or []
    struct_diffs = structural_differences or []

    # E-001: Source expression / rule
    if source_expression:
        items.append(
            EvidenceItem(
                evidence_id="E-001",
                evidence_type="SOURCE_EXPRESSION",
                description=f"Source SQL expression: {source_expression}",
                details={"expression": source_expression, "path": analysis_path or ""},
            )
        )

    # E-002: Target expression / rule
    if target_expression:
        items.append(
            EvidenceItem(
                evidence_id="E-002",
                evidence_type="TARGET_EXPRESSION",
                description=f"Target SQL expression: {target_expression}",
                details={"expression": target_expression, "path": analysis_path or ""},
            )
        )

    # E-003: Discrepancy impact (affected row count & percentage)
    items.append(
        EvidenceItem(
            evidence_id="E-003",
            evidence_type="DISCREPANCY_IMPACT",
            description=(
                f"Discrepancy category '{category}' affected {affected_row_count} rows "
                f"({affected_percentage:.2f}%) across columns: {', '.join(aff_cols) if aff_cols else 'N/A'}"
            ),
            details={
                "category": category,
                "severity": severity,
                "affected_row_count": affected_row_count,
                "affected_percentage": affected_percentage,
                "affected_columns": aff_cols,
            },
        )
    )

    # E-004: Representative boundary or execution example
    if examples:
        items.append(
            EvidenceItem(
                evidence_id="E-004",
                evidence_type="REPRESENTATIVE_EXAMPLE",
                description=f"Representative row mismatch example: {json.dumps(examples[0])}",
                details={"example": examples[0]},
            )
        )

    # E-005: Structural difference (if present)
    if struct_diffs:
        items.append(
            EvidenceItem(
                evidence_id="E-005",
                evidence_type="STRUCTURAL_DIFFERENCE",
                description=f"AST structural differences: {'; '.join(struct_diffs)}",
                details={"structural_differences": struct_diffs},
            )
        )

    return EvidencePack(
        discrepancy_id=discrepancy_id,
        category=category,
        severity=severity,
        classification_confidence=classification_confidence,
        source_expression=source_expression,
        target_expression=target_expression,
        analysis_path=analysis_path,
        affected_row_count=affected_row_count,
        affected_percentage=affected_percentage,
        affected_columns=aff_cols,
        items=items,
        structural_differences=struct_diffs,
        representative_examples=examples,
    )


def build_diagnosis_context(
    discrepancy_id: str,
    validation_id: str,
    translation_id: str,
    source_sql: str,
    target_sql: str,
    source_dialect: str,
    target_dialect: str,
    evidence_pack: EvidencePack,
) -> DiagnosisContext:
    """Construct deterministic DiagnosisContext and compute context_hash."""
    raw_hash_data = {
        "discrepancy_id": discrepancy_id,
        "source_sql": source_sql.strip(),
        "target_sql": target_sql.strip(),
        "source_dialect": source_dialect.lower(),
        "target_dialect": target_dialect.lower(),
        "evidence_pack": evidence_pack.model_dump(),
    }

    serialized = json.dumps(raw_hash_data, sort_keys=True)
    context_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    return DiagnosisContext(
        discrepancy_id=discrepancy_id,
        validation_id=validation_id,
        translation_id=translation_id,
        source_sql=source_sql,
        target_sql=target_sql,
        source_dialect=source_dialect,
        target_dialect=target_dialect,
        evidence_pack=evidence_pack,
        context_hash=context_hash,
    )
