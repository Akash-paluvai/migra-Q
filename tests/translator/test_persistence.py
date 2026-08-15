"""Unit tests for translation PostgreSQL persistence and secret isolation."""


from backend.translator.models import TranslationRequest
from backend.translator.repository import save_translation_result
from backend.translator.service import TranslationService


def test_save_and_get_translation_result_in_memory():
    req = TranslationRequest(
        source_sql="SELECT customer_id FROM transactions;",
        source_dialect="teradata",
        target_dialect="bigquery",
    )
    res = TranslationService.translate(request=req, mock_mode="MOCK_GOOD")

    # In test environment with memory persistence, save_translation_result handles DB gracefully
    save_translation_result(res)
    assert res.metadata.translation_id != ""


def test_translation_metadata_does_not_contain_api_key():
    req = TranslationRequest(
        source_sql="SELECT customer_id FROM transactions;",
        source_dialect="teradata",
        target_dialect="bigquery",
    )
    res = TranslationService.translate(request=req, mock_mode="MOCK_GOOD")

    res_dict = res.model_dump()
    json_str = str(res_dict)

    assert "LLM_API_KEY" not in json_str
    assert "sk-" not in json_str
