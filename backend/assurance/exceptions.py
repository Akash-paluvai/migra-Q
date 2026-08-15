"""Phase 9 Assurance exceptions."""


class AssuranceError(Exception):
    """Base exception for Phase 9 assurance operations."""


class InvalidStateTransitionError(AssuranceError):
    """Raised when a state machine transition violates the allowed transition graph."""

    def __init__(self, from_state: str, to_state: str, reason: str = ""):
        msg = f"Invalid state transition: {from_state} -> {to_state}"
        if reason:
            msg += f" ({reason})"
        super().__init__(msg)
        self.from_state = from_state
        self.to_state = to_state


class ArtifactMissingError(AssuranceError):
    """Raised when a required upstream artifact is missing."""

    def __init__(self, artifact_name: str, artifact_id: str = ""):
        msg = f"Required artifact missing: {artifact_name}"
        if artifact_id:
            msg += f" (expected ID: {artifact_id})"
        super().__init__(msg)
        self.artifact_name = artifact_name


class LineageIncompleteError(AssuranceError):
    """Raised when the audit lineage chain is incomplete for the verification path."""

    def __init__(self, missing_fields: list[str], verification_path: str = ""):
        msg = f"Incomplete audit lineage: missing {', '.join(missing_fields)}"
        if verification_path:
            msg += f" (path: {verification_path})"
        super().__init__(msg)
        self.missing_fields = missing_fields
