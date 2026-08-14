class MigraQException(Exception):
    """Base exception for all Migra-Q system errors."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class TranslationException(MigraQException):
    """Raised when SQL dialect translation fails."""

    pass


class ParserException(MigraQException):
    """Raised when SQL syntax parsing fails."""

    pass


class ValidationException(MigraQException):
    """Raised when equivalence validation process encounters an unrecoverable failure."""

    pass


class ExecutionSandboxException(MigraQException):
    """Raised when DuckDB or target database execution encounters a query error."""

    pass


class RepairException(MigraQException):
    """Raised when SQL repair synthesis cannot produce a valid patch."""

    pass
