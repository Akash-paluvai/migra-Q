import sys
sys.path.append('.')
from backend.db.database import SessionLocal
from backend.db.models import MigrationRecordModel, MigrationAssuranceReportModel
import json
import requests

db = SessionLocal()
rec = db.query(MigrationRecordModel).order_by(MigrationRecordModel.created_at.desc()).first()
rep = db.query(MigrationAssuranceReportModel).filter(MigrationAssuranceReportModel.migration_id == rec.migration_id).first()

if rep:
    lineage = json.loads(rep.lineage_json)
    translation_id = lineage.get('translation_id')
    print("Translation ID:", translation_id)
    r = requests.get(f"http://127.0.0.1:8000/api/v1/translations/{translation_id}")
    print("Translations Status code:", r.status_code)
    print("Translations Response:", r.text[:200])

    # Also test translation without plural
    r2 = requests.get(f"http://127.0.0.1:8000/api/v1/translation/{translation_id}")
    print("Translation Status code:", r2.status_code)

else:
    print("No Assurance Report")
