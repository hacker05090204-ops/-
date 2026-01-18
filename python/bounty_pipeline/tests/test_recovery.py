"""
Tests for Recovery Manager.

**Feature: bounty-pipeline**

Property tests validate:
- Property 17: Failure Recovery
  (preserve drafts, queue actions for retry)
"""

import pytest
from datetime import datetime, timezone
from hypothesis import given, strategies as st, settings

from bounty_pipeline.recovery import (
    RecoveryManager,
    PipelineState,
    PendingAction,
    ActionResult,
    ActionType,
    ActionStatus,
)
from bounty_pipeline.errors import RecoveryError


# =============================================================================
# Property 17: Failure Recovery Tests
# =============================================================================


class TestFailureRecovery:
    """
    **Property 17: Failure Recovery**
    **Validates: Requirements 12.1, 12.4**

    For any submission failure or network unavailability,
    the system SHALL preserve drafts and queue actions for retry.
    """

    def test_state_can_be_saved_and_recovered(self):
        """Pipeline state can be saved and recovered."""
        manager = RecoveryManager()

        state = manager.create_state(
            pending_drafts=[{"draft_id": "d1", "title": "Test"}],
            pending_reviews=[{"review_id": "r1"}],
            metadata={"version": "1.0"},
        )

        state_id = manager.save_state(state)
        recovered = manager.recover_state(state_id)

        assert recovered is not None
        assert recovered.state_id == state.state_id
        assert recovered.pending_drafts == state.pending_drafts
        assert recovered.pending_reviews == state.pending_reviews

    def test_actions_can_be_queued(self):
        """Actions can be queued for later execution."""
        manager = RecoveryManager()

        action = manager.queue_action(
            action_type=ActionType.SUBMIT,
            payload={"draft_id": "d1", "platform": "hackerone"},
        )

        assert action.action_id
        assert action.action_type == ActionType.SUBMIT
        assert action.status == ActionStatus.PENDING

    def test_queued_actions_are_retrievable(self):
        """Queued actions can be retrieved."""
        manager = RecoveryManager()

        manager.queue_action(ActionType.SUBMIT, {"draft_id": "d1"})
        manager.queue_action(ActionType.UPDATE_STATUS, {"submission_id": "s1"})
        manager.queue_action(ActionType.NOTIFY_HUMAN, {"message": "test"})

        pending = manager.get_pending_actions()
        assert len(pending) == 3

    @given(
        draft_count=st.integers(min_value=0, max_value=10),
        review_count=st.integers(min_value=0, max_value=10),
    )
    @settings(max_examples=20, deadline=5000)
    def test_state_preserves_all_data(self, draft_count: int, review_count: int):
        """State preserves all pending work."""
        manager = RecoveryManager()

        drafts = [{"draft_id": f"d{i}"} for i in range(draft_count)]
        reviews = [{"review_id": f"r{i}"} for i in range(review_count)]

        state = manager.create_state(
            pending_drafts=drafts,
            pending_reviews=reviews,
        )

        manager.save_state(state)
        recovered = manager.recover_state(state.state_id)

        assert len(recovered.pending_drafts) == draft_count
        assert len(recovered.pending_reviews) == review_count

    def test_failed_actions_can_retry(self):
        """Failed actions can be retried."""
        manager = RecoveryManager()

        action = manager.queue_action(
            ActionType.SUBMIT,
            {"draft_id": "d1"},
            max_retries=3,
        )

        # Simulate failure
        action.status = ActionStatus.FAILED
        action.retry_count = 1

        assert action.can_retry

        # After max retries
        action.retry_count = 3
        assert not action.can_retry

    def test_human_alerts_on_failure(self):
        """Human is alerted on recovery failure."""
        manager = RecoveryManager()

        error = RecoveryError("State corruption detected")
        diagnostic = {
            "state_id": "state-001",
            "corruption_type": "hash_mismatch",
        }

        manager.alert_human(error, diagnostic, severity="critical")

        alerts = manager.get_alerts()
        assert len(alerts) == 1
        assert alerts[0]["severity"] == "critical"
        assert alerts[0]["error_type"] == "RecoveryError"


# =============================================================================
# State Management Tests
# =============================================================================


class TestStateManagement:
    """Tests for state management functionality."""

    def test_create_state_generates_id(self):
        """Creating state generates unique ID."""
        manager = RecoveryManager()

        state1 = manager.create_state()
        state2 = manager.create_state()

        assert state1.state_id != state2.state_id

    def test_state_serialization(self):
        """State can be serialized and deserialized."""
        state = PipelineState(
            state_id="test-state",
            created_at=datetime.now(timezone.utc),
            pending_drafts=[{"id": "d1"}],
            pending_reviews=[{"id": "r1"}],
            pending_submissions=[{"id": "s1"}],
            audit_records=[{"id": "a1"}],
            metadata={"key": "value"},
        )

        data = state.to_dict()
        recovered = PipelineState.from_dict(data)

        assert recovered.state_id == state.state_id
        assert recovered.pending_drafts == state.pending_drafts
        assert recovered.metadata == state.metadata

    def test_state_hash_is_deterministic(self):
        """State hash is deterministic."""
        state = PipelineState(
            state_id="test-state",
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            pending_drafts=[{"id": "d1"}],
            pending_reviews=[],
            pending_submissions=[],
            audit_records=[],
        )

        hash1 = state.compute_hash()
        hash2 = state.compute_hash()

        assert hash1 == hash2

    def test_recover_latest_state(self):
        """Can recover most recent state."""
        manager = RecoveryManager()

        state1 = manager.create_state(metadata={"version": "1"})
        manager.save_state(state1)

        state2 = manager.create_state(metadata={"version": "2"})
        manager.save_state(state2)

        recovered = manager.recover_state()  # No ID = latest

        assert recovered.state_id == state2.state_id

    def test_recover_nonexistent_returns_none(self):
        """Recovering nonexistent state returns None."""
        manager = RecoveryManager()

        recovered = manager.recover_state("nonexistent")
        assert recovered is None


# =============================================================================
# Action Queue Tests
# =============================================================================


class TestActionQueue:
    """Tests for action queue functionality."""

    def test_action_types(self):
        """All action types can be queued."""
        manager = RecoveryManager()

        for action_type in ActionType:
            action = manager.queue_action(action_type, {"test": True})
            assert action.action_type == action_type

    def test_action_processing_with_handler(self):
        """Actions are processed by registered handlers."""
        manager = RecoveryManager()

        # Register handler
        def submit_handler(action: PendingAction) -> ActionResult:
            return ActionResult(
                action_id=action.action_id,
                success=True,
                message="Submitted successfully",
            )

        manager.register_handler(ActionType.SUBMIT, submit_handler)

        action = manager.queue_action(ActionType.SUBMIT, {"draft_id": "d1"})
        result = manager.process_action(action.action_id)

        assert result.success
        assert action.status == ActionStatus.COMPLETED

    def test_action_processing_without_handler_raises(self):
        """Processing without handler raises RecoveryError."""
        manager = RecoveryManager()

        action = manager.queue_action(ActionType.SUBMIT, {"draft_id": "d1"})

        with pytest.raises(RecoveryError, match="No handler"):
            manager.process_action(action.action_id)

    def test_action_failure_updates_status(self):
        """Failed action updates status correctly."""
        manager = RecoveryManager()

        def failing_handler(action: PendingAction) -> ActionResult:
            return ActionResult(
                action_id=action.action_id,
                success=False,
                message="Failed",
                error="Network error",
            )

        manager.register_handler(ActionType.SUBMIT, failing_handler)

        action = manager.queue_action(ActionType.SUBMIT, {"draft_id": "d1"})
        result = manager.process_action(action.action_id)

        assert not result.success
        assert action.status == ActionStatus.FAILED
        assert action.last_error == "Network error"

    def test_process_queue_handles_all_pending(self):
        """Process queue handles all pending actions."""
        manager = RecoveryManager()

        def success_handler(action: PendingAction) -> ActionResult:
            return ActionResult(
                action_id=action.action_id,
                success=True,
                message="OK",
            )

        manager.register_handler(ActionType.SUBMIT, success_handler)
        manager.register_handler(ActionType.UPDATE_STATUS, success_handler)

        manager.queue_action(ActionType.SUBMIT, {"id": "1"})
        manager.queue_action(ActionType.SUBMIT, {"id": "2"})
        manager.queue_action(ActionType.UPDATE_STATUS, {"id": "3"})

        results = manager.process_queue()

        assert len(results) == 3
        assert all(r.success for r in results)

    def test_cleanup_completed_actions(self):
        """Completed actions can be cleaned up."""
        manager = RecoveryManager()

        def success_handler(action: PendingAction) -> ActionResult:
            return ActionResult(
                action_id=action.action_id,
                success=True,
                message="OK",
            )

        manager.register_handler(ActionType.SUBMIT, success_handler)

        manager.queue_action(ActionType.SUBMIT, {"id": "1"})
        manager.queue_action(ActionType.SUBMIT, {"id": "2"})

        manager.process_queue()

        removed = manager.cleanup_completed()
        assert removed == 2
        assert manager.pending_count == 0


# =============================================================================
# Alert Tests
# =============================================================================


class TestAlerts:
    """Tests for human alert functionality."""

    def test_alert_records_details(self):
        """Alerts record all details."""
        manager = RecoveryManager()

        error = ValueError("Test error")
        diagnostic = {"key": "value"}

        manager.alert_human(error, diagnostic, severity="warning")

        alerts = manager.get_alerts()
        assert len(alerts) == 1

        alert = alerts[0]
        assert alert["error_type"] == "ValueError"
        assert alert["error_message"] == "Test error"
        assert alert["diagnostic"] == diagnostic
        assert alert["severity"] == "warning"
        assert "timestamp" in alert

    def test_multiple_alerts(self):
        """Multiple alerts are recorded."""
        manager = RecoveryManager()

        manager.alert_human(ValueError("Error 1"), {})
        manager.alert_human(RuntimeError("Error 2"), {})
        manager.alert_human(RecoveryError("Error 3"), {})

        assert manager.alert_count == 3

    def test_clear_alerts(self):
        """Alerts can be cleared."""
        manager = RecoveryManager()

        manager.alert_human(ValueError("Error 1"), {})
        manager.alert_human(ValueError("Error 2"), {})

        cleared = manager.clear_alerts()

        assert cleared == 2
        assert manager.alert_count == 0


# =============================================================================
# Retry Logic Tests
# =============================================================================


class TestRetryLogic:
    """Tests for action retry logic."""

    def test_retry_count_increments(self):
        """Retry count increments on each attempt."""
        manager = RecoveryManager()

        def failing_handler(action: PendingAction) -> ActionResult:
            return ActionResult(
                action_id=action.action_id,
                success=False,
                message="Failed",
                error="Error",
            )

        manager.register_handler(ActionType.SUBMIT, failing_handler)

        action = manager.queue_action(ActionType.SUBMIT, {"id": "1"}, max_retries=3)

        manager.process_action(action.action_id)
        assert action.retry_count == 1

        manager.process_action(action.action_id)
        assert action.retry_count == 2

    def test_max_retries_respected(self):
        """Actions stop retrying after max retries."""
        manager = RecoveryManager()

        action = manager.queue_action(ActionType.SUBMIT, {"id": "1"}, max_retries=2)

        # Simulate failures
        action.retry_count = 2
        action.status = ActionStatus.FAILED

        assert not action.can_retry

    def test_completed_actions_not_in_pending(self):
        """Completed actions are not in pending list."""
        manager = RecoveryManager()

        def success_handler(action: PendingAction) -> ActionResult:
            return ActionResult(
                action_id=action.action_id,
                success=True,
                message="OK",
            )

        manager.register_handler(ActionType.SUBMIT, success_handler)

        action = manager.queue_action(ActionType.SUBMIT, {"id": "1"})
        manager.process_action(action.action_id)

        pending = manager.get_pending_actions()
        assert action not in pending
