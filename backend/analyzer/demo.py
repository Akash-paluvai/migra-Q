"""CLI demo — human-readable and JSON modes.

Usage:
    python -m backend.analyzer.demo examples/customer_risk.sql
    python -m backend.analyzer.demo examples/customer_risk.sql --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from backend.analyzer.service import analyze


def _print_human(a) -> None:  # noqa: ANN001 – type is SQLAnalysis
    print()
    print("MIGRA-Q SQL ANALYSIS")
    print("─" * 40)

    # Tables
    print()
    print("Tables")
    for t in a.tables:
        print(f"  {t}")

    # Joins
    if a.joins:
        print()
        print("Joins")
        for j in a.joins:
            print(f"  {j.id}")
            print(f"    {j.join_type}")
            print(f"    {j.condition}")

    # Filters
    if a.filters:
        print()
        print("Filters")
        for f in a.filters:
            print(f"  {f.id}")
            print(f"    {f.expression}")

    # Aggregations
    if a.aggregations:
        print()
        print("Aggregations")
        for ag in a.aggregations:
            label = f"{ag.function}({ag.expression})"
            if ag.distinct:
                label = f"{ag.function}(DISTINCT {ag.expression})"
            print(f"  {ag.id}")
            print(f"    {label}")

    # Business Rules
    if a.business_rules:
        print()
        print("Business Rules")
        for r in a.business_rules:
            cond = r.condition
            if cond.get("type") == "comparison":
                cond_str = f"{cond['left']} {cond['operator']} {cond['right']}"
            else:
                cond_str = cond.get("expression", str(cond))
            print(f"  {r.id}")
            print(f"    {cond_str}")
            print(f"    → {r.then}")
            if r.else_val:
                print(f"    → {r.else_val}")

    # NULL-sensitive
    print()
    null_flag = "YES" if a.null_sensitive_expressions else "NO"
    print("NULL-sensitive:")
    print(f"  {null_flag}")
    if a.null_sensitive_expressions:
        for ns in a.null_sensitive_expressions:
            print(f"    {ns.kind}: {ns.expression}")

    # Warnings
    if a.warnings:
        print()
        print("Warnings")
        for w in a.warnings:
            print(f"  [{w.code}] {w.message}")

    # Version
    print()
    print("Analysis version:")
    print(f"  {a.analyzer_version}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="MIGRA-Q SQL Analyzer")
    parser.add_argument("file", help="Path to a .sql file")
    parser.add_argument(
        "--dialect", default="teradata", help="Source SQL dialect (default: teradata)"
    )
    parser.add_argument(
        "--json",
        dest="output_json",
        action="store_true",
        help="Output JSON instead of human-readable",
    )
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    sql = path.read_text(encoding="utf-8").strip()
    if not sql:
        print("Error: file is empty", file=sys.stderr)
        sys.exit(1)

    result = analyze(sql, dialect=args.dialect)

    if args.output_json:
        print(json.dumps(result.model_dump(), indent=2, default=str))
    else:
        _print_human(result)


if __name__ == "__main__":
    main()
