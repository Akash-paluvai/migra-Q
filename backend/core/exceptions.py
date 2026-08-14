"""Application-specific exceptions."""


class MigraQError(Exception):
    """Base exception for all Migra-Q errors."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ParserError(MigraQError):
    """Raised when SQL parsing fails."""


class AnalyzerError(MigraQError):
    """Raised when SQL analysis encounters an unrecoverable problem."""
