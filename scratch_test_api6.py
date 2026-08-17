import sys
sys.path.append('.')
from backend.db.database import SessionLocal
from backend.db.models import MigrationRecordModel, MigrationAssuranceReportModel
import json

db = SessionLocal()
rec = db.query(MigrationRecordModel).order_by(MigrationRecordModel.created_at.desc()).first()
rep = db.query(MigrationAssuranceReportModel).filter(MigrationAssuranceReportModel.migration_id == rec.migration_id).first()

if rep:
    lineage = json.loads(rep.lineage_json)
    translation_id = lineage.get('translation_id')
    print("Translation ID:", translation_id)
else:
    print("No Assurance Report")
