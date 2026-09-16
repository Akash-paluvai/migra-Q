"""Semantic Name Resolution layer.

Binds the parsed AST against a physical dataset schema using sqlglot's 
built-in scope analysis and qualification utilities.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

import sqlglot
from sqlglot import exp
from sqlglot.optimizer.qualify import qualify
from sqlglot.errors import OptimizeError

from backend.datasets.registry import DatasetRegistry


@dataclass
class SemanticDiagnostic:
    severity: str
    code: str
    message: str
    available_columns: Dict[str, List[str]] | None = None


def build_sqlglot_schema(dataset_id: str) -> Dict[str, Dict[str, str]]:
    """Builds a sqlglot-compatible schema dict from the dataset."""
    registry = DatasetRegistry()
    dataset = registry.get_dataset(dataset_id)
    if not dataset:
        return {}

    schema_dict = {}
    for table in dataset.table_summaries:
        t_name = table.table_name.lower()
        schema_dict[t_name] = {c.name.lower(): c.data_type for c in table.columns}
    
    return schema_dict


def resolve_semantics(ast: exp.Expression, dialect: str, dataset_id: str) -> List[SemanticDiagnostic]:
    """
    Run sqlglot's qualification optimizer to perform semantic name resolution.
    
    Returns a list of SemanticDiagnostic objects if resolution fails.
    Returns an empty list if resolution succeeds.
    """
    schema = build_sqlglot_schema(dataset_id)
    
    if not schema:
        return [SemanticDiagnostic(
            severity="ERROR",
            code="DATASET_NOT_FOUND",
            message=f"Dataset '{dataset_id}' could not be loaded for semantic resolution."
        )]

    try:
        # sqlglot.optimizer.qualify handles scope building, CTE resolution, alias resolution,
        # and physical column binding. 
        # validate_qualify_columns=True ensures it strictly errors on missing identifiers.
        qualify(
            ast, 
            dialect=dialect.lower(), 
            schema=schema, 
            validate_qualify_columns=True
        )
        return []
    except OptimizeError as e:
        error_msg = str(e)
        
        # Heuristically classify the error based on sqlglot's standard messages
        if "Unknown table" in error_msg:
            code = "UNKNOWN_TABLE"
        elif "Unknown column" in error_msg:
            code = "INPUT_SCHEMA_MISMATCH"
        elif "could not be resolved" in error_msg:
            # Often happens with unqualified columns or ambiguous columns
            if "Ambiguous column" in error_msg:
                code = "AMBIGUOUS_COLUMN"
            else:
                code = "UNKNOWN_COLUMN"
        else:
            code = "SEMANTIC_ERROR"

        available_cols = {}
        for tbl, cols in schema.items():
            available_cols[tbl] = list(cols.keys())

        return [SemanticDiagnostic(
            severity="ERROR",
            code=code,
            message=error_msg,
            available_columns=available_cols
        )]
