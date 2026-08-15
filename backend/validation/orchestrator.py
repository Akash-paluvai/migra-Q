"""Validation Orchestrator — executes independent validators and aggregates ValidationReport."""

import uuid
from datetime import datetime, timezone

from backend.validation.context import ValidationContext
from backend.validation.models import (
    VALIDATOR_VERSION,
    ValidationCheckStatus,
    ValidationReport,
    ValidationResult,
    ValidationSeverity,
)
from backend.validation.validators.aggregates import AggregateValidator
from backend.validation.validators.base import BaseValidator
from backend.validation.validators.business_rules import BusinessRuleValidator
from backend.validation.validators.edge_cases import EdgeCaseValidator
from backend.validation.validators.rows import RowValidator
from backend.validation.validators.schema import SchemaValidator


class ValidationOrchestrator:
    """Orchestrates independent validator execution and generates ValidationReport."""

    def __init__(self, validators: list[BaseValidator] | None = None):
        if validators is None:
            self.validators = [
                SchemaValidator(),
                RowValidator(),
                AggregateValidator(),
                BusinessRuleValidator(),
                EdgeCaseValidator(),
            ]
        else:
            self.validators = validators

    def validate(self, context: ValidationContext) -> ValidationReport:
        """Run all enabled validators independently and aggregate final report."""
        enabled_names = context.config.enabled_validators
        results: list[ValidationResult] = []

        summary_counts = {
            "checks_run": 0,
            "checks_passed": 0,
            "checks_warned": 0,
            "checks_failed": 0,
            "checks_errored": 0,
        }

        for v in self.validators:
            if enabled_names and v.name not in enabled_names:
                continue

            summary_counts["checks_run"] += 1
            try:
                res = v.validate(context)
            except Exception as exc:
                res = ValidationResult(
                    check_name=v.name,
                    validator_version=VALIDATOR_VERSION,
                    status=ValidationCheckStatus.ERROR,
                    severity=ValidationSeverity.HIGH,
                    score=0.0,
                    summary=f"Validator unexpected error: {exc}",
                )

            results.append(res)

            if res.status == ValidationCheckStatus.PASS:
                summary_counts["checks_passed"] += 1
            elif res.status == ValidationCheckStatus.WARN:
                summary_counts["checks_warned"] += 1
            elif res.status == ValidationCheckStatus.FAIL:
                summary_counts["checks_failed"] += 1
            elif res.status == ValidationCheckStatus.ERROR:
                summary_counts["checks_errored"] += 1

        # Determine overall_status aggregate
        if summary_counts["checks_failed"] > 0:
            overall_status = "FAIL"
        elif summary_counts["checks_errored"] > 0:
            overall_status = "ERROR"
        elif summary_counts["checks_warned"] > 0:
            overall_status = "WARN"
        else:
            overall_status = "PASS"

        val_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        return ValidationReport(
            validation_id=val_id,
            source_execution_id=context.source_execution.execution_id,
            target_execution_id=context.target_execution.execution_id,
            dataset_id=context.source_execution.dataset_id,
            created_at=created_at,
            validator_version=VALIDATOR_VERSION,
            checks=results,
            overall_status=overall_status,
            summary=summary_counts,
        )
