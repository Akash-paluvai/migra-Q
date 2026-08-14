"""Command line interface for Phase 2 Synthetic Migration Laboratory."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from backend.lab.config import GENERATOR_VERSION, SCHEMA_VERSION
from backend.lab.exporters.csv import export_to_csv
from backend.lab.exporters.parquet import export_to_parquet
from backend.lab.generators.dataset_builder import build_base_dataset
from backend.lab.models import ALL_SCHEMAS, DatasetManifest
from backend.lab.scenarios.registry import get_scenario, list_all_scenarios
from backend.lab.validation.integrity import compute_dataset_profile, validate_dataset_integrity


def cmd_generate(args: argparse.Namespace) -> None:
    """Generate base synthetic dataset with specified profile and seed."""
    profile_name = args.profile
    seed = args.seed
    out_dir = Path(args.out_dir or f"datasets/generated/{profile_name}")

    print(f"Generating synthetic dataset: profile='{profile_name}', seed={seed}...")

    dfs = build_base_dataset(seed=seed, profile_name=profile_name)
    row_counts = {name: len(df) for name, df in dfs.items()}

    # Export Parquet
    file_names, checksums = export_to_parquet(dfs, out_dir)

    # Export optional CSV
    if args.csv:
        export_to_csv(dfs, out_dir)

    # Generate manifest
    dataset_id = f"{profile_name}_{seed}"
    manifest = DatasetManifest(
        dataset_id=dataset_id,
        generator_version=GENERATOR_VERSION,
        schema_version=SCHEMA_VERSION,
        seed=seed,
        profile=profile_name,
        generation_timestamp=datetime.now(timezone.utc).isoformat(),
        row_counts=row_counts,
        table_schemas=ALL_SCHEMAS,
        scenario_ids=[],
        file_names=file_names,
        checksums=checksums,
    )

    manifest_path = out_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(manifest.model_dump_json(indent=2))

    print(f"Dataset successfully generated at {out_dir}")
    print(f"Manifest written to {manifest_path}")
    print(f"Row counts: {row_counts}")


def cmd_generate_scenario(args: argparse.Namespace) -> None:
    """Generate specific benchmark scenario dataset."""
    scenario_id = args.scenario_id
    seed = args.seed
    out_dir = Path(args.out_dir or f"datasets/scenarios/{scenario_id}")

    print(f"Generating scenario '{scenario_id}': seed={seed}...")
    scenario = get_scenario(scenario_id)
    dfs = scenario.generate(seed=seed, profile_name=args.profile)

    row_counts = {name: len(df) for name, df in dfs.items()}

    file_names, checksums = export_to_parquet(dfs, out_dir)

    manifest = DatasetManifest(
        dataset_id=f"{scenario_id}_{seed}",
        generator_version=GENERATOR_VERSION,
        schema_version=SCHEMA_VERSION,
        seed=seed,
        profile=args.profile,
        generation_timestamp=datetime.now(timezone.utc).isoformat(),
        row_counts=row_counts,
        table_schemas=ALL_SCHEMAS,
        scenario_ids=[scenario_id],
        file_names=file_names,
        checksums=checksums,
    )

    manifest_path = out_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(manifest.model_dump_json(indent=2))

    print(f"Scenario dataset successfully generated at {out_dir}")
    print(f"Manifest written to {manifest_path}")
    print(f"Row counts: {row_counts}")


def cmd_validate_dataset(args: argparse.Namespace) -> None:
    """Validate dataset integrity given a manifest file."""
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"Error: Manifest file not found: {manifest_path}", file=sys.stderr)
        sys.exit(1)

    dataset_dir = manifest_path.parent
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    manifest = DatasetManifest.model_validate(manifest_data)
    print(f"Validating dataset '{manifest.dataset_id}' in {dataset_dir}...")

    # Load tables from Parquet files
    dfs = {}
    for table_name, file_name in manifest.file_names.items():
        parquet_path = dataset_dir / file_name
        if parquet_path.exists():
            dfs[table_name] = pd.read_parquet(parquet_path)
        else:
            print(f"Warning: Table file missing: {parquet_path}", file=sys.stderr)

    result = validate_dataset_integrity(dfs)

    print("\nDataset Integrity Validation Results:")
    print("-------------------------------------")
    print(f"Status: {'PASSED' if result['is_valid'] else 'FAILED'}")
    for check_name, status in result["checks"].items():
        print(f"  - {check_name}: {'OK' if status else 'FAIL'}")

    if result["violations"]:
        print("\nViolations:")
        for v in result["violations"]:
            print(f"  ! {v}")

    if not result["is_valid"]:
        sys.exit(1)


def cmd_profile(args: argparse.Namespace) -> None:
    """Generate statistical profile for a dataset given its manifest."""
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"Error: Manifest file not found: {manifest_path}", file=sys.stderr)
        sys.exit(1)

    dataset_dir = manifest_path.parent
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    manifest = DatasetManifest.model_validate(manifest_data)

    dfs = {}
    for table_name, file_name in manifest.file_names.items():
        parquet_path = dataset_dir / file_name
        if parquet_path.exists():
            dfs[table_name] = pd.read_parquet(parquet_path)

    stats = compute_dataset_profile(manifest.dataset_id, dfs)
    print(json.dumps(stats.model_dump(), indent=2))


def cmd_list_scenarios(args: argparse.Namespace) -> None:
    """List all registered benchmark scenarios."""
    scenarios = list_all_scenarios()
    print(f"\nRegistered Benchmark Scenarios ({len(scenarios)} total):\n")
    print(f"{'ID':<25} {'CATEGORY':<20} {'NAME'}")
    print("-" * 75)
    for s in scenarios:
        print(f"{s.scenario_id:<25} {s.category:<20} {s.name}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 2 Synthetic Migration Laboratory CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # generate
    p_gen = subparsers.add_parser("generate", help="Generate a fresh synthetic dataset profile")
    p_gen.add_argument(
        "--profile",
        default="dev",
        choices=["dev", "demo"],
        help="Dataset scale profile (default: dev)",
    )
    p_gen.add_argument(
        "--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)"
    )
    p_gen.add_argument("--out-dir", default=None, help="Output directory path")
    p_gen.add_argument("--csv", action="store_true", help="Also export optional CSV files")

    # generate-scenario
    p_scen = subparsers.add_parser(
        "generate-scenario", help="Generate a specific benchmark scenario dataset"
    )
    p_scen.add_argument("scenario_id", help="ID of the benchmark scenario")
    p_scen.add_argument("--profile", default="dev", choices=["dev", "demo"], help="Base profile")
    p_scen.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    p_scen.add_argument("--out-dir", default=None, help="Output directory path")

    # validate-dataset
    p_val = subparsers.add_parser("validate-dataset", help="Validate dataset integrity")
    p_val.add_argument("manifest", help="Path to dataset manifest.json")

    # profile
    p_prof = subparsers.add_parser(
        "profile", help="Generate machine-readable statistics for dataset"
    )
    p_prof.add_argument("manifest", help="Path to dataset manifest.json")

    # list-scenarios
    subparsers.add_parser("list-scenarios", help="List all available benchmark scenarios")

    args = parser.parse_args()

    if args.command == "generate":
        cmd_generate(args)
    elif args.command == "generate-scenario":
        cmd_generate_scenario(args)
    elif args.command == "validate-dataset":
        cmd_validate_dataset(args)
    elif args.command == "profile":
        cmd_profile(args)
    elif args.command == "list-scenarios":
        cmd_list_scenarios(args)


if __name__ == "__main__":
    main()
