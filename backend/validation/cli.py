"""CLI tool for running and inspecting MIGRA-Q semantic validation."""

import argparse
import json
import sys

from backend.validation.helpers import format_validation_summary
from backend.validation.models import ValidationConfig
from backend.validation.service import ValidationService


def main() -> None:
    parser = argparse.ArgumentParser(description="MIGRA-Q Semantic Validation CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # run command
    run_parser = subparsers.add_parser(
        "run", help="Run semantic validation between two Phase 3 executions"
    )
    run_parser.add_argument("--source-execution", required=True, help="Source execution ID")
    run_parser.add_argument("--target-execution", required=True, help="Target execution ID")
    run_parser.add_argument(
        "--comparison-key", default="customer_id", help="Primary key column(s) comma separated"
    )
    run_parser.add_argument("--json", action="store_true", help="Output raw JSON ValidationReport")

    # inspect command
    inspect_parser = subparsers.add_parser("inspect", help="Inspect a completed ValidationReport")
    inspect_parser.add_argument("--validation-id", required=True, help="Validation ID to inspect")

    args = parser.parse_args()

    if args.command == "run":
        keys = [k.strip() for k in args.comparison_key.split(",") if k.strip()]
        config = ValidationConfig(comparison_key=keys)

        try:
            report = ValidationService.validate_executions(
                source_execution_id=args.source_execution,
                target_execution_id=args.target_execution,
                config=config,
            )
            report_dict = report.model_dump()
            if args.json:
                print(json.dumps(report_dict, indent=2))
            else:
                print(format_validation_summary(report_dict))
        except Exception as exc:
            print(f"Validation failed: {exc}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "inspect":
        report = ValidationService.get_validation(args.validation_id)
        if not report:
            print(f"Validation ID '{args.validation_id}' not found.", file=sys.stderr)
            sys.exit(1)

        print(json.dumps(report.model_dump(), indent=2))


if __name__ == "__main__":
    main()
