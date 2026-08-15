"""Base class for deterministic rule classifiers."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from backend.diagnosis.models import ClassificationMethod, DiscrepancyCategory
from backend.diagnosis.signals import RawDiscrepancySignal


class ClassificationCandidate(BaseModel):
    """Candidate result produced by a rule classifier."""

    category: DiscrepancyCategory
    subcategory: str | None = None
    priority: int
    source_expression: str | None = None
    target_expression: str | None = None
    analysis_path: str = ""
    classification_method: ClassificationMethod = ClassificationMethod.COMBINED_DETERMINISTIC
    reason_template: str = ""
    payload: dict[str, Any] = {}


class BaseRuleClassifier(ABC):
    """Abstract base class for rule classifiers in the classifier registry."""

    @property
    @abstractmethod
    def priority(self) -> int:
        """Priority rank (1 = highest priority)."""
        pass

    @property
    @abstractmethod
    def category(self) -> DiscrepancyCategory:
        """Target primary discrepancy category."""
        pass

    @abstractmethod
    def matches(self, signal: RawDiscrepancySignal, signals: list[RawDiscrepancySignal]) -> bool:
        """Check if signal(s) match this classifier's deterministic criteria."""
        pass

    @abstractmethod
    def classify(
        self, signal: RawDiscrepancySignal, signals: list[RawDiscrepancySignal]
    ) -> ClassificationCandidate:
        """Produce a ClassificationCandidate for matching signals."""
        pass
