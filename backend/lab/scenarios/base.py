"""Base class and metadata models for benchmark scenarios."""

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field


class ScenarioMetadata(BaseModel):
    scenario_id: str
    name: str
    category: str  # BOUNDARY, NULL, ZERO_NEGATIVE, DUPLICATE_KEYS, etc.
    description: str
    seed: int = 42
    base_profile: str = "dev"
    expected_behavior: str = ""
    affected_tables: list[str] = Field(default_factory=list)
    scenario_params: dict[str, Any] = Field(default_factory=dict)


class BaseScenario(ABC):
    """Abstract base class for all benchmark scenario generators."""

    def __init__(self, metadata: ScenarioMetadata):
        self.metadata = metadata

    @abstractmethod
    def generate(self, seed: int = 42, profile_name: str = "dev") -> dict[str, pd.DataFrame]:
        """Generate dataset containing the specific scenario conditions."""
        pass
