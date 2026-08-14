"""Execution module exception hierarchy."""

from backend.core.exceptions import MigraQError


class ExecutionError(MigraQError):
    """Base exception for query execution errors."""


class DatasetError(ExecutionError):
    """Raised when a dataset cannot be loaded or is invalid."""


class QueryTimeoutError(ExecutionError):
    """Raised when query execution exceeds the configured timeout."""


class SecurityViolationError(ExecutionError):
    """Raised when unsafe or mutating SQL is submitted."""


class ResultCaptureError(ExecutionError):
    """Raised when query result capture or artifact persistence fails."""
