"""
Tests for Status Tracker.

**Feature: bounty-pipeline**

Property tests validate:
- Property 10: Status Tracking Accuracy
  (only record confirmed updates, never assume)
"""

import pytest
from datetime import datetime, timezone
from hypothesis import given, strategies as st, settings

from bounty_pipeline.status import (
    StatusTracker,
    TrackedSubmission,
)
from bounty_pipeline.types import (
    SubmissionStatus,
    StatusUpdate,
)


# =============================================================================
# Property 10: Status Tracking Accuracy Tests
# =============================================================================


class TestStatusTrackingAccuracy:
    """
    **Property 10: Status Tracking Accuracy**
    **Validates: Requirements 7.1, 7.3, 7.4, 7.5**

    For any submission status, the system SHALL only record
    confirmed status updates and SHALL NOT assume acceptance
    or rejection.
    """

    def test_initial_status_is_submitted(self):
        """New submissions start with SUBMITTED status."""
        tracker = StatusTracker()

        tracked = tracker.register_submission(
            submission_id="test-001",
            platform="hackerone",
        )

        assert tracked.current_status == SubmissionStatus.SUBMITTED

    def test_status_only_changes_on_explicit_update(self):
        """Status only changes when explicitly updated."""
        tracker = StatusTracker()

        tracker.register_submission(
            submission_id="test-001",
            platform="hackerone",
        )

        # Status should remain SUBMITTED until explicitly updated
        assert tracker.get_status("test-001") == SubmissionStatus.SUBMITTED

        # Update status
        tracker.update_status("test-001", SubmissionStatus.TRIAGED)
        assert tracker.get_status("test-001") == SubmissionStatus.TRIAGED

    @given(
        submission_id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N", "P"))),
        platform=st.sampled_from(["hackerone", "bugcrowd", "generic"]),
    )
    @settings(max_examples=50, deadline=5000)
    def test_registered_submissions_are_tracked(self, submission_id: str, platform: str):
        """All registered submissions are tracked."""
        tracker = StatusTracker()

        tracked = tracker.register_submission(
            submission_id=submission_id,
            platform=platform,
        )

        assert tracked.submission_id == submission_id
        assert tracked.platform == platform
        assert tracker.get_submission(submission_id) is not None

    def test_status_history_is_complete(self):
        """All status changes are recorded in history."""
        tracker = StatusTracker()

        tracker.register_submission("test-001", "hackerone")

        # Make several status updates
        tracker.update_status("test-001", SubmissionStatus.TRIAGED)
        tracker.update_status("test-001", SubmissionStatus.NEEDS_MORE_INFO)
        tracker.update_status("test-001", SubmissionStatus.TRIAGED)
        tracker.record_acceptance("test-001", bounty_amount=500.0)

        history = tracker.get_history("test-001")

        assert len(history) == 4
        assert history[0].new_status == SubmissionStatus.TRIAGED
        assert history[1].new_status == SubmissionStatus.NEEDS_MORE_INFO
        assert history[2].new_status == SubmissionStatus.TRIAGED
        assert history[3].new_status == SubmissionStatus.ACCEPTED

    def test_acceptance_records_bounty_amount(self):
        """Acceptance records bounty amount when provided."""
        tracker = StatusTracker()

        tracker.register_submission("test-001", "hackerone")
        update = tracker.record_acceptance("test-001", bounty_amount=1000.0)

        assert update.new_status == SubmissionStatus.ACCEPTED
        assert update.bounty_amount == 1000.0

        tracked = tracker.get_submission("test-001")
        assert tracked.bounty_amount == 1000.0

    def test_acceptance_without_bounty_amount(self):
        """Acceptance can be recorded without bounty amount."""
        tracker = StatusTracker()

        tracker.register_submission("test-001", "hackerone")
        update = tracker.record_acceptance("test-001")

        assert update.new_status == SubmissionStatus.ACCEPTED
        assert update.bounty_amount is None

    def test_rejection_records_reason(self):
        """Rejection records reason when provided."""
        tracker = StatusTracker()

        tracker.register_submission("test-001", "hackerone")
        update = tracker.record_rejection("test-001", reason="Duplicate")

        assert update.new_status == SubmissionStatus.REJECTED
        assert update.rejection_reason == "Duplicate"

        tracked = tracker.get_submission("test-001")
        assert tracked.rejection_reason == "Duplicate"

    def test_rejection_without_reason(self):
        """Rejection can be recorded without reason."""
        tracker = StatusTracker()

        tracker.register_submission("test-001", "hackerone")
        update = tracker.record_rejection("test-001")

        assert update.new_status == SubmissionStatus.REJECTED
        assert update.rejection_reason is None

    def test_payment_records_amount(self):
        """Payment records bounty amount."""
        tracker = StatusTracker()

        tracker.register_submission("test-001", "hackerone")
        tracker.record_acceptance("test-001")
        update = tracker.record_payment("test-001", bounty_amount=2500.0)

        assert update.new_status == SubmissionStatus.PAID
        assert update.bounty_amount == 2500.0

        tracked = tracker.get_submission("test-001")
        assert tracked.bounty_amount == 2500.0

    def test_unknown_submission_raises(self):
        """Operations on unknown submissions raise ValueError."""
        tracker = StatusTracker()

        with pytest.raises(ValueError, match="not found"):
            tracker.get_status("nonexistent")

        with pytest.raises(ValueError, match="not found"):
            tracker.update_status("nonexistent", SubmissionStatus.TRIAGED)

        with pytest.raises(ValueError, match="not found"):
            tracker.record_acceptance("nonexistent")

        with pytest.raises(ValueError, match="not found"):
            tracker.record_rejection("nonexistent")


# =============================================================================
# Status Update Tests
# =============================================================================


class TestStatusUpdates:
    """Tests for status update functionality."""

    def test_update_preserves_old_status(self):
        """Status updates record the old status."""
        tracker = StatusTracker()

        tracker.register_submission("test-001", "hackerone")
        update = tracker.update_status("test-001", SubmissionStatus.TRIAGED)

        assert update.old_status == SubmissionStatus.SUBMITTED
        assert update.new_status == SubmissionStatus.TRIAGED

    def test_update_records_timestamp(self):
        """Status updates record timestamp."""
        tracker = StatusTracker()

        tracker.register_submission("test-001", "hackerone")
        before = datetime.now(timezone.utc)
        update = tracker.update_status("test-001", SubmissionStatus.TRIAGED)
        after = datetime.now(timezone.utc)

        assert before <= update.updated_at <= after

    def test_update_stores_platform_data(self):
        """Status updates store platform-specific data."""
        tracker = StatusTracker()

        tracker.register_submission("test-001", "hackerone")
        platform_data = {"triage_date": "2024-01-15", "analyst": "John"}

        update = tracker.update_status(
            "test-001",
            SubmissionStatus.TRIAGED,
            platform_data=platform_data,
        )

        assert update.platform_data == platform_data

        tracked = tracker.get_submission("test-001")
        assert tracked.platform_data["triage_date"] == "2024-01-15"


# =============================================================================
# Query Tests
# =============================================================================


class TestStatusQueries:
    """Tests for status query functionality."""

    def test_get_by_status(self):
        """Can filter submissions by status."""
        tracker = StatusTracker()

        tracker.register_submission("test-001", "hackerone")
        tracker.register_submission("test-002", "hackerone")
        tracker.register_submission("test-003", "hackerone")

        tracker.update_status("test-001", SubmissionStatus.TRIAGED)
        tracker.update_status("test-002", SubmissionStatus.TRIAGED)

        triaged = tracker.get_by_status(SubmissionStatus.TRIAGED)
        submitted = tracker.get_by_status(SubmissionStatus.SUBMITTED)

        assert len(triaged) == 2
        assert len(submitted) == 1

    def test_get_pending(self):
        """Can get pending (non-terminal) submissions."""
        tracker = StatusTracker()

        tracker.register_submission("test-001", "hackerone")
        tracker.register_submission("test-002", "hackerone")
        tracker.register_submission("test-003", "hackerone")
        tracker.register_submission("test-004", "hackerone")

        tracker.record_acceptance("test-001")
        tracker.record_rejection("test-002")
        tracker.update_status("test-003", SubmissionStatus.TRIAGED)

        pending = tracker.get_pending()

        # test-003 (TRIAGED) and test-004 (SUBMITTED) are pending
        assert len(pending) == 2
        pending_ids = {p.submission_id for p in pending}
        assert "test-003" in pending_ids
        assert "test-004" in pending_ids

    def test_total_bounty_calculation(self):
        """Total bounty is calculated correctly."""
        tracker = StatusTracker()

        tracker.register_submission("test-001", "hackerone")
        tracker.register_submission("test-002", "hackerone")
        tracker.register_submission("test-003", "hackerone")

        tracker.record_acceptance("test-001", bounty_amount=500.0)
        tracker.record_acceptance("test-002", bounty_amount=1000.0)
        tracker.record_rejection("test-003")

        assert tracker.total_bounty == 1500.0

    def test_counts(self):
        """Status counts are accurate."""
        tracker = StatusTracker()

        tracker.register_submission("test-001", "hackerone")
        tracker.register_submission("test-002", "hackerone")
        tracker.register_submission("test-003", "hackerone")
        tracker.register_submission("test-004", "hackerone")

        tracker.record_acceptance("test-001")
        tracker.record_rejection("test-002")
        tracker.record_acceptance("test-003")
        tracker.record_payment("test-003", bounty_amount=500.0)

        assert tracker.total_count == 4
        assert tracker.accepted_count == 1  # test-001
        assert tracker.rejected_count == 1  # test-002
        assert tracker.paid_count == 1  # test-003


# =============================================================================
# History Tests
# =============================================================================


class TestStatusHistory:
    """Tests for status history functionality."""

    def test_history_order_is_chronological(self):
        """History is in chronological order."""
        tracker = StatusTracker()

        tracker.register_submission("test-001", "hackerone")

        tracker.update_status("test-001", SubmissionStatus.TRIAGED)
        tracker.update_status("test-001", SubmissionStatus.NEEDS_MORE_INFO)
        tracker.update_status("test-001", SubmissionStatus.TRIAGED)

        history = tracker.get_history("test-001")

        for i in range(len(history) - 1):
            assert history[i].updated_at <= history[i + 1].updated_at

    def test_history_tracks_transitions(self):
        """History tracks all status transitions."""
        tracker = StatusTracker()

        tracker.register_submission("test-001", "hackerone")

        tracker.update_status("test-001", SubmissionStatus.TRIAGED)
        tracker.update_status("test-001", SubmissionStatus.NEEDS_MORE_INFO)
        tracker.update_status("test-001", SubmissionStatus.TRIAGED)
        tracker.record_acceptance("test-001")

        history = tracker.get_history("test-001")

        # Verify transitions
        assert history[0].old_status == SubmissionStatus.SUBMITTED
        assert history[0].new_status == SubmissionStatus.TRIAGED

        assert history[1].old_status == SubmissionStatus.TRIAGED
        assert history[1].new_status == SubmissionStatus.NEEDS_MORE_INFO

        assert history[2].old_status == SubmissionStatus.NEEDS_MORE_INFO
        assert history[2].new_status == SubmissionStatus.TRIAGED

        assert history[3].old_status == SubmissionStatus.TRIAGED
        assert history[3].new_status == SubmissionStatus.ACCEPTED
