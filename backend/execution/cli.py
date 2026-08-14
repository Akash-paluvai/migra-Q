"""Command line interface for Phase 3 Deterministic SQL Execution Engine."""

import argparse
import json
import sys
from pathlib import Path

from backend.execution.models import ExecutionRequest
from backend.execution.service import ExecutionService


def cmd_run(args: argparse.Namespace) -> None:
    """Run a single SQL file against a dataset."""
    sql_path = Path(args.sql)
    if not sql_path.exists():
        print(f"Error: SQL file not found: {sql_path}", file=sys.stderr)
        sys.exit(1)

    sql = sql_path.read_text(encoding="utf-8").strip()
    req = ExecutionRequest(
        sql=sql,
        dataset_id=args.dataset,
        dataset_dir=args.dataset if Path(args.dataset).is_dir() else None,
        execution_mode=args.mode,
    )

    print(f"Executing query from '{sql_path}' against dataset '{args.dataset}'...")
    res = ExecutionService.execute(req)

    print("\nEXECUTION RESULT")
    print("────────────────────────────────────────")
    print(f"Execution ID : {res.execution_id}")
    print(f"Status       : {res.status}")
    print(f"Query Hash   : {res.query_hash}")
    print(f"Dataset Hash : {res.dataset_hash}")
    print(f"Duration (ms): {res.duration_ms}")
    print(f"Row Count    : {res.row_count}")

    if res.columns:
        print("\nSchema:")
        for col in res.columns:
            print(f"  - {col.name}: {col.type}")

    if res.result_artifact:
        print(f"\nResult Artifact: {res.result_artifact}")

    if res.error_message:
        print(f"\nError [{res.error_code}]: {res.error_message}")


def cmd_inspect(args: argparse.Namespace) -> None:
    """Inspect execution metadata by ID."""
    exec_id = args.execution_id
    res = ExecutionService.get_execution(exec_id)
    if not res:
        print(f"Error: Execution '{exec_id}' not found.", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(res.model_dump(), indent=2))


def cmd_compare_inputs(args: argparse.Namespace) -> None:
    """Execute source and target SQL candidates independently.

    Does NOT calculate semantic equivalence (Phase 4).
    """
    src_path = Path(args.source)
    tgt_path = Path(args.target)

    if not src_path.exists():
        print(f"Error: Source SQL file not found: {src_path}", file=sys.stderr)
        sys.exit(1)

    if not tgt_path.exists():
        print(f"Error: Target SQL file not found: {tgt_path}", file=sys.stderr)
        sys.exit(1)

    src_sql = src_path.read_text(encoding="utf-8").strip()
    tgt_sql = tgt_path.read_text(encoding="utf-8").strip()

    print(f"Executing Source & Target candidates against dataset '{args.dataset}'...\n")

    res_src, res_tgt = ExecutionService.compare_inputs(
        source_sql=src_sql,
        target_sql=tgt_sql,
        dataset_id=args.dataset,
    )

    print("========================================")
    print("SOURCE EXECUTION")
    print("========================================")
    print(f"Status      : {res_src.status}")
    print(f"Row Count   : {res_src.row_count}")
    print(f"Duration    : {res_src.duration_ms} ms")
    print(f"Query Hash  : {res_src.query_hash}")
    print(f"Artifact    : {res_src.result_artifact}")
    if res_src.error_message:
        print(f"Error       : {res_src.error_message}")

    print("\n========================================")
    print("TARGET EXECUTION")
    print("========================================")
    print(f"Status      : {res_tgt.status}")
    print(f"Row Count   : {res_tgt.row_count}")
    print(f"Duration    : {res_tgt.duration_ms} ms")
    print(f"Query Hash  : {res_tgt.query_hash}")
    print(f"Artifact    : {res_tgt.result_artifact}")
    if res_tgt.error_message:
        print(f"Error       : {res_tgt.error_message}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 3 Execution Engine CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # run
    p_run = subparsers.add_parser("run", help="Run a single SQL file against a dataset")
    p_run.add_argument("--sql", required=True, help="Path to SQL file")
    p_run.add_argument("--dataset", required=True, help="Dataset ID or directory path")
    p_run.add_argument(
        "--mode", default="SOURCE", choices=["SOURCE", "TARGET"], help="Execution mode"
    )

    # inspect
    p_insp = subparsers.add_parser("inspect", help="Inspect execution metadata by ID")
    p_insp.add_argument("--execution-id", required=True, help="Execution ID to inspect")

    # compare-inputs
    p_comp = subparsers.add_parser(
        "compare-inputs", help="Execute source and target candidates independently"
    )
    p_comp.add_argument("--source", required=True, help="Path to source SQL file")
    p_comp.add_argument("--target", required=True, help="Path to target SQL file")
    p_comp.add_argument("--dataset", required=True, help="Dataset ID or directory path")

    args = parser.parse_args()

    if args.command == "run":
        cmd_run(args)
    elif args.command == "inspect":
        cmd_inspect(args)
    elif args.command == "compare-inputs":
        cmd_compare_inputs(args)


if __name__ == "__main__":
    main()
