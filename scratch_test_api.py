import sys
sys.path.append('.')
from backend.db.database import SessionLocal
from backend.db.models import MigrationRecord

db = SessionLocal()
rec = db.query(MigrationRecord).order_by(MigrationRecord.created_at.desc()).first()
print("Migration ID:", rec.migration_id)
print("Storage:", rec.source_sql_storage)
print("Source SQL snippet:", rec.source_sql[:50] if rec.source_sql else "None")
print("Ref:", rec.source_sql_ref)
