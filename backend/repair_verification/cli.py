"""CLI runner for Phase 8 Repair Execution & Deterministic Re-Validation Engine."""

from __future__ import annotations

import argparse
import sys

from backend.repair_verification.models import VerificationStatus
from backend.repair_verification.service import RepairVerificationService


def main() -> None:
    """CLI entry point: python -m backend.repair_verification.cli verify --repair-id <repair_id>."""
    parser = argparse.ArgumentParser(description="MIGRA-Q Phase 8 Repair Verification Engine")
    subparsers = parser.add_subparsers(dest="command")

    verify_parser = subparsers.add_parser("verify", help="Verify a proposed repair candidate")
    verify_parser.add_argument("--repair-id", required=True, help="Phase 7 Repair Proposal ID")
    verify_parser.add_argument("--discrepancy-id", help="Targeted Discrepancy ID")
    verify_parser.add_argument("--target-dialect", default="bigquery", help="Target SQL dialect")

    args = parser.parse_args()

    if args.command != "verify":
        parser.print_help()
        sys.exit(1)

    try:
        result = RepairVerificationService.verify_repair(
            repair_id=args.repair_id,
            discrepancy_id=args.discrepancy_id,
            target_dialect=args.target_dialect,
        )

        out_summary = result.outcomes[0] if result.outcomes else None
        disc_category = out_summary.summary if out_summary else "BOUNDARY_CONDITION"

        print("MIGRA-Q REPAIR VERIFICATION")
        print("===========================")
        print("")
        print(f"Repair:\n{result.repair_id}\n")
        print(f"Target discrepancy:\n{result.discrepancy_id}\n{disc_category}\n")
        print(f"BEFORE\n------\nAffected rows: {result.affected_rows_before:,}\n")
        print(f"AFTER\n-----\nAffected rows: {result.affected_rows_after:,}\n")
        print(f"Reduction:\n{result.reduction_percentage:.2f}%\n")
        print(f"New discrepancies:\n{result.new_discrepancy_count}\n")
        print(f"Remaining discrepancies:\n{result.remaining_discrepancy_count}\n")
        print(f"Status:\n{result.status.value}\n")

        print("Evidence:")
        if result.status == VerificationStatus.VERIFIED:
            print("✓ Original discrepancy disappeared")
            print("✓ No new discrepancies introduced")
            print("✓ Dataset unchanged")
            print("✓ Validation configuration unchanged")
            print("✓ Repair artifact matched")
        elif result.status == VerificationStatus.CANDIDATE_REJECTED:
            print(f"✗ Candidate repair rejected: {result.metadata.rejection_reason}")
        elif result.status == VerificationStatus.NEW_DISCREPANCIES:
            print(f"✗ Repair introduced {result.new_discrepancy_count} new discrepancy regressions")
        elif result.status == VerificationStatus.PARTIALLY_RESOLVED:
            print(f"~ Discrepancy partially improved ({result.reduction_percentage:.2f}% reduction)")
        else:
            print(f"✗ Verification failed: {result.summary}")

    except Exception as e:
        print(f"Error executing repair verification: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
