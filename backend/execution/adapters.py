from abc import ABC, abstractmethod
import pandas as pd
from backend.core.models import Dialect


class BaseDBAdapter(ABC):
    """Abstract interface for database connection adapters."""

    @abstractmethod
    def fetch_data(self, query: str) -> pd.DataFrame:
        pass


class MockAdapter(BaseDBAdapter):
    """Fallback mock adapter for standalone sandbox mode."""

    def __init__(self, dialect: Dialect):
        self.dialect = dialect

    def fetch_data(self, query: str) -> pd.DataFrame:
        return pd.DataFrame({"id": [1, 2], "val": [100.0, 200.0]})


class DatabaseAdapterFactory:
    """Factory creating engine-specific database adapters."""

    @staticmethod
    def get_adapter(dialect: Dialect, connection_string: str = "") -> BaseDBAdapter:
        return MockAdapter(dialect)
