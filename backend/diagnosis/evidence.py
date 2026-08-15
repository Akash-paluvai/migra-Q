"""Evidence Consolidator for consolidating signals into distinct semantic discrepancies."""

from backend.diagnosis.classifier import DiscrepancyClassifier
from backend.diagnosis.confidence import ConfidenceCalculator
from backend.diagnosis.models import (
    DiscrepancyCategory,
    DiscrepancyRecord,
    TypedEvidence,
    TypedEvidenceType,
)
from backend.diagnosis.normalizer import compute_discrepancy_signature
from backend.diagnosis.severity import SeverityCalculator
from backend.diagnosis.signals import RawDiscrepancySignal


class EvidenceConsolidator:
    """Consolidates raw signals into distinct semantic discrepancy records."""

    def __init__(self, classifier: DiscrepancyClassifier | None = None) -> None:
        self.classifier = classifier or DiscrepancyClassifier()

    def consolidate(
        self,
        validation_id: str,
        signals: list[RawDiscrepancySignal],
        total_output_rows: int = 0,
        max_evidence_items: int = 100,
        created_at: str = "2026-08-15T00:00:00Z",
    ) -> list[DiscrepancyRecord]:
        """Group signals into distinct semantic discrepancies via deterministic signatures."""
        if not signals:
            return []

        # Map signals by signature: (category, analysis_path, source_expression, target_expression)
        groups: dict[str, list[RawDiscrepancySignal]] = {}

        # Find primary AST/structural signals to inherit expressions and paths
        ast_signals = [
            s
            for s in signals
            if s.source_validator in ("BusinessRuleValidator", "AST_ANALYZER")
            or s.source_expression
        ]

        for sig in signals:
            path = sig.analysis_path
            src_expr = sig.source_expression
            tgt_expr = sig.target_expression

            # If execution signal lacks expressions or matching path, link to AST signal
            if ast_signals and sig.source_validator in ("RowValidator", "EdgeCaseValidator"):
                for ast_s in ast_signals:
                    if (
                        not path
                        or path == ast_s.analysis_path
                        or path.startswith(ast_s.analysis_path)
                        or ast_s.analysis_path.startswith(path)
                    ):
                        src_expr = src_expr or ast_s.source_expression
                        tgt_expr = tgt_expr or ast_s.target_expression
                        path = ast_s.analysis_path
                        break

            candidate = self.classifier.classify_signal(sig, signals)
            base_path = path or candidate.analysis_path
            norm_path = base_path.split(".")[0] if base_path else ""

            sig_hash = compute_discrepancy_signature(
                category=candidate.category.value,
                analysis_path=norm_path,
                source_expr=src_expr or candidate.source_expression,
                target_expr=tgt_expr or candidate.target_expression,
            )

            if sig_hash not in groups:
                groups[sig_hash] = []
            groups[sig_hash].append(sig)

        discrepancies: list[DiscrepancyRecord] = []
        disc_index = 1

        # Process each consolidated group deterministically
        for sig_hash in sorted(groups.keys()):
            sig_list = sorted(
                groups[sig_hash], key=lambda s: (s.source_validator, s.signal_type, s.analysis_path)
            )
            first_sig = sig_list[0]
            candidate = self.classifier.classify_signal(first_sig, signals)

            # Aggregate evidence & row counts across signals in this group
            affected_rows = 0
            has_exec_evidence = False
            has_edge_case = False
            has_struct_match = any(
                s.source_validator in ("BusinessRuleValidator", "AST_ANALYZER") for s in sig_list
            )
            validator_checks = sorted(list(set(s.source_validator for s in sig_list)))

            typed_evidences: list[TypedEvidence] = []
            ev_ordinal = 1

            for s in sig_list:
                payload = s.payload
                # Check for row mismatch signal
                if (
                    s.source_validator == "RowValidator"
                    or "VALUE_MISMATCH" in s.signal_type
                    or "mismatch" in s.signal_type
                ):
                    has_exec_evidence = True
                    row_cnt = payload.get("mismatch_count", 0) or payload.get("rows_compared", 0)
                    if row_cnt > affected_rows:
                        affected_rows = row_cnt

                    if len(typed_evidences) < max_evidence_items:
                        typed_evidences.append(
                            TypedEvidence(
                                type=TypedEvidenceType.ROW_DIFF.value,
                                column=payload.get("column"),
                                value=payload.get("value"),
                                source_result=payload.get("source_value"),
                                target_result=payload.get("target_value"),
                                row_key=payload.get("key"),
                                detail=payload.get(
                                    "detail", f"Row difference in column {payload.get('column')}"
                                ),
                                ordinal=ev_ordinal,
                            )
                        )
                        ev_ordinal += 1

                elif s.source_validator == "EdgeCaseValidator" or "EDGE_CASE" in s.signal_type:
                    has_edge_case = True
                    has_exec_evidence = True
                    if len(typed_evidences) < max_evidence_items:
                        typed_evidences.append(
                            TypedEvidence(
                                type=TypedEvidenceType.BOUNDARY_CASE.value
                                if candidate.category == DiscrepancyCategory.BOUNDARY_CONDITION
                                else TypedEvidenceType.ROW_DIFF.value,
                                detail=payload.get(
                                    "detail", "Edge case scenario mismatch confirmed"
                                ),
                                ordinal=ev_ordinal,
                            )
                        )
                        ev_ordinal += 1

                elif s.source_validator in ("BusinessRuleValidator", "AST_ANALYZER"):
                    if len(typed_evidences) < max_evidence_items:
                        detail_msg = f"Rule diff: {s.source_expression} vs {s.target_expression}"
                        typed_evidences.append(
                            TypedEvidence(
                                type=TypedEvidenceType.RULE_DIFF.value,
                                source_result=s.source_expression,
                                target_result=s.target_expression,
                                detail=payload.get("detail", detail_msg),
                                ordinal=ev_ordinal,
                            )
                        )
                        ev_ordinal += 1

            # Compute severity & confidence
            severity = SeverityCalculator.calculate_severity(
                category=candidate.category,
                affected_row_count=affected_rows,
                total_output_rows=total_output_rows,
            )

            confidence = ConfidenceCalculator.calculate_confidence(
                has_structural_match=has_struct_match,
                has_execution_evidence=has_exec_evidence,
                has_edge_case_confirmation=has_edge_case,
                is_unknown=(candidate.category == DiscrepancyCategory.UNKNOWN),
            )

            affected_pct = round(
                (affected_rows / total_output_rows * 100.0) if total_output_rows > 0 else 0.0, 3
            )

            # Build human-readable deterministic classification reason
            reason_parts = [candidate.reason_template]
            if affected_rows > 0:
                reason_parts.append(f"Execution evidence confirms {affected_rows} affected rows.")
            if has_edge_case:
                reason_parts.append(
                    "Edge-case scenario test confirms behavioral boundary discrepancy."
                )
            classification_reason = " ".join(reason_parts)

            discrepancies.append(
                DiscrepancyRecord(
                    discrepancy_id=f"D-{disc_index:03d}",
                    validation_id=validation_id,
                    category=candidate.category,
                    subcategory=candidate.subcategory,
                    severity=severity,
                    classification_confidence=confidence,
                    status="OPEN",
                    source_location=candidate.analysis_path,
                    target_location=candidate.analysis_path,
                    source_expression=candidate.source_expression,
                    target_expression=candidate.target_expression,
                    affected_output_columns=[],
                    affected_row_count=affected_rows,
                    affected_percentage=affected_pct,
                    evidence=typed_evidences,
                    validator_checks=validator_checks,
                    classification_method=candidate.classification_method,
                    classification_reason=classification_reason,
                    analysis_path=candidate.analysis_path,
                    discrepancy_signature=sig_hash,
                    created_at=created_at,
                )
            )
            disc_index += 1

        return discrepancies
