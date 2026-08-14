from typing import Any, Dict, List, Tuple
import pandas as pd
from backend.execution.duckdb_runner import DuckDBRunner


class ExecutionSandbox:
    """Isolated execution sandbox comparing source and target queries against test datasets."""

    @staticmethod
    def run_comparison(
        source_sql: str,
        target_sql: str,
        sample_tables: Dict[str, List[Dict[str, Any]]]
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Execute both source and target queries in isolated DuckDB runners and return DataFrames."""
        runner_source = DuckDBRunner()
        runner_target = DuckDBRunner()

        for table_name, data in sample_tables.items():
            runner_source.register_dataset(table_name, data)
            runner_target.register_dataset(table_name, data)

        source_df = runner_source.execute_query(source_sql)
        target_df = runner_target.execute_query(target_sql)

        runner_source.close()
        runner_target.close()

        return source_df, target_df
