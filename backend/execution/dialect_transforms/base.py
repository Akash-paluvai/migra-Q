"""Base class and models for dialect-specific DuckDB compatibility adapters.

Defines the formal capability/confidence contract:
- SemanticConfidence: how confident we are in a transformation
- CompatibilityResult: per-node result from an adapter
- CompatibilityAnalysis: aggregate result from the full AST walk
- DialectCompatibilityAdapter: base class for all dialect adapters
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import sqlglot.expressions as exp


class SemanticConfidence(str, Enum):
    """Semantic risk ordering: EXACT < SAFE_EQUIVALENT < APPROXIMATION < UNKNOWN.

    Higher = greater semantic risk, not greater confidence.
    Aggregate across transforms = max(all confidences).
    """

    EXACT = "EXACT"
    SAFE_EQUIVALENT = "SAFE_EQUIVALENT"
    APPROXIMATION = "APPROXIMATION"
    UNKNOWN = "UNKNOWN"

    @staticmethod
    def risk_order(conf: "SemanticConfidence") -> int:
        return {
            SemanticConfidence.EXACT: 0,
            SemanticConfidence.SAFE_EQUIVALENT: 1,
            SemanticConfidence.APPROXIMATION: 2,
            SemanticConfidence.UNKNOWN: 3,
        }[conf]

    def __lt__(self, other: "SemanticConfidence") -> bool:
        return SemanticConfidence.risk_order(self) < SemanticConfidence.risk_order(other)

    def __gt__(self, other: "SemanticConfidence") -> bool:
        return SemanticConfidence.risk_order(self) > SemanticConfidence.risk_order(other)

    def __le__(self, other: "SemanticConfidence") -> bool:
        return SemanticConfidence.risk_order(self) <= SemanticConfidence.risk_order(other)

    def __ge__(self, other: "SemanticConfidence") -> bool:
        return SemanticConfidence.risk_order(self) >= SemanticConfidence.risk_order(other)


@dataclass
class CompatibilityResult:
    """Per-node result from a dialect adapter's transform() method."""

    executable: bool
    confidence: SemanticConfidence
    transformed_node: exp.Expression
    diagnostics: list[dict] = field(default_factory=list)


@dataclass
class CompatibilityAnalysis:
    """Aggregate result from the full AST compatibility analysis.

    Produced by analyze_and_transform() in __init__.py.
    Consumed by duckdb_runner.py to decide whether to execute.
    """

    transformed_ast: exp.Expression
    aggregate_confidence: SemanticConfidence
    executable: bool
    diagnostics: list[dict] = field(default_factory=list)


class DialectCompatibilityAdapter:
    """Base class for dialect-specific DuckDB compatibility adapters.

    Subclasses override ``transform`` to rewrite AST nodes that SQLGlot's
    generic ``dialect -> duckdb`` transpilation cannot handle correctly.

    Each transform must return a CompatibilityResult declaring:
    - Whether the result is executable by DuckDB
    - The semantic confidence of the transformation
    - Structured diagnostics for any capability gaps
    """

    @staticmethod
    def transform(node: exp.Expression) -> CompatibilityResult:
        """Transform a single AST node for DuckDB compatibility.

        Returns the node unchanged with EXACT confidence if no
        transformation applies.
        """
        return CompatibilityResult(
            executable=True,
            confidence=SemanticConfidence.EXACT,
            transformed_node=node,
        )
