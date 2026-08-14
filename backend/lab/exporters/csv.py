"""CSV exporter — optional export of DataFrames to CSV files."""

from pathlib import Path

import pandas as pd


def export_to_csv(dfs: dict[str, pd.DataFrame], output_dir: Path) -> dict[str, str]:
    """Export a dictionary of {table_name: DataFrame} to output_dir as CSV files.

    Returns:
        file_names dict
    """
    csv_dir = output_dir / "csv"
    csv_dir.mkdir(parents=True, exist_ok=True)
    file_names = {}

    for table_name, df in dfs.items():
        file_path = csv_dir / f"{table_name}.csv"
        df.to_csv(file_path, index=False)
        file_names[table_name] = f"csv/{table_name}.csv"

    return file_names
