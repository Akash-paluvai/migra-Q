"""Command-line interface for Phase 6 Translation Engine."""

from __future__ import annotations

import argparse
import json
import sys

from backend.translator.models import SchemaContext, TranslationRequest
from backend.translator.service import TranslationService


def main() -> None:
    """CLI entry point for MIGRA-Q SQL translation."""
    parser = argparse.ArgumentParser(description="MIGRA-Q SQL Translation CLI Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    trans_parser = subparsers.add_parser(
        "translate", help="Translate source SQL to target candidate SQL"
    )
    trans_parser.add_argument("--input", "-i", required=True, help="Path to source SQL file")
    trans_parser.add_argument(
        "--source-dialect", default="teradata", help="Source SQL dialect (default: teradata)"
    )
    trans_parser.add_argument(
        "--target-dialect", default="bigquery", help="Target SQL dialect (default: bigquery)"
    )
    trans_parser.add_argument("--schema", help="Path to JSON file containing target SchemaContext")
    trans_parser.add_argument(
        "--provider", default="mock", help="Provider name ('openai' or 'mock')"
    )
    trans_parser.add_argument(
        "--mock-mode",
        default="MOCK_GOOD",
        help="Mock scenario mode ('MOCK_GOOD', 'MOCK_BOUNDARY_BUG', etc.)",
    )

    args = parser.parse_args()

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            source_sql = f.read()
    except Exception as e:
        print(f"Error reading input SQL file '{args.input}': {e}", file=sys.stderr)
        sys.exit(1)

    schema_ctx = None
    if args.schema:
        try:
            with open(args.schema, "r", encoding="utf-8") as f:
                raw_schema = json.load(f)
                schema_ctx = SchemaContext(**raw_schema)
        except Exception as e:
            print(f"Error reading schema context file '{args.schema}': {e}", file=sys.stderr)
            sys.exit(1)

    req = TranslationRequest(
        source_sql=source_sql,
        source_dialect=args.source_dialect,
        target_dialect=args.target_dialect,
        schema=schema_ctx,
    )

    res = TranslationService.translate(request=req, mock_mode=args.mock_mode)

    print("MIGRA-Q TRANSLATION")
    print("===================")
    print(f"Translation ID : {res.metadata.translation_id}")
    print(f"Source Dialect : {res.metadata.source_dialect}")
    print(f"Target Dialect : {res.metadata.target_dialect}")
    print(f"Status         : {res.status.value}")
    if res.candidate_validation_status:
        print(f"Candidate Check: {res.candidate_validation_status.value}")
    print(f"Semantic Status: {res.semantic_status}")
    print(f"Summary        : {res.validation_summary}")
    print()

    if res.structural_differences:
        print("Structural Differences:")
        for diff in res.structural_differences:
            print(f"  - {diff}")
        print()

    if res.response and res.response.target_sql:
        print("Target Candidate SQL:")
        print("---------------------")
        print(res.response.target_sql)
        print()

    if res.response and res.response.assumptions:
        print("Assumptions:")
        for a in res.response.assumptions:
            print(f"  - {a}")
        print()

    if res.response and res.response.potential_risks:
        print("Potential Risks:")
        for r in res.response.potential_risks:
            print(f"  - {r}")
        print()

    if res.response and res.response.translated_rules:
        print("Translated Rules:")
        for rule in res.response.translated_rules:
            print(f"  - [{rule.rule_type}] {rule.source_expression} -> {rule.target_expression}")
        print()


if __name__ == "__main__":
    main()
