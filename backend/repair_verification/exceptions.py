"""Domain exceptions for Phase 8 Repair Execution & Deterministic Re-Validation Engine."""


class RepairVerificationError(Exception):
    """Base exception for all repair verification errors."""


class CandidateRejectedError(RepairVerificationError):
    """Raised when candidate repair fails pre-execution integrity checks."""

    def __init__(self, reason: str, details: dict | None = None) -> None:
        super().__init__(f"Candidate repair rejected: {reason}")
        self.reason = reason
        self.details = details or {}


class ExecutionFailedError(RepairVerificationError):
    """Raised when repaired SQL runtime execution fails in Phase 3."""

    def __init__(self, error_code: str, error_message: str) -> None:
        super().__init__(f"Repaired SQL execution failed [{error_code}]: {error_message}")
        self.error_code = error_code
        self.error_message = error_message


class ImmutabilityViolationError(RepairVerificationError):
    """Raised when dataset or validation configuration immutability is violated."""

    def __init__(self, violation_type: str, details: str) -> None:
        super().__init__(f"Immutability violation ({violation_type}): {details}")
        self.violation_type = violation_type
        self.details = details


class ArtifactMismatchError(RepairVerificationError):
    """Raised when supplied repaired SQL differs from Phase 7 stored proposal artifact."""

    def __init__(self, repair_id: str) -> None:
        super().__init__(f"Repaired SQL content does not match stored proposal artifact for '{repair_id}'")
        self.repair_id = repair_id
