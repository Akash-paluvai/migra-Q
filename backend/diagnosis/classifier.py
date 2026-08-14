from backend.core.models import MismatchClassification, ValidationPipelineResult


class MismatchClassifier:
    """Classifies root causes of validation mismatches based on 5-stage pipeline outputs."""

    @staticmethod
    def classify(val_result: ValidationPipelineResult) -> list[MismatchClassification]:
        classifications = []

        if not val_result.schema_check.passed:
            classifications.append(
                MismatchClassification(
                    mismatch_type="SCHEMA_MISMATCH",
                    severity="HIGH",
                    description=f"Missing columns: {val_result.schema_check.missing_columns}",
                    affected_nodes=val_result.schema_check.missing_columns,
                    root_cause_explanation="Column projection or naming dialect divergence between source and target."
                )
            )

        if not val_result.row_check.passed:
            classifications.append(
                MismatchClassification(
                    mismatch_type="ROW_DATA_DRIFT",
                    severity="HIGH",
                    description=f"Row count disparity or content hashing mismatch ({val_result.row_check.mismatched_row_count} rows differ).",
                    affected_nodes=[],
                    root_cause_explanation="Filter conditions (WHERE clause), JOIN semantics (INNER vs LEFT), or NULL filtering differ."
                )
            )

        if not val_result.edge_cases_check.null_handling_passed:
            classifications.append(
                MismatchClassification(
                    mismatch_type="NULL_SEMANTICS_DIVERGENCE",
                    severity="MEDIUM",
                    description="Null handling behavior differs between source and target dialect.",
                    affected_nodes=[],
                    root_cause_explanation="NVL / ISNULL / COALESCE logic or NULL sorting behavior differs across database engines."
                )
            )

        return classifications
