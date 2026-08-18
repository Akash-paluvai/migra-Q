import uuid
import datetime
from sqlalchemy.orm import Session
from backend.db.session import SessionLocal
from backend.models import (
    MigrationRecordORM,
    ValidationSummaryORM,
    DiscrepancySummaryORM,
    DiagnosisSummaryORM,
    RepairSummaryORM,
    VerificationSummaryORM
)

def create_mock():
    db = SessionLocal()
    mig_id = f"MIG-{uuid.uuid4().hex[:12].upper()}"
    
    mig = MigrationRecordORM(
        migration_id=mig_id,
        source_dialect="teradata",
        target_dialect="bigquery",
        dataset_id="customer_risk",
        source_sql_hash="fakehash",
        current_state="VERIFIED",
        final_status="VERIFIED"
    )
    db.add(mig)
    db.flush()
    
    val = ValidationSummaryORM(
        validation_id=f"VAL-{uuid.uuid4().hex[:8]}",
        migration_id=mig_id,
        overall_status="FAIL"
    )
    db.add(val)
    
    disc = DiscrepancySummaryORM(
        diagnosis_id=f"DIAG-{uuid.uuid4().hex[:8]}",
        migration_id=mig_id,
        discrepancy_count=1,
        total_affected_rows=3200
    )
    db.add(disc)
    
    diag = DiagnosisSummaryORM(
        diagnosis_id=disc.diagnosis_id,
        migration_id=mig_id,
        discrepancy_id="D-001",
        status="REPAIR_PROPOSED",
        observed_change="COUNT(DISTINCT entity_id) differs between source and target.",
        diagnosis_confidence=0.94
    )
    db.add(diag)
    
    rep = RepairSummaryORM(
        repair_id=f"REP-{uuid.uuid4().hex[:8]}",
        migration_id=mig_id,
        status="VERIFIED",
        repair_confidence=0.92,
        changed_region="columns[entity_count]",
        original_sql="SELECT COUNT(entity_id) FROM customers",
        proposed_sql="SELECT COUNT(DISTINCT entity_id) FROM customers"
    )
    db.add(rep)
    
    ver = VerificationSummaryORM(
        verification_id=f"VER-{uuid.uuid4().hex[:8]}",
        migration_id=mig_id,
        status="VERIFIED",
        original_discrepancy_count=1,
        remaining_discrepancy_count=0,
        new_discrepancy_count=0,
        resolved_discrepancy_count=1,
        affected_rows_before=3200,
        affected_rows_after=0,
        reduction_percentage=100.0
    )
    db.add(ver)
    
    db.commit()
    print(mig_id)
    db.close()

create_mock()
