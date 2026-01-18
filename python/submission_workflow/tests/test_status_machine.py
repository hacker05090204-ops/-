"""
Phase-7 SubmissionStatus State Machine Tests

Tests for the SubmissionStatusMachine that ensures:
- Valid transitions follow the state diagram
- Invalid transitions raise InvalidStatusTransitionError
- Terminal states have no outgoing transitions
- PENDING → SUBMITTED without CONFIRMED is blocked (security)

State Diagram:
    PENDING → CONFIRMED → SUBMITTED → ACKNOWLEDGED
                    ↓           ↓
                 FAILED      REJECTED

Feature: human-authorized-submission, Property 15: Status Transition Validation
Validates: Requirements 5.1, 5.2
"""

from __future__ import annotations
from itertools import product

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from submission_workflow.types import (
    SubmissionStatus,
    SubmissionStatusMachine,
    VALID_STATUS_TRANSITIONS,
)
from submission_workflow.errors import InvalidStatusTransitionError


class TestValidTransitions:
    """Tests for valid status transitions."""
    
    def test_pending_to_confirmed(self) -> None:
        """PENDING → CONFIRMED is valid (human confirms)."""
        machine = SubmissionStatusMachine(SubmissionStatus.PENDING)
        
        result = machine.transition(SubmissionStatus.CONFIRMED)
        
        assert result == SubmissionStatus.CONFIRMED
        assert machine.current_status == SubmissionStatus.CONFIRMED
    
    def test_confirmed_to_submitted(self) -> None:
        """CONFIRMED → SUBMITTED is valid (transmission succeeds)."""
        machine = SubmissionStatusMachine(SubmissionStatus.CONFIRMED)
        
        result = machine.transition(SubmissionStatus.SUBMITTED)
        
        assert result == SubmissionStatus.SUBMITTED
        assert machine.current_status == SubmissionStatus.SUBMITTED
    
    def test_confirmed_to_failed(self) -> None:
        """CONFIRMED → FAILED is valid (transmission fails)."""
        machine = SubmissionStatusMachine(SubmissionStatus.CONFIRMED)
        
        result = machine.transition(SubmissionStatus.FAILED)
        
        assert result == SubmissionStatus.FAILED
        assert machine.current_status == SubmissionStatus.FAILED
    
    def test_submitted_to_acknowledged(self) -> None:
        """SUBMITTED → ACKNOWLEDGED is valid (platform acknowledges)."""
        machine = SubmissionStatusMachine(SubmissionStatus.SUBMITTED)
        
        result = machine.transition(SubmissionStatus.ACKNOWLEDGED)
        
        assert result == SubmissionStatus.ACKNOWLEDGED
        assert machine.current_status == SubmissionStatus.ACKNOWLEDGED
    
    def test_submitted_to_rejected(self) -> None:
        """SUBMITTED → REJECTED is valid (platform rejects)."""
        machine = SubmissionStatusMachine(SubmissionStatus.SUBMITTED)
        
        result = machine.transition(SubmissionStatus.REJECTED)
        
        assert result == SubmissionStatus.REJECTED
        assert machine.current_status == SubmissionStatus.REJECTED
    
    def test_full_happy_path(self) -> None:
        """Full happy path: PENDING → CONFIRMED → SUBMITTED → ACKNOWLEDGED."""
        machine = SubmissionStatusMachine()
        
        assert machine.current_status == SubmissionStatus.PENDING
        
        machine.transition(SubmissionStatus.CONFIRMED)
        assert machine.current_status == SubmissionStatus.CONFIRMED
        
        machine.transition(SubmissionStatus.SUBMITTED)
        assert machine.current_status == SubmissionStatus.SUBMITTED
        
        machine.transition(SubmissionStatus.ACKNOWLEDGED)
        assert machine.current_status == SubmissionStatus.ACKNOWLEDGED
        assert machine.is_terminal()


class TestInvalidTransitions:
    """Tests for invalid status transitions that must raise InvalidStatusTransitionError."""
    
    def test_pending_to_submitted_blocked(self) -> None:
        """
        PENDING → SUBMITTED is INVALID (must go through CONFIRMED).
        
        SECURITY: This prevents bypassing the human confirmation step.
        
        Feature: human-authorized-submission, Property 15: Status Transition Validation
        """
        machine = SubmissionStatusMachine(SubmissionStatus.PENDING)
        
        with pytest.raises(InvalidStatusTransitionError) as exc_info:
            machine.transition(SubmissionStatus.SUBMITTED)
        
        assert exc_info.value.from_status == SubmissionStatus.PENDING
        assert exc_info.value.to_status == SubmissionStatus.SUBMITTED
        # Status should not have changed
        assert machine.current_status == SubmissionStatus.PENDING
    
    def test_pending_to_acknowledged_blocked(self) -> None:
        """PENDING → ACKNOWLEDGED is INVALID."""
        machine = SubmissionStatusMachine(SubmissionStatus.PENDING)
        
        with pytest.raises(InvalidStatusTransitionError):
            machine.transition(SubmissionStatus.ACKNOWLEDGED)
    
    def test_pending_to_rejected_blocked(self) -> None:
        """PENDING → REJECTED is INVALID."""
        machine = SubmissionStatusMachine(SubmissionStatus.PENDING)
        
        with pytest.raises(InvalidStatusTransitionError):
            machine.transition(SubmissionStatus.REJECTED)
    
    def test_pending_to_failed_blocked(self) -> None:
        """PENDING → FAILED is INVALID (must confirm first)."""
        machine = SubmissionStatusMachine(SubmissionStatus.PENDING)
        
        with pytest.raises(InvalidStatusTransitionError):
            machine.transition(SubmissionStatus.FAILED)
    
    def test_confirmed_to_acknowledged_blocked(self) -> None:
        """CONFIRMED → ACKNOWLEDGED is INVALID (must submit first)."""
        machine = SubmissionStatusMachine(SubmissionStatus.CONFIRMED)
        
        with pytest.raises(InvalidStatusTransitionError):
            machine.transition(SubmissionStatus.ACKNOWLEDGED)
    
    def test_confirmed_to_rejected_blocked(self) -> None:
        """CONFIRMED → REJECTED is INVALID (must submit first)."""
        machine = SubmissionStatusMachine(SubmissionStatus.CONFIRMED)
        
        with pytest.raises(InvalidStatusTransitionError):
            machine.transition(SubmissionStatus.REJECTED)
    
    def test_submitted_to_pending_blocked(self) -> None:
        """SUBMITTED → PENDING is INVALID (no backward transitions)."""
        machine = SubmissionStatusMachine(SubmissionStatus.SUBMITTED)
        
        with pytest.raises(InvalidStatusTransitionError):
            machine.transition(SubmissionStatus.PENDING)
    
    def test_submitted_to_confirmed_blocked(self) -> None:
        """SUBMITTED → CONFIRMED is INVALID (no backward transitions)."""
        machine = SubmissionStatusMachine(SubmissionStatus.SUBMITTED)
        
        with pytest.raises(InvalidStatusTransitionError):
            machine.transition(SubmissionStatus.CONFIRMED)
    
    def test_submitted_to_failed_blocked(self) -> None:
        """SUBMITTED → FAILED is INVALID (failure only from CONFIRMED)."""
        machine = SubmissionStatusMachine(SubmissionStatus.SUBMITTED)
        
        with pytest.raises(InvalidStatusTransitionError):
            machine.transition(SubmissionStatus.FAILED)


class TestTerminalStates:
    """Tests for terminal states (no outgoing transitions)."""
    
    def test_acknowledged_is_terminal(self) -> None:
        """ACKNOWLEDGED is a terminal state."""
        machine = SubmissionStatusMachine(SubmissionStatus.ACKNOWLEDGED)
        
        assert machine.is_terminal()
        
        # No transitions allowed
        for status in SubmissionStatus:
            with pytest.raises(InvalidStatusTransitionError):
                machine.transition(status)
    
    def test_rejected_is_terminal(self) -> None:
        """REJECTED is a terminal state."""
        machine = SubmissionStatusMachine(SubmissionStatus.REJECTED)
        
        assert machine.is_terminal()
        
        # No transitions allowed
        for status in SubmissionStatus:
            with pytest.raises(InvalidStatusTransitionError):
                machine.transition(status)
    
    def test_failed_is_terminal(self) -> None:
        """FAILED is a terminal state."""
        machine = SubmissionStatusMachine(SubmissionStatus.FAILED)
        
        assert machine.is_terminal()
        
        # No transitions allowed
        for status in SubmissionStatus:
            with pytest.raises(InvalidStatusTransitionError):
                machine.transition(status)
    
    def test_pending_is_not_terminal(self) -> None:
        """PENDING is not a terminal state."""
        machine = SubmissionStatusMachine(SubmissionStatus.PENDING)
        assert not machine.is_terminal()
    
    def test_confirmed_is_not_terminal(self) -> None:
        """CONFIRMED is not a terminal state."""
        machine = SubmissionStatusMachine(SubmissionStatus.CONFIRMED)
        assert not machine.is_terminal()
    
    def test_submitted_is_not_terminal(self) -> None:
        """SUBMITTED is not a terminal state."""
        machine = SubmissionStatusMachine(SubmissionStatus.SUBMITTED)
        assert not machine.is_terminal()


class TestCanTransition:
    """Tests for can_transition() method."""
    
    def test_can_transition_returns_true_for_valid(self) -> None:
        """can_transition() returns True for valid transitions."""
        machine = SubmissionStatusMachine(SubmissionStatus.PENDING)
        
        assert machine.can_transition(SubmissionStatus.CONFIRMED)
    
    def test_can_transition_returns_false_for_invalid(self) -> None:
        """can_transition() returns False for invalid transitions."""
        machine = SubmissionStatusMachine(SubmissionStatus.PENDING)
        
        assert not machine.can_transition(SubmissionStatus.SUBMITTED)
        assert not machine.can_transition(SubmissionStatus.ACKNOWLEDGED)
    
    def test_can_transition_does_not_change_state(self) -> None:
        """can_transition() does not change the current state."""
        machine = SubmissionStatusMachine(SubmissionStatus.PENDING)
        
        machine.can_transition(SubmissionStatus.CONFIRMED)
        
        assert machine.current_status == SubmissionStatus.PENDING


class TestStaticMethods:
    """Tests for static utility methods."""
    
    def test_get_valid_transitions_from_pending(self) -> None:
        """get_valid_transitions() returns correct set for PENDING."""
        valid = SubmissionStatusMachine.get_valid_transitions(SubmissionStatus.PENDING)
        
        assert valid == {SubmissionStatus.CONFIRMED}
    
    def test_get_valid_transitions_from_confirmed(self) -> None:
        """get_valid_transitions() returns correct set for CONFIRMED."""
        valid = SubmissionStatusMachine.get_valid_transitions(SubmissionStatus.CONFIRMED)
        
        assert valid == {SubmissionStatus.SUBMITTED, SubmissionStatus.FAILED}
    
    def test_get_valid_transitions_from_submitted(self) -> None:
        """get_valid_transitions() returns correct set for SUBMITTED."""
        valid = SubmissionStatusMachine.get_valid_transitions(SubmissionStatus.SUBMITTED)
        
        assert valid == {SubmissionStatus.ACKNOWLEDGED, SubmissionStatus.REJECTED}
    
    def test_get_valid_transitions_from_terminal(self) -> None:
        """get_valid_transitions() returns empty set for terminal states."""
        assert SubmissionStatusMachine.get_valid_transitions(SubmissionStatus.ACKNOWLEDGED) == set()
        assert SubmissionStatusMachine.get_valid_transitions(SubmissionStatus.REJECTED) == set()
        assert SubmissionStatusMachine.get_valid_transitions(SubmissionStatus.FAILED) == set()
    
    def test_validate_transition_static(self) -> None:
        """validate_transition() works without instance."""
        assert SubmissionStatusMachine.validate_transition(
            SubmissionStatus.PENDING,
            SubmissionStatus.CONFIRMED,
        )
        assert not SubmissionStatusMachine.validate_transition(
            SubmissionStatus.PENDING,
            SubmissionStatus.SUBMITTED,
        )


class TestPropertyBased:
    """Property-based tests for SubmissionStatusMachine."""
    
    @given(
        from_status=st.sampled_from(list(SubmissionStatus)),
        to_status=st.sampled_from(list(SubmissionStatus)),
    )
    @settings(max_examples=100)
    def test_property_all_transitions_validated(
        self,
        from_status: SubmissionStatus,
        to_status: SubmissionStatus,
    ) -> None:
        """
        Property: All transitions are validated against the state diagram.
        
        For any (from_status, to_status) pair:
        - If valid: transition succeeds
        - If invalid: InvalidStatusTransitionError is raised
        
        Feature: human-authorized-submission, Property 15: Status Transition Validation
        """
        machine = SubmissionStatusMachine(from_status)
        is_valid = to_status in VALID_STATUS_TRANSITIONS.get(from_status, set())
        
        if is_valid:
            result = machine.transition(to_status)
            assert result == to_status
            assert machine.current_status == to_status
        else:
            with pytest.raises(InvalidStatusTransitionError):
                machine.transition(to_status)
            # State should not have changed
            assert machine.current_status == from_status
    
    @given(
        from_status=st.sampled_from(list(SubmissionStatus)),
        to_status=st.sampled_from(list(SubmissionStatus)),
    )
    @settings(max_examples=100)
    def test_property_can_transition_matches_transition(
        self,
        from_status: SubmissionStatus,
        to_status: SubmissionStatus,
    ) -> None:
        """
        Property: can_transition() result matches transition() behavior.
        
        If can_transition() returns True, transition() should succeed.
        If can_transition() returns False, transition() should raise.
        """
        machine = SubmissionStatusMachine(from_status)
        can_do = machine.can_transition(to_status)
        
        if can_do:
            # Should not raise
            machine.transition(to_status)
        else:
            # Should raise
            with pytest.raises(InvalidStatusTransitionError):
                machine.transition(to_status)
    
    @given(
        status=st.sampled_from([
            SubmissionStatus.ACKNOWLEDGED,
            SubmissionStatus.REJECTED,
            SubmissionStatus.FAILED,
        ]),
        target=st.sampled_from(list(SubmissionStatus)),
    )
    @settings(max_examples=100)
    def test_property_terminal_states_block_all_transitions(
        self,
        status: SubmissionStatus,
        target: SubmissionStatus,
    ) -> None:
        """
        Property: Terminal states block ALL transitions.
        
        From ACKNOWLEDGED, REJECTED, or FAILED, no transition is valid.
        """
        machine = SubmissionStatusMachine(status)
        
        assert machine.is_terminal()
        
        with pytest.raises(InvalidStatusTransitionError):
            machine.transition(target)
    
    @given(
        target=st.sampled_from([
            SubmissionStatus.SUBMITTED,
            SubmissionStatus.ACKNOWLEDGED,
            SubmissionStatus.REJECTED,
        ]),
    )
    @settings(max_examples=100)
    def test_property_pending_cannot_skip_confirmed(
        self,
        target: SubmissionStatus,
    ) -> None:
        """
        Property: PENDING cannot skip CONFIRMED to reach later states.
        
        SECURITY: This ensures human confirmation cannot be bypassed.
        
        Feature: human-authorized-submission, Property 15: Status Transition Validation
        """
        machine = SubmissionStatusMachine(SubmissionStatus.PENDING)
        
        # Only CONFIRMED is valid from PENDING
        if target != SubmissionStatus.CONFIRMED:
            with pytest.raises(InvalidStatusTransitionError):
                machine.transition(target)


class TestAllTransitionsCoverage:
    """Exhaustive tests covering all possible transitions."""
    
    def test_all_valid_transitions_succeed(self) -> None:
        """All valid transitions in the state diagram should succeed."""
        for from_status, valid_targets in VALID_STATUS_TRANSITIONS.items():
            for to_status in valid_targets:
                machine = SubmissionStatusMachine(from_status)
                result = machine.transition(to_status)
                assert result == to_status, (
                    f"Valid transition {from_status.value} → {to_status.value} failed"
                )
    
    def test_all_invalid_transitions_raise(self) -> None:
        """All invalid transitions should raise InvalidStatusTransitionError."""
        all_statuses = set(SubmissionStatus)
        
        for from_status in SubmissionStatus:
            valid_targets = VALID_STATUS_TRANSITIONS.get(from_status, set())
            invalid_targets = all_statuses - valid_targets
            
            for to_status in invalid_targets:
                machine = SubmissionStatusMachine(from_status)
                with pytest.raises(InvalidStatusTransitionError):
                    machine.transition(to_status)
    
    def test_transition_count(self) -> None:
        """Verify the expected number of valid transitions."""
        total_valid = sum(len(targets) for targets in VALID_STATUS_TRANSITIONS.values())
        # PENDING→CONFIRMED, CONFIRMED→SUBMITTED, CONFIRMED→FAILED,
        # SUBMITTED→ACKNOWLEDGED, SUBMITTED→REJECTED = 5 valid transitions
        assert total_valid == 5
    
    def test_terminal_state_count(self) -> None:
        """Verify the expected number of terminal states."""
        terminal_count = sum(
            1 for targets in VALID_STATUS_TRANSITIONS.values()
            if len(targets) == 0
        )
        # ACKNOWLEDGED, REJECTED, FAILED = 3 terminal states
        assert terminal_count == 3
