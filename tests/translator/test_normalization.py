import pytest
from backend.translator.models import (
    TranslationResult,
    TranslationMetadata,
    TranslationStatus,
    TranslationResponse,
    StructuredRule
)


@pytest.fixture
def base_metadata() -> TranslationMetadata:
    return TranslationMetadata(
        translation_id="t-123",
        request_id="r-123",
        provider="mock",
        model="mock",
        source_dialect="oracle",
        target_dialect="snowflake",
        source_sql_hash="xyz",
        translation_context_hash="abc",
        prompt_hash="def",
        created_at="2026-08-18T00:00:00Z",
    )


def test_duplicate_rule_grouping(base_metadata):
    """Test that identical source/target mappings increment occurrences instead of duplicating."""
    response = TranslationResponse(
        target_sql="SELECT COALESCE(a, 0), COALESCE(b, 0)",
        translated_rules=[
            StructuredRule(source_path="path1", source_expression="NVL", target_expression="COALESCE", rule_type="mapping"),
            StructuredRule(source_path="path2", source_expression="NVL", target_expression="COALESCE", rule_type="mapping"),
        ]
    )
    result = TranslationResult(
        metadata=base_metadata,
        status=TranslationStatus.SUCCESS,
        response=response
    )
    
    assert result.transformation_count == 1
    t = result.transformations[0]
    assert t.source == "NVL"
    assert t.target == "COALESCE"
    assert t.occurrences == 2
    assert t.type == "TRANSLATED_RULE"


def test_zero_transformations(base_metadata):
    """Test behavior with absolutely no transformations."""
    response = TranslationResponse(
        target_sql="SELECT a",
        translated_rules=[]
    )
    result = TranslationResult(
        metadata=base_metadata,
        status=TranslationStatus.SUCCESS,
        response=response
    )
    
    assert result.transformation_count == 0
    assert result.transformations == []


def test_multiple_rules(base_metadata):
    """Test grouping of disparate mappings."""
    response = TranslationResponse(
        target_sql="SELECT CASE WHEN a THEN COALESCE(b, 0)",
        translated_rules=[
            StructuredRule(source_path="p1", source_expression="NVL", target_expression="COALESCE", rule_type="mapping"),
            StructuredRule(source_path="p2", source_expression="DECODE", target_expression="CASE", rule_type="mapping"),
        ]
    )
    result = TranslationResult(
        metadata=base_metadata,
        status=TranslationStatus.SUCCESS,
        response=response
    )
    
    assert result.transformation_count == 2
    sources = [t.source for t in result.transformations]
    assert "NVL" in sources
    assert "DECODE" in sources


def test_same_rule_across_different_sources(base_metadata):
    """Test that if the same mapping appears in diffs and translated rules, it deduplicates."""
    response = TranslationResponse(
        target_sql="SELECT COALESCE(a, 0)",
        translated_rules=[
            StructuredRule(source_path="p1", source_expression="NVL", target_expression="COALESCE", rule_type="mapping"),
        ]
    )
    # The structural diff also records NVL -> COALESCE
    result = TranslationResult(
        metadata=base_metadata,
        status=TranslationStatus.SUCCESS,
        response=response,
        structural_differences=["NVL -> COALESCE"]
    )
    
    assert result.transformation_count == 1
    t = result.transformations[0]
    assert t.source == "NVL"
    assert t.target == "COALESCE"
    assert t.occurrences == 1  # Should not double-count logical transformation across evidence sources


def test_assumptions_not_misinterpreted(base_metadata):
    """Verify assumptions don't get incorrectly parsed as function mappings."""
    response = TranslationResponse(
        target_sql="SELECT a",
        assumptions=["Assumes target warehouse uses UTC timestamps."]
    )
    result = TranslationResult(
        metadata=base_metadata,
        status=TranslationStatus.SUCCESS,
        response=response
    )
    
    assert result.assumption_count == 1
    assert result.transformation_count == 0
    t = result.transformations[0]
    assert t.type == "ASSUMPTION"
    assert t.source == "ASSUMPTION"
    assert t.target == "Assumes target warehouse uses UTC timestamps."
    assert t.occurrences == 1


def test_api_serialization(base_metadata):
    """Verify computed fields actually appear in Pydantic JSON serialization."""
    response = TranslationResponse(
        target_sql="SELECT COALESCE(a, 0)",
        translated_rules=[
            StructuredRule(source_path="p1", source_expression="NVL", target_expression="COALESCE", rule_type="mapping"),
        ]
    )
    result = TranslationResult(
        metadata=base_metadata,
        status=TranslationStatus.SUCCESS,
        response=response
    )
    
    # Dump to dictionary simulating FastAPI serialization
    data = result.model_dump(mode="json")
    
    assert "transformation_count" in data
    assert data["transformation_count"] == 1
    
    assert "transformations" in data
    assert len(data["transformations"]) == 1
    
    t = data["transformations"][0]
    assert t["source"] == "NVL"
    assert t["target"] == "COALESCE"


def test_old_migration_compatibility(base_metadata):
    """Load an older object lacking newer attributes if any, and verify computed fields don't break."""
    # Build dictionary missing new/optional fields
    old_data = {
        "metadata": base_metadata.model_dump(),
        "status": "SUCCESS",
        "validation_summary": "",
        # Note lack of response, structural_differences, etc.
    }
    
    result = TranslationResult.model_validate(old_data)
    assert result.transformation_count == 0
    assert result.transformations == []

def test_regression_nvl_coalesce_2_occurrences(base_metadata):
    """
    Regression test for MIG-690BDDF5F5BC7:
    The source SQL contains two NVL calls and the target contains two COALESCE calls.
    Ensure they map to a single NVL -> COALESCE transformation with 2 occurrences.
    """
    response = TranslationResponse(
        target_sql="SELECT COALESCE(a, 0), COALESCE(b, 0) FROM t",
        translated_rules=[
            StructuredRule(
                source_path="select_clause",
                source_expression="NVL",
                target_expression="COALESCE",
                rule_type="FUNCTION_MAPPING"
            ),
            StructuredRule(
                source_path="where_clause",
                source_expression="NVL",
                target_expression="COALESCE",
                rule_type="FUNCTION_MAPPING"
            )
        ]
    )
    result = TranslationResult(
        metadata=base_metadata,
        status=TranslationStatus.SUCCESS,
        response=response
    )
    
    assert result.transformation_count == 1
    t = result.transformations[0]
    assert t.source == "NVL"
    assert t.target == "COALESCE"
    assert t.occurrences == 2
