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

class ProviderError(MigraQError):
    """Base exception for LLM provider errors."""
    
class NonRetryableProviderError(ProviderError):
    """Raised for provider errors that should fail immediately (e.g., HTTP 400)."""

class RateLimitError(ProviderError):
    """Raised when rate limits are exceeded (HTTP 429)."""
    def __init__(self, message: str, retry_after: float = 0.0, details: dict | None = None):
        super().__init__(message, details)
        self.retry_after = retry_after

class TransientProviderError(ProviderError):
    """Raised for transient provider issues (e.g., HTTP 5xx, timeouts)."""
