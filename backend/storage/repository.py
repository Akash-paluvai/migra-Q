import uuid
from typing import Dict, Any, List, Optional


class MigrationRepository:
    """In-memory & DB persistence layer for storing migration runs and validation artifacts."""

    _migrations_db: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def save_migration(cls, migration_data: Dict[str, Any]) -> str:
        migration_id = migration_data.get("migration_id", str(uuid.uuid4()))
        migration_data["migration_id"] = migration_id
        cls._migrations_db[migration_id] = migration_data
        return migration_id

    @classmethod
    def get_migration(cls, migration_id: str) -> Optional[Dict[str, Any]]:
        return cls._migrations_db.get(migration_id)

    @classmethod
    def list_migrations(cls) -> List[Dict[str, Any]]:
        return list(cls._migrations_db.values())
