"""Migration state machine — enforces valid transitions and terminal state protection."""

from __future__ import annotations

from datetime import datetime, timezone

from backend.assurance.exceptions import InvalidStateTransitionError
from backend.assurance.models import MigrationState, MigrationStateEvent

# Terminal states cannot transition to any other state.
TERMINAL_STATES: frozenset[MigrationState] = frozenset({
    MigrationState.VERIFIED,
    MigrationState.FAILED,
    MigrationState.BLOCKED,
    MigrationState.ERROR,
})

# Allowed transitions as a directed graph: from_state -> set of valid to_states.
ALLOWED_TRANSITIONS: dict[MigrationState, frozenset[MigrationState]] = {
    MigrationState.CREATED: frozenset({
        MigrationState.ANALYZING,
        MigrationState.ERROR,
    }),
    MigrationState.ANALYZING: frozenset({
        MigrationState.TRANSLATING,
        MigrationState.ERROR,
    }),
    MigrationState.TRANSLATING: frozenset({
        MigrationState.PREFLIGHTING,
        MigrationState.FAILED,
        MigrationState.ERROR,
    }),
    MigrationState.PREFLIGHTING: frozenset({
        MigrationState.EXECUTING,
        MigrationState.BLOCKED,
        MigrationState.ERROR,
    }),
    MigrationState.EXECUTING: frozenset({
        MigrationState.VALIDATING,
        MigrationState.FAILED,
        MigrationState.ERROR,
    }),
    MigrationState.VALIDATING: frozenset({
        MigrationState.VERIFIED,
        MigrationState.DISCREPANCIES_FOUND,
        MigrationState.ERROR,
    }),
    MigrationState.DISCREPANCIES_FOUND: frozenset({
        MigrationState.DIAGNOSING,
        MigrationState.BLOCKED,
        MigrationState.ERROR,
    }),
    MigrationState.DIAGNOSING: frozenset({
        MigrationState.REPAIR_PROPOSED,
        MigrationState.BLOCKED,
        MigrationState.FAILED,
        MigrationState.ERROR,
    }),
    MigrationState.REPAIR_PROPOSED: frozenset({
        MigrationState.REPAIR_VERIFYING,
        MigrationState.ERROR,
    }),
    MigrationState.REPAIR_VERIFYING: frozenset({
        MigrationState.VERIFIED,
        MigrationState.BLOCKED,
        MigrationState.FAILED,
        MigrationState.ERROR,
    }),
    # Terminal states have no outgoing transitions.
    MigrationState.VERIFIED: frozenset(),
    MigrationState.FAILED: frozenset(),
    MigrationState.BLOCKED: frozenset(),
    MigrationState.ERROR: frozenset(),
}


class MigrationStateMachine:
    """Enforces the Phase 9 migration state transition graph.

    Each state transition creates an immutable MigrationStateEvent.
    Terminal states cannot transition to any other state.
    """

    def transition(
        self,
        migration_id: str,
        from_state: MigrationState,
        to_state: MigrationState,
        reason: str,
        artifact_id: str = "",
    ) -> MigrationStateEvent:
        """Validate and execute a state transition.

        Args:
            migration_id: The migration this transition belongs to.
            from_state: Current state.
            to_state: Target state.
            reason: Human-readable reason for the transition.
            artifact_id: Optional artifact ID triggering the transition.

        Returns:
            Immutable MigrationStateEvent recording the transition.

        Raises:
            InvalidStateTransitionError: If the transition is not allowed.
        """
        if from_state in TERMINAL_STATES:
            raise InvalidStateTransitionError(
                from_state.value,
                to_state.value,
                f"Cannot transition from terminal state {from_state.value}",
            )

        allowed = ALLOWED_TRANSITIONS.get(from_state, frozenset())
        if to_state not in allowed:
            raise InvalidStateTransitionError(
                from_state.value,
                to_state.value,
                f"Allowed targets from {from_state.value}: "
                f"{', '.join(s.value for s in sorted(allowed, key=lambda s: s.value))}",
            )

        return MigrationStateEvent(
            migration_id=migration_id,
            from_state=from_state,
            to_state=to_state,
            reason=reason,
            artifact_id=artifact_id,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def is_terminal(state: MigrationState) -> bool:
        """Return True if the given state is terminal."""
        return state in TERMINAL_STATES

    @staticmethod
    def get_allowed_targets(state: MigrationState) -> frozenset[MigrationState]:
        """Return the set of states reachable from the given state."""
        return ALLOWED_TRANSITIONS.get(state, frozenset())
