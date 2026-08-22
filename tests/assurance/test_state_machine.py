"""Tests for Phase 9 state machine."""

import pytest

from backend.assurance.exceptions import InvalidStateTransitionError
from backend.assurance.models import MigrationState
from backend.assurance.state import (
    ALLOWED_TRANSITIONS,
    TERMINAL_STATES,
    MigrationStateMachine,
)


@pytest.fixture
def sm():
    return MigrationStateMachine()


class TestValidTransitions:
    def test_created_to_analyzing(self, sm):
        event = sm.transition("MIG-001", MigrationState.CREATED, MigrationState.ANALYZING, "Analysis started")
        assert event.from_state == MigrationState.CREATED
        assert event.to_state == MigrationState.ANALYZING
        assert event.migration_id == "MIG-001"

    def test_analyzing_to_translating(self, sm):
        event = sm.transition("MIG-001", MigrationState.ANALYZING, MigrationState.TRANSLATING, "Analysis complete")
        assert event.to_state == MigrationState.TRANSLATING

    def test_translating_to_preflighting(self, sm):
        event = sm.transition("MIG-001", MigrationState.TRANSLATING, MigrationState.PREFLIGHTING, "Translation succeeded")
        assert event.to_state == MigrationState.PREFLIGHTING

    def test_executing_to_validating(self, sm):
        event = sm.transition("MIG-001", MigrationState.EXECUTING, MigrationState.VALIDATING, "Execution succeeded")
        assert event.to_state == MigrationState.VALIDATING

    def test_validating_to_verified_direct_pass(self, sm):
        event = sm.transition("MIG-001", MigrationState.VALIDATING, MigrationState.VERIFIED, "No discrepancies")
        assert event.to_state == MigrationState.VERIFIED

    def test_validating_to_discrepancies_found(self, sm):
        event = sm.transition("MIG-001", MigrationState.VALIDATING, MigrationState.DISCREPANCIES_FOUND, "Discrepancies detected")
        assert event.to_state == MigrationState.DISCREPANCIES_FOUND

    def test_repair_verifying_to_verified(self, sm):
        event = sm.transition("MIG-001", MigrationState.REPAIR_VERIFYING, MigrationState.VERIFIED, "Repair verified")
        assert event.to_state == MigrationState.VERIFIED

    def test_repair_verifying_to_blocked(self, sm):
        event = sm.transition("MIG-001", MigrationState.REPAIR_VERIFYING, MigrationState.BLOCKED, "Partial resolution")
        assert event.to_state == MigrationState.BLOCKED

    def test_any_non_terminal_to_error(self, sm):
        for state in MigrationState:
            if state not in TERMINAL_STATES:
                event = sm.transition("MIG-001", state, MigrationState.ERROR, "System error")
                assert event.to_state == MigrationState.ERROR


class TestInvalidTransitions:
    def test_cannot_skip_states(self, sm):
        with pytest.raises(InvalidStateTransitionError):
            sm.transition("MIG-001", MigrationState.CREATED, MigrationState.VALIDATING, "Skip")

    def test_cannot_transition_from_verified(self, sm):
        with pytest.raises(InvalidStateTransitionError):
            sm.transition("MIG-001", MigrationState.VERIFIED, MigrationState.ANALYZING, "Reopen")

    def test_cannot_transition_from_failed(self, sm):
        with pytest.raises(InvalidStateTransitionError):
            sm.transition("MIG-001", MigrationState.FAILED, MigrationState.CREATED, "Reset")

    def test_cannot_transition_from_blocked(self, sm):
        with pytest.raises(InvalidStateTransitionError):
            sm.transition("MIG-001", MigrationState.BLOCKED, MigrationState.DIAGNOSING, "Retry")

    def test_cannot_transition_from_error(self, sm):
        with pytest.raises(InvalidStateTransitionError):
            sm.transition("MIG-001", MigrationState.ERROR, MigrationState.CREATED, "Reset")


class TestTerminalProtection:
    def test_terminal_states_have_no_outgoing(self):
        for state in TERMINAL_STATES:
            assert ALLOWED_TRANSITIONS[state] == frozenset()

    def test_is_terminal(self, sm):
        assert sm.is_terminal(MigrationState.VERIFIED)
        assert sm.is_terminal(MigrationState.FAILED)
        assert sm.is_terminal(MigrationState.BLOCKED)
        assert sm.is_terminal(MigrationState.ERROR)
        assert not sm.is_terminal(MigrationState.CREATED)
        assert not sm.is_terminal(MigrationState.VALIDATING)


class TestEventCreation:
    def test_event_has_artifact_id(self, sm):
        event = sm.transition("MIG-001", MigrationState.CREATED, MigrationState.ANALYZING, "start", artifact_id="ANA-001")
        assert event.artifact_id == "ANA-001"

    def test_event_has_timestamp(self, sm):
        event = sm.transition("MIG-001", MigrationState.CREATED, MigrationState.ANALYZING, "start")
        assert event.created_at  # non-empty
