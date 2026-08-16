import sys
import os

# Ensure backend can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from backend.orchestrator.models import PipelineRunRequest
from backend.orchestrator.service import MigrationOrchestrator
from backend.core.config import settings

def test_dynamic():
    print(f"Using LLM_PROVIDER={settings.LLM_PROVIDER}, MODEL={settings.LLM_MODEL}")
    
    orchestrator = MigrationOrchestrator()
    
    source_sql = """
    SELECT 
        region_id, 
        SUM(revenue) AS total_revenue
    FROM monthly_sales
    WHERE sale_year = 2026
    GROUP BY region_id
    HAVING SUM(revenue) > 1000
    """
    
    req = PipelineRunRequest(
        source_sql=source_sql,
        source_dialect="teradata",
        target_dialect="bigquery",
        dataset_id="customer_aggregation",
        mock_mode=None
    )
    
    print("Running migration pipeline...")
    result = orchestrator.run(req)
    
    print("\n--- RESULT ---")
    print(f"Migration ID: {result.migration_id}")
    print(f"Final Status: {result.migration_record.final_status}")
    print(f"Assurance Score: {result.migration_record.assurance_score}")
    
    print("\n--- ASSURANCE REPORT SUMMARY ---")
    if result.assurance_report:
        if result.assurance_report.translation_summary:
            print("Translation:", result.assurance_report.translation_summary.status)
            print("Summary:", result.assurance_report.translation_summary)

if __name__ == "__main__":
    test_dynamic()
