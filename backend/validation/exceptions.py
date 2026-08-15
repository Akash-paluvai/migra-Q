"""Validation module exception hierarchy."""

from backend.core.exceptions import MigraQError


class ValidationError(MigraQError):
    """Base exception for semantic validation errors."""


class ValidatorNotFoundError(ValidationError):
    """Raised when an requested validator is not found in the registry."""


class InvalidContextError(ValidationError):
    """Raised when the validation context lacks required inputs."""


class ComparisonKeyError(ValidationError):
    """Raised when a required comparison key is missing or invalid."""
