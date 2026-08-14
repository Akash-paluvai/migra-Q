"""Scenarios package for benchmark and adversarial dataset generation."""

from backend.lab.scenarios.base import BaseScenario, ScenarioMetadata
from backend.lab.scenarios.registry import BENCHMARK_SCENARIOS, get_scenario, list_all_scenarios

__all__ = [
    "BaseScenario",
    "ScenarioMetadata",
    "BENCHMARK_SCENARIOS",
    "get_scenario",
    "list_all_scenarios",
]
