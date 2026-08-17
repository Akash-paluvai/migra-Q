import sys
sys.path.append('.')
from backend.db.database import SessionLocal
from backend.db.models import MigrationModel, AssuranceReportModel
import json
import requests

db = SessionLocal()
rec = db.query(MigrationModel).order_by(MigrationModel.created_at.desc()).first()
rep = db.query(AssuranceReportModel).filter(AssuranceReportModel.migration_id == rec.migration_id).first()

if rep:
    lineage = json.loads(rep.lineage_json)
    translation_id = lineage.get('translation_id')
    print("Translation ID:", translation_id)
    r = requests.get(f"http://127.0.0.1:8000/api/v1/translations/{translation_id}")
    print("Status code:", r.status_code)
    print("Response:", r.text[:200])
else:
    print("No Assurance Report")
