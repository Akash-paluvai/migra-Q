import pandas as pd
import uuid
from backend.core.models import ValidationPipelineResult
from backend.validation.schema import SchemaValidator
from backend.validation.rows import RowValidator
from backend.validation.aggregates import AggregateValidator
from backend.validation.business_rules import BusinessRulesValidator
from backend.validation.edge_cases import EdgeCaseValidator


class ValidationOrchestrator:
    """Master Orchestrator executing the 5-stage validation pipeline."""

    @staticmethod
    def run_pipeline(
        source_df: pd.DataFrame,
        target_df: pd.DataFrame,
        migration_id: str = ""
    ) -> ValidationPipelineResult:
        if not migration_id:
            migration_id = str(uuid.uuid4())

        schema_res = SchemaValidator.validate(source_df, target_df)
        row_res = RowValidator.validate(source_df, target_df)
        agg_res = AggregateValidator.validate(source_df, target_df)
        rules_res = BusinessRulesValidator.validate(source_df, target_df)
        edge_res = EdgeCaseValidator.validate(source_df, target_df)

        passed = (
            schema_res.passed
            and row_res.passed
            and agg_res.passed
            and all(r.passed for r in rules_res)
            and edge_res.null_handling_passed
            and edge_res.floating_point_passed
        )

        score = 100.0 if passed else 50.0

        return ValidationPipelineResult(
            migration_id=migration_id,
            passed=passed,
            schema_check=schema_res,
            row_check=row_res,
            aggregate_check=agg_res,
            business_rules_check=rules_res,
            edge_cases_check=edge_res,
            overall_confidence_score=score
        )
