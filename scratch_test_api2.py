import sys
sys.path.append('.')
from backend.db.database import SessionLocal
from backend.db.models import MigrationRecord, AssuranceReportRecord
import json

db = SessionLocal()
rec = db.query(MigrationRecord).order_by(MigrationRecord.created_at.desc()).first()
rep = db.query(AssuranceReportRecord).filter(AssuranceReportRecord.migration_id == rec.migration_id).first()

print("Migration ID:", rec.migration_id)
if rep:
    lineage = json.loads(rep.lineage_json)
    translation_id = lineage.get('translation_id')
    print("Translation ID:", translation_id)
else:
    print("No Assurance Report")
