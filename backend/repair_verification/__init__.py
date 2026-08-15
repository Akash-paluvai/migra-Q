"""Phase 8 — Repair Execution & Deterministic Re-Validation Engine."""

from backend.repair_verification.candidate_validator import CandidateRepairValidator
from backend.repair_verification.comparator import DiscrepancyComparator
from backend.repair_verification.context import RepairVerificationContext
from backend.repair_verification.executor import RepairExecutor
from backend.repair_verification.models import (
    VERIFICATION_ENGINE_VERSION,
    DiscrepancyOutcome,
    DiscrepancyOutcomeStatus,
    RepairOutcome,
    RepairVerificationResult,
    VerificationEvidenceItem,
    VerificationMetadata,
    VerificationStatus,
)
from backend.repair_verification.repository import (
    get_outcomes_by_verification_id,
    get_verification_result,
    save_verification_result,
)
from backend.repair_verification.service import RepairVerificationService
from backend.repair_verification.status import VerificationStatusDeterminer

__all__ = [
    "VERIFICATION_ENGINE_VERSION",
    "CandidateRepairValidator",
    "DiscrepancyComparator",
    "DiscrepancyOutcome",
    "DiscrepancyOutcomeStatus",
    "RepairExecutor",
    "RepairOutcome",
    "RepairVerificationContext",
    "RepairVerificationResult",
    "RepairVerificationService",
    "VerificationEvidenceItem",
    "VerificationMetadata",
    "VerificationStatus",
    "VerificationStatusDeterminer",
    "get_outcomes_by_verification_id",
    "get_verification_result",
    "save_verification_result",
]
