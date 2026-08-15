"""CLI tool for running MIGRA-Q discrepancy classification & evidence consolidation."""

import argparse
import json
import sys

from backend.diagnosis.helpers import format_discrepancy_summary
from backend.diagnosis.service import DiagnosisService


def main() -> None:
    parser = argparse.ArgumentParser(description="MIGRA-Q Discrepancy Classification CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # run command
    run_parser = subparsers.add_parser(
        "run", help="Run discrepancy classification on a ValidationReport"
    )
    run_parser.add_argument("--validation-id", required=True, help="Validation ID to diagnose")
    run_parser.add_argument("--json", action="store_true", help="Output raw JSON DiscrepancyReport")

    # get command
    get_parser = subparsers.add_parser("get", help="Retrieve a completed DiscrepancyReport")
    get_parser.add_argument("--diagnosis-id", required=True, help="Diagnosis ID to retrieve")

    args = parser.parse_args()

    if args.command == "run":
        try:
            report = DiagnosisService.diagnose_validation(validation_id=args.validation_id)
            report_dict = report.model_dump()
            if args.json:
                print(json.dumps(report_dict, indent=2))
            else:
                print(format_discrepancy_summary(report_dict))
        except Exception as exc:
            print(f"Diagnosis failed: {exc}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "get":
        report = DiagnosisService.get_diagnosis(args.diagnosis_id)
        if not report:
            print(f"Diagnosis ID '{args.diagnosis_id}' not found.", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(report.model_dump(), indent=2))


if __name__ == "__main__":
    main()
