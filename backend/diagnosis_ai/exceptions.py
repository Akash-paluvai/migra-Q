class DiagnosisAIError(Exception):
    """Base exception for Diagnosis AI errors."""

    pass


class PersistenceError(DiagnosisAIError):
    """Raised when authoritative PostgreSQL persistence fails in non-test environments."""

    pass


class EvidenceGroundingError(DiagnosisAIError):
    """Raised when AI response claims contain ungrounded or invalid evidence IDs."""

    pass


class ScopeCreepError(DiagnosisAIError):
    """Raised when candidate repair modifies AST nodes outside the discrepancy target region."""

    pass


class ContractViolationError(DiagnosisAIError):
    """Raised when candidate repair violates target SQL contract (output aliases, tables)."""

    pass


class InvalidRepairSQLError(DiagnosisAIError):
    """Raised when candidate repair SQL is syntactically invalid or unsafe."""

    pass


class InsufficientEvidenceError(DiagnosisAIError):
    """Raised when evidence is ambiguous or insufficient to formulate a diagnosis/repair."""

    pass


class InvalidTargetCandidateError(DiagnosisAIError):
    """Raised when input target candidate SQL is already invalid."""

    pass
