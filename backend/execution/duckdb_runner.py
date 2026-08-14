import duckdb
import pandas as pd
from typing import Any, Dict, List, Optional
from backend.core.exceptions import ExecutionSandboxException
from backend.core.logging import logger


class DuckDBRunner:
    """Embedded in-memory DuckDB runner for high-performance query validation."""

    def __init__(self):
        self.conn = duckdb.connect(database=":memory:")

    def register_dataset(self, table_name: str, data: List[Dict[str, Any]] | pd.DataFrame) -> None:
        """Register a Python dictionary list or DataFrame as a DuckDB table."""
        try:
            if isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                df = data
            self.conn.register(table_name, df)
            logger.info(f"Registered table '{table_name}' with {len(df)} rows in DuckDB sandbox")
        except Exception as e:
            raise ExecutionSandboxException(f"Failed to register table {table_name}: {str(e)}")

    def execute_query(self, sql: str) -> pd.DataFrame:
        """Execute query in DuckDB and return DataFrame result."""
        try:
            return self.conn.execute(sql).df()
        except Exception as e:
            logger.error(f"DuckDB execution error: {str(e)}")
            raise ExecutionSandboxException(f"Query execution error: {str(e)}")

    def close(self) -> None:
        """Close memory connection."""
        self.conn.close()
