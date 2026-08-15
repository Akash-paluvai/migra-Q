"""Base abstract validator class."""

from abc import ABC, abstractmethod

from backend.validation.context import ValidationContext
from backend.validation.models import ValidationResult


class BaseValidator(ABC):
    """Abstract validator interface."""

    name: str

    @abstractmethod
    def validate(self, context: ValidationContext) -> ValidationResult:
        """Perform validation check against ValidationContext and return ValidationResult."""
        pass
