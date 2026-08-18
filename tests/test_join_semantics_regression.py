import pytest
from unittest.mock import patch
from backend.assurance.service import MigrationAssuranceService
from backend.translator.models import TranslationResult, TranslationStatus, TranslationMetadata

@pytest.fixture
def assurance_service():
    return MigrationAssuranceService()

def test_join_semantics_null_nan_regression(assurance_service):

    source_sql = """
        SELECT 
            pe.ref_code,
            COUNT(se.detail_id) as joined_rows,
            COUNT(DISTINCT pe.entity_id) as entity_count,
            SUM(pe.base_val) as total_base_val,
            SUM(se.secondary_val) as total_secondary_val,
            CASE 
                WHEN COUNT(se.detail_id) = 0 THEN 'NO_MATCH'
                WHEN COUNT(se.detail_id) = 1 THEN 'SINGLE_MATCH'
                ELSE 'MULTI_ENTITY'
            END as cardinality_status
        FROM primary_entity pe
        LEFT JOIN secondary_entity se 
            ON pe.ref_code = se.ref_code
        GROUP BY pe.ref_code
        ORDER BY pe.ref_code NULLS FIRST
    """
    
    # We want to mock translation to just return the same SQL, to test purely semantic equivalence bugs
    def mock_translate(*args, **kwargs):
        import hashlib
        req = args[0]
        sql_hash = hashlib.sha256(req.source_sql.encode('utf-8')).hexdigest()[:16]
        meta = TranslationMetadata(
            translation_id="mock_id",
            request_id="mock_req",
            migration_id=req.migration_id,
            provider="mock_provider",
            model="mock_model",
            source_dialect="oracle",
            target_dialect="bigquery",
            source_sql_hash=sql_hash,
            translation_context_hash="mock",
            prompt_hash="mock",
            created_at="2024-01-01T00:00:00Z"
        )
        return TranslationResult(
            status=TranslationStatus.SUCCESS,
            source_sql=req.source_sql,
            translated_sql=req.source_sql,
            translation_time_ms=100,
            error_message=None,
            confidence_score=0.99,
            metadata=meta
        )
    
    with patch("backend.translator.service.TranslationService.translate", side_effect=mock_translate):
        report = assurance_service.run_migration_pipeline(
            source_sql=source_sql,
            source_dialect="oracle",
            target_dialect="bigquery",
            dataset_id="join_semantics",
        )
    
    assert report.validation_summary.overall_status == "PASS"


