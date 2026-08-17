from __future__ import annotations

from datetime import datetime, timezone

from backend.assurance.models import (
    MigrationAssuranceReport,
    MigrationRecord,
    MigrationStateEvent,
)
from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)


class MigrationAssuranceRepository:
    """Persistence layer for Phase 9 migration assurance artifacts.

    Uses in-memory storage in test mode, PostgreSQL in production.
    """

    _migrations: dict[str, MigrationRecord] = {}
    _events: dict[str, list[MigrationStateEvent]] = {}
    _reports: dict[str, MigrationAssuranceReport] = {}

    def save_migration(self, record: MigrationRecord) -> None:
        """Persist a migration record."""
        if settings.PERSISTENCE_MODE == "memory":
            self._migrations[record.migration_id] = record
            return
        self._save_migration_pg(record)

    def save_state_event(self, event: MigrationStateEvent) -> None:
        """Persist a state transition event."""
        if settings.PERSISTENCE_MODE == "memory":
            self._events.setdefault(event.migration_id, []).append(event)
            return
        self._save_event_pg(event)

    def save_assurance_report(self, report: MigrationAssuranceReport) -> None:
        """Persist a migration assurance report."""
        if settings.PERSISTENCE_MODE == "memory":
            self._reports[report.migration_id] = report
            return
        self._save_report_pg(report)

    def get_migration(self, migration_id: str) -> MigrationRecord | None:
        """Retrieve a migration record by ID."""
        if settings.PERSISTENCE_MODE == "memory":
            return self._migrations.get(migration_id)
        return self._get_migration_pg(migration_id)

    def get_events(self, migration_id: str) -> list[MigrationStateEvent]:
        """Retrieve all state events for a migration."""
        if settings.PERSISTENCE_MODE == "memory":
            return self._events.get(migration_id, [])
        return self._get_events_pg(migration_id)

    def get_assurance_report(self, migration_id: str) -> MigrationAssuranceReport | None:
        """Retrieve the assurance report for a migration."""
        if settings.PERSISTENCE_MODE == "memory":
            return self._reports.get(migration_id)
        return self._get_report_pg(migration_id)

    def get_all_migrations(self) -> list[MigrationRecord]:
        """Retrieve all migration records."""
        if settings.PERSISTENCE_MODE == "memory":
            return list(self._migrations.values())
        return self._get_all_migrations_pg()

    @classmethod
    def reset_memory_store(cls) -> None:
        """Clear all in-memory data (test utility)."""
        cls._migrations.clear()
        cls._events.clear()
        cls._reports.clear()

    # -----------------------------------------------------------------------
    # PostgreSQL persistence
    # -----------------------------------------------------------------------

    def _save_migration_pg(self, record: MigrationRecord) -> None:
        try:
            from backend.db.database import get_db_session
            from backend.db.models import MigrationRecordModel

            current_state_str = record.current_state.value if hasattr(record.current_state, "value") else str(record.current_state)
            final_status_str = (
                record.final_status.value if record.final_status and hasattr(record.final_status, "value")
                else (str(record.final_status) if record.final_status else "IN_PROGRESS")
            )

            session = get_db_session()
            try:
                existing = session.query(MigrationRecordModel).filter_by(migration_id=record.migration_id).first()
                if existing:
                    existing.source_dialect = record.source_dialect
                    existing.target_dialect = record.target_dialect
                    existing.source_sql_hash = record.source_sql_hash
                    existing.normalized_sql_hash = record.normalized_sql_hash
                    existing.source_sql = record.source_sql
                    existing.source_sql_storage = record.source_sql_storage
                    existing.source_sql_ref = record.source_sql_ref
                    existing.dataset_id = record.dataset_id
                    existing.dataset_hash = record.dataset_hash
                    existing.current_state = current_state_str
                    existing.final_status = final_status_str
                    existing.assurance_score = record.assurance_score
                    existing.evidence_coverage = record.evidence_coverage
                    existing.assurance_version = record.assurance_version
                    existing.updated_at = datetime.now(timezone.utc)
                else:
                    db_record = MigrationRecordModel(
                        migration_id=record.migration_id,
                        source_dialect=record.source_dialect,
                        target_dialect=record.target_dialect,
                        source_sql_hash=record.source_sql_hash,
                        normalized_sql_hash=record.normalized_sql_hash,
                        source_sql=record.source_sql,
                        source_sql_storage=record.source_sql_storage,
                        source_sql_ref=record.source_sql_ref,
                        dataset_id=record.dataset_id,
                        dataset_hash=record.dataset_hash,
                        current_state=current_state_str,
                        final_status=final_status_str,
                        assurance_score=record.assurance_score,
                        evidence_coverage=record.evidence_coverage,
                        assurance_version=record.assurance_version,
                    )
                    session.add(db_record)
                session.commit()
            finally:
                session.close()
        except Exception as exc:
            logger.error("Failed to persist migration record: %s", exc)
            raise

    def _save_event_pg(self, event: MigrationStateEvent) -> None:
        try:
            from backend.db.database import get_db_session
            from backend.db.models import MigrationStateEventModel

            from_state_str = event.from_state.value if hasattr(event.from_state, "value") else str(event.from_state)
            to_state_str = event.to_state.value if hasattr(event.to_state, "value") else str(event.to_state)

            session = get_db_session()
            try:
                db_record = MigrationStateEventModel(
                    migration_id=event.migration_id,
                    from_state=from_state_str,
                    to_state=to_state_str,
                    reason=event.reason,
                    artifact_id=event.artifact_id,
                )
                session.add(db_record)
                session.commit()
            finally:
                session.close()
        except Exception as exc:
            logger.error("Failed to persist state event: %s", exc)
            raise

    def _save_report_pg(self, report: MigrationAssuranceReport) -> None:
        try:
            from backend.db.database import get_db_session
            from backend.db.models import MigrationAssuranceReportModel

            final_status_str = (
                report.final_status.value if report.final_status and hasattr(report.final_status, "value")
                else str(report.final_status)
            )
            verification_path_str = (
                report.verification_path.value if report.verification_path and hasattr(report.verification_path, "value")
                else (str(report.verification_path) if report.verification_path else "DIRECT_PASS")
            )
            band_str = (
                report.score.band.value if report.score and report.score.band and hasattr(report.score.band, "value")
                else (str(report.score.band) if report.score and report.score.band else None)
            )
            evidence_score_val = report.score.evidence_score if report.score else None
            evidence_coverage_val = report.score.evidence_coverage if report.score else None

            session = get_db_session()
            try:
                existing = session.query(MigrationAssuranceReportModel).filter_by(migration_id=report.migration_id).first()
                if existing:
                    existing.assurance_version = report.assurance_version
                    existing.final_status = final_status_str
                    existing.decision_reason = report.decision_reason
                    existing.verification_path = verification_path_str
                    existing.evidence_score = evidence_score_val
                    existing.evidence_coverage = evidence_coverage_val
                    existing.band = band_str
                    existing.report_json = report.model_dump_json()
                else:
                    db_record = MigrationAssuranceReportModel(
                        migration_id=report.migration_id,
                        assurance_version=report.assurance_version,
                        final_status=final_status_str,
                        decision_reason=report.decision_reason,
                        verification_path=verification_path_str,
                        evidence_score=evidence_score_val,
                        evidence_coverage=evidence_coverage_val,
                        band=band_str,
                        report_json=report.model_dump_json(),
                    )
                    session.add(db_record)
                session.commit()
            finally:
                session.close()
        except Exception as exc:
            logger.error("Failed to persist assurance report: %s", exc)
            raise

    def _get_migration_pg(self, migration_id: str) -> MigrationRecord | None:
        try:
            from backend.db.database import get_db_session
            from backend.db.models import MigrationRecordModel

            session = get_db_session()
            try:
                row = session.query(MigrationRecordModel).filter_by(
                    migration_id=migration_id
                ).first()
                if row is None:
                    return None
                return MigrationRecord(
                    migration_id=row.migration_id,
                    source_dialect=row.source_dialect,
                    target_dialect=row.target_dialect,
                    source_sql_hash=row.source_sql_hash,
                    normalized_sql_hash=row.normalized_sql_hash,
                    source_sql=row.source_sql,
                    source_sql_storage=row.source_sql_storage,
                    source_sql_ref=row.source_sql_ref,
                    dataset_id=row.dataset_id,
                    dataset_hash=row.dataset_hash,
                    current_state=row.current_state,
                    final_status=row.final_status,
                    assurance_score=row.assurance_score,
                    evidence_coverage=row.evidence_coverage,
                    assurance_version=row.assurance_version,
                    created_at=row.created_at.isoformat() if row.created_at else "",
                    updated_at=row.updated_at.isoformat() if row.updated_at else "",
                )
            finally:
                session.close()
        except Exception as exc:
            logger.error("Failed to retrieve migration record: %s", exc)
            return None

    def _get_events_pg(self, migration_id: str) -> list[MigrationStateEvent]:
        try:
            from backend.db.database import get_db_session
            from backend.db.models import MigrationStateEventModel

            session = get_db_session()
            try:
                rows = session.query(MigrationStateEventModel).filter_by(
                    migration_id=migration_id
                ).order_by(MigrationStateEventModel.id).all()
                return [
                    MigrationStateEvent(
                        migration_id=r.migration_id,
                        from_state=r.from_state,
                        to_state=r.to_state,
                        reason=r.reason or "",
                        artifact_id=r.artifact_id or "",
                        created_at=r.created_at.isoformat() if r.created_at else "",
                    )
                    for r in rows
                ]
            finally:
                session.close()
        except Exception as exc:
            logger.error("Failed to retrieve state events: %s", exc)
            return []

    def _get_report_pg(self, migration_id: str) -> MigrationAssuranceReport | None:
        try:
            from backend.db.database import get_db_session
            from backend.db.models import MigrationAssuranceReportModel

            session = get_db_session()
            try:
                row = session.query(MigrationAssuranceReportModel).filter_by(
                    migration_id=migration_id
                ).first()
                if row is None:
                    return None
                return MigrationAssuranceReport.model_validate_json(row.report_json)
            finally:
                session.close()
        except Exception as exc:
            logger.error("Failed to retrieve assurance report: %s", exc)
            return None

    def _get_all_migrations_pg(self) -> list[MigrationRecord]:
        try:
            from backend.db.database import get_db_session
            from backend.db.models import MigrationRecordModel

            session = get_db_session()
            try:
                rows = session.query(MigrationRecordModel).order_by(MigrationRecordModel.id.desc()).all()
                return [
                    MigrationRecord(
                        migration_id=row.migration_id,
                        source_dialect=row.source_dialect,
                        target_dialect=row.target_dialect,
                        source_sql_hash=row.source_sql_hash,
                        normalized_sql_hash=row.normalized_sql_hash,
                        source_sql=row.source_sql,
                        source_sql_storage=row.source_sql_storage,
                        source_sql_ref=row.source_sql_ref,
                        dataset_id=row.dataset_id,
                        dataset_hash=row.dataset_hash,
                        current_state=row.current_state,
                        final_status=row.final_status,
                        assurance_score=row.assurance_score,
                        evidence_coverage=row.evidence_coverage,
                        assurance_version=row.assurance_version,
                        created_at=row.created_at.isoformat() if row.created_at else "",
                        updated_at=row.updated_at.isoformat() if row.updated_at else "",
                    )
                    for row in rows
                ]
            finally:
                session.close()
        except Exception as exc:
            logger.error("Failed to retrieve all migrations: %s", exc)
            return []
