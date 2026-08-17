import sys
from sqlalchemy import text

sys.path.append('.')
from backend.db.database import get_db_session

session = get_db_session()
try:
    session.execute(text("ALTER TABLE migrations ADD COLUMN normalized_sql_hash VARCHAR(64);"))
    session.execute(text("ALTER TABLE migrations ADD COLUMN source_sql TEXT;"))
    session.execute(text("ALTER TABLE migrations ADD COLUMN source_sql_storage VARCHAR(32) NOT NULL DEFAULT 'database';"))
    session.execute(text("ALTER TABLE migrations ADD COLUMN source_sql_ref VARCHAR(256);"))
    session.commit()
    print("Successfully altered table migrations.")
except Exception as e:
    session.rollback()
    print("Error altering table migrations:", e)
finally:
    session.close()
