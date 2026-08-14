"""Parquet exporter — saves DataFrames as compact Parquet files and computes SHA-256 checksums."""

import hashlib
from pathlib import Path

import pandas as pd


def export_to_parquet(
    dfs: dict[str, pd.DataFrame], output_dir: Path
) -> tuple[dict[str, str], dict[str, str]]:
    """Export a dictionary of {table_name: DataFrame} to output_dir as Parquet.

    Returns:
        (file_names, sha256_checksums)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    file_names = {}
    checksums = {}

    for table_name, df in dfs.items():
        file_path = output_dir / f"{table_name}.parquet"
        df.to_parquet(file_path, index=False, engine="pyarrow")
        file_names[table_name] = f"{table_name}.parquet"

        # Compute SHA-256 checksum of the file
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        checksums[table_name] = sha256.hexdigest()

    return file_names, checksums
