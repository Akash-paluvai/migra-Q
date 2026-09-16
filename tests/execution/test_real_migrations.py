import os
import sys

# Configure mock database for tests to prevent psycopg errors when orchestrator hits DB
os.environ["POSTGRES_DB"] = "migraq_test"
os.environ["POSTGRES_USER"] = "postgres"
os.environ["POSTGRES_PASSWORD"] = "postgres"
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["POSTGRES_PORT"] = "5432"

from backend.orchestrator.service import MigrationOrchestrator
from backend.orchestrator.models import PipelineRunRequest
from backend.db.database import get_db_session, engine, Base
from sqlalchemy import text

def run_test_migration(test_name: str, sql: str, expected_status: str):
    print(f"\n{'='*80}")
    print(f"Running Test: {test_name}")
    print(f"{'='*80}")
    
    orchestrator = MigrationOrchestrator()
    try:
        req = PipelineRunRequest(
            migration_id=test_name,
            source_sql=sql,
            source_dialect="teradata",
            target_dialect="bigquery",
            dataset_id="customer_risk",
            force_new=True
        )
        report = orchestrator.run(req)
        print(f"\nFinal Assurance Status: {report.assurance_report.final_status.name}")
        print(f"Decision Reason: {report.assurance_report.decision_reason}")
        
        assert report.assurance_report.final_status.name == expected_status, f"Expected {expected_status}, got {report.assurance_report.final_status.name}"
        print(f"✓ TEST PASSED: {test_name}")
    except Exception as e:
        print(f"\n✗ TEST FAILED: {test_name} with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    q1 = """
SELECT
    c.customer_id,
    ZEROIFNULL(a.balance) AS account_balance,
    NULLIFZERO(c.credit_score) AS normalized_credit_score,
    CASE
        WHEN c.credit_score >= 700 THEN 'LOW_RISK'
        WHEN c.credit_score >= 600 THEN 'MEDIUM_RISK'
        ELSE 'HIGH_RISK'
    END AS calculated_risk
FROM customers c
LEFT JOIN accounts a
    ON c.customer_id = a.customer_id
WHERE c.status = 'ACTIVE'
ORDER BY c.customer_id
LIMIT 100;
"""
    
    q2 = """
SELECT HASHROW(c.customer_id, c.customer_segment) AS fingerprint FROM customers c LIMIT 10;
"""
    
    q3 = """
SELECT
    c.customer_id,
    c.this_column_does_not_exist
FROM customers c
WHERE c.status = 'ACTIVE';
"""

    # Ensure all tables exist for the mock db
    Base.metadata.create_all(bind=engine)
    
    with get_db_session() as db:
        # Tables that might exist, just skip deletion or ignore errors
        pass

    run_test_migration("test_q1_exact", q1, "VERIFIED")
    run_test_migration("test_q2_sandbox_lim", q2, "INCONCLUSIVE")
    run_test_migration("test_q3_exec_error", q3, "BLOCKED")
