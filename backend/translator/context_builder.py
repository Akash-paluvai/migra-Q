"""Context builder module — transforms Phase 1 SQLAnalysis into TranslationContext."""

from __future__ import annotations

import hashlib
import json

from backend.analyzer.service import analyze
from backend.core.config import settings
from backend.translator.models import TranslationContext, TranslationRequest


def build_translation_context(request: TranslationRequest) -> TranslationContext:
    """Analyze source SQL and build structured TranslationContext."""
    # Analyze source SQL with explicit source_dialect
    analysis = analyze(sql=request.source_sql, dialect=request.source_dialect)

    tables_dict = [t.model_dump() for t in analysis.tables]
    columns_dict = [c.model_dump() for c in analysis.columns]
    joins_dict = [j.model_dump() for j in analysis.joins]
    filters_dict = [f.model_dump() for f in analysis.filters]
    aggs_dict = [a.model_dump() for a in analysis.aggregations]
    cases_dict = [c.model_dump() for c in analysis.case_expressions]
    rules_dict = [r.model_dump() for r in analysis.business_rules]
    nulls_dict = [n.model_dump() for n in analysis.null_sensitive_expressions]

    schema_dict = request.schema_context.model_dump() if request.schema_context else None

    # Compute deterministic translation_context_hash
    hash_payload = {
        "source_sql": request.source_sql.strip(),
        "source_dialect": request.source_dialect.lower(),
        "target_dialect": request.target_dialect.lower(),
        "normalized_sql": analysis.normalized_sql,
        "tables": tables_dict,
        "columns": columns_dict,
        "joins": joins_dict,
        "filters": filters_dict,
        "aggregations": aggs_dict,
        "business_rules": rules_dict,
        "case_expressions": cases_dict,
        "null_sensitive": nulls_dict,
        "schema": schema_dict,
        "prompt_version": settings.PROMPT_VERSION,
    }

    serialized = json.dumps(hash_payload, sort_keys=True)
    context_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]

    return TranslationContext(
        source_sql=request.source_sql,
        normalized_sql=analysis.normalized_sql,
        source_dialect=request.source_dialect,
        target_dialect=request.target_dialect,
        tables=tables_dict,
        columns=columns_dict,
        joins=joins_dict,
        filters=filters_dict,
        aggregations=aggs_dict,
        business_rules=rules_dict,
        case_expressions=cases_dict,
        null_sensitive_expressions=nulls_dict,
        dataset_id=request.dataset_id,
        schema=request.schema_context,
        context_hash=context_hash,
    )
