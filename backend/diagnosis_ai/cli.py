"""Command Line Interface for Phase 7 AI Diagnosis & Repair Engine."""

from __future__ import annotations

import argparse
import sys

from backend.diagnosis_ai.service import DiagnosisAIService


def main() -> None:
    """Run CLI command for Phase 7 AI Diagnosis."""
    parser = argparse.ArgumentParser(description="MIGRA-Q AI Diagnosis & Repair Proposal CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    diag_parser = subparsers.add_parser("diagnose", help="Diagnose discrepancy and propose candidate repair")
    diag_parser.add_argument("--discrepancy-id", default="D-001", help="Discrepancy ID (e.g. D-001)")
    diag_parser.add_argument("--category", default="BOUNDARY_CONDITION", help="Discrepancy category")
    diag_parser.add_argument("--severity", default="HIGH", help="Discrepancy severity")
    diag_parser.add_argument("--source-expression", default="t.amount > 500", help="Source expression")
    diag_parser.add_argument("--target-expression", default="t.amount >= 500", help="Target expression")
    diag_parser.add_argument("--path", default="columns[risk_class]", help="Analysis path")
    diag_parser.add_argument("--affected-rows", type=int, default=10512, help="Affected row count")
    diag_parser.add_argument("--affected-pct", type=float, default=10.51, help="Affected percentage")
    diag_parser.add_argument(
        "--provider",
        choices=["mock", "openai"],
        default="mock",
        help="Provider choice",
    )
    diag_parser.add_argument(
        "--mock-mode",
        default="MOCK_BOUNDARY_REPAIR",
        help="Mock mode scenario name",
    )

    args = parser.parse_args()

    # Flagship source SQL
    source_sql = """SELECT
  c.customer_id,
  c.customer_segment,
  SUM(t.amount) AS total_amount,
  CASE WHEN t.amount > 500.00 THEN 'HIGH_RISK' ELSE 'NORMAL' END AS risk_class
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.status = 'COMPLETED'
GROUP BY c.customer_id, c.customer_segment, t.amount;"""

    # Flagship candidate target SQL
    target_sql = """SELECT
  c.customer_id,
  c.customer_segment,
  SUM(t.amount) AS total_amount,
  CASE WHEN t.amount >= 500.00 THEN 'HIGH_RISK' ELSE 'NORMAL' END AS risk_class
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.status = 'COMPLETED'
GROUP BY c.customer_id, c.customer_segment, t.amount;"""

    example = {
        "customer_id": "C18291",
        "refund_amount": 500.00,
        "source_risk": "NORMAL",
        "target_risk": "HIGH_RISK",
    }

    try:
        res = DiagnosisAIService.diagnose_discrepancy(
            discrepancy_id=args.discrepancy_id,
            category=args.category,
            severity=args.severity,
            source_sql=source_sql,
            target_sql=target_sql,
            source_expression=args.source_expression,
            target_expression=args.target_expression,
            analysis_path=args.path,
            affected_row_count=args.affected_rows,
            affected_percentage=args.affected_pct,
            affected_columns=["risk_class"],
            representative_examples=[example],
            provider_name=args.provider,
            mock_mode=args.mock_mode,
        )
    except Exception as e:
        print(f"Error executing AI diagnosis: {e}", file=sys.stderr)
        sys.exit(1)

    print("MIGRA-Q AI DIAGNOSIS")
    print("====================")
    print(f"Discrepancy ID: {res.diagnosis.discrepancy_id}")
    print(f"Category      : {args.category}")
    print(f"Status        : {res.diagnosis.status.value}")
    print()
    print("Explanation:")
    print(f"  Observed Change : {res.diagnosis.observed_change}")
    print(f"  Likely Mechanism: {res.diagnosis.likely_mechanism}")
    print(f"  Possible Cause  : {res.diagnosis.possible_cause}")
    print(f"  Uncertainty     : {res.diagnosis.uncertainty}")
    print()

    print("Grounded Claims & Evidence Citations:")
    for claim in res.diagnosis.claims:
        refs_str = f"[{', '.join(claim.evidence_refs)}]" if claim.evidence_refs else "[UNGROUNDED]"
        print(f"  - {claim.text} {refs_str}")
    print(f"Diagnosis Confidence: {res.diagnosis.diagnosis_confidence:.2f}")
    print("------------------------------------------------")
    print()

    print("REPAIR PROPOSAL")
    print("===============")
    print(f"Status         : {res.repair_proposal.status.value}")
    print(f"Changed Region : {res.repair_proposal.changed_region}")
    print(f"Rationale      : {res.repair_proposal.rationale}")
    print(f"Expected Effect: {res.repair_proposal.expected_effect}")
    print(f"Repair Confidence: {res.repair_proposal.repair_confidence:.2f}")
    print()

    if res.repair_proposal.proposed_sql:
        print("Proposed Candidate Repair Target SQL:")
        print("-------------------------------------")
        print(res.repair_proposal.proposed_sql)
        print()

    print("IMPORTANT: Deterministic re-validation required (Phase 8).")


if __name__ == "__main__":
    main()
