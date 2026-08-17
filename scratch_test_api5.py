import sys
sys.path.append('.')
from backend.db.database import SessionLocal
from sqlalchemy import text
import json
import requests

db = SessionLocal()
res = db.execute(text("SELECT lineage_json FROM assurance_reports ORDER BY created_at DESC LIMIT 1")).fetchone()
if res:
    lineage = json.loads(res[0])
    translation_id = lineage.get('translation_id')
    print("Translation ID:", translation_id)
    r = requests.get(f"http://127.0.0.1:8000/api/v1/translations/{translation_id}")
    print("Translations Status code:", r.status_code)
    print("Translations Response:", r.text[:200])
else:
    print("No Assurance Report")
