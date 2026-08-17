import sys
sys.path.append('.')
from backend.db.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
recs = db.execute(text("SELECT execution_mode, status, error_message FROM executions ORDER BY id DESC LIMIT 2")).fetchall()
for r in recs:
    print(r)
