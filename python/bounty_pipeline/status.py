"""
Status Tracker - Tracks submission status through platform lifecycle.

This module tracks the status of submissions on bug bounty platforms.

CRITICAL CONSTRAINTS:
- NEVER assume status — only record confirmed updates
- Status updates must come from platform data
- All status changes are recorded in audit trail
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from bounty_pipeline.types import (
    SubmissionStatus,
    StatusUpdate,
)


@dataclass
class TrackedSubmission:
    """A submission being tracked."""

    submission_id: str
    platform: str
    current_status: SubmissionStatus
    created_at: datetime
    last_updated_at: datetime
    history: list[StatusUpdate] = field(default_factory=list)
    bounty_amount: Optional[float] = None
    rejection_reason: Optional[str] = None
    platform_data: dict[str, Any] = field(default_factory=dict)


class StatusTracker:
    """
    Tracks submission status through platform lifecycle.

    CRITICAL: This tracker NEVER assumes status.
    It only records confirmed updates from platform data.

    Status lifecycle:
    SUBMITTED → TRIAGED → NEEDS_MORE_INFO → ACCEPTED → PAID
                       ↘ REJECTED

    Features:
    - Tracks status: submitted, triaged, accepted, rejected, paid
    - Updates from platform status webhooks/polling
    - Records acceptance with bounty amount
    - Records rejection with reason
    - Maintains complete status history
    """

    def __init__(self) -> None:
        """Initialize status tracker."""
        self._submissions: dict[str, TrackedSubmission] = {}

    def register_submission(
        self,
        submission_id: str,
        platform: str,
        initial_status: SubmissionStatus = SubmissionStatus.SUBMITTED,
        platform_data: Optional[dict[str, Any]] = None,
    ) -> TrackedSubmission:
        """
        Register a new submission for tracking.

        Args:
            submission_id: Platform submission ID
            platform: Platform name
            initial_status: Initial status (default SUBMITTED)
            platform_data: Optional platform-specific data

        Returns:
            TrackedSubmission object
        """
        now = datetime.now(timezone.utc)

        tracked = TrackedSubmission(
            submission_id=submission_id,
            platform=platform,
            current_status=initial_status,
            created_at=now,
            last_updated_at=now,
            platform_data=platform_data or {},
        )

        self._submissions[submission_id] = tracked
        return tracked

    def get_status(self, submission_id: str) -> SubmissionStatus:
        """
        Get current status of submission.

        Args:
            submission_id: Platform submission ID

        Returns:
            Current submission status

        Raises:
            ValueError: If submission not found
        """
        if submission_id not in self._submissions:
            raise ValueError(f"Submission not found: {submission_id}")

        return self._submissions[submission_id].current_status

    def get_submission(self, submission_id: str) -> Optional[TrackedSubmission]:
        """
        Get tracked submission details.

        Args:
            submission_id: Platform submission ID

        Returns:
            TrackedSubmission or None if not found
        """
        return self._submissions.get(submission_id)

    def update_status(
        self,
        submission_id: str,
        new_status: SubmissionStatus,
        platform_data: Optional[dict[str, Any]] = None,
    ) -> StatusUpdate:
        """
        Update submission status from platform data.

        CRITICAL: Only call this with confirmed platform data.
        Do NOT assume or predict status changes.

        Args:
            submission_id: Platform submission ID
            new_status: New status from platform
            platform_data: Platform-specific data

        Returns:
            StatusUpdate record

        Raises:
            ValueError: If submission not found
        """
        if submission_id not in self._submissions:
            raise ValueError(f"Submission not found: {submission_id}")

        tracked = self._submissions[submission_id]
        old_status = tracked.current_status

        update = StatusUpdate(
            submission_id=submission_id,
            old_status=old_status,
            new_status=new_status,
            platform_data=platform_data or {},
        )

        # Update tracked submission
        tracked.current_status = new_status
        tracked.last_updated_at = update.updated_at
        tracked.history.append(update)

        if platform_data:
            tracked.platform_data.update(platform_data)

        return update

    def record_acceptance(
        self,
        submission_id: str,
        bounty_amount: Optional[float] = None,
        platform_data: Optional[dict[str, Any]] = None,
    ) -> StatusUpdate:
        """
        Record submission acceptance.

        Args:
            submission_id: Platform submission ID
            bounty_amount: Bounty amount (if disclosed)
            platform_data: Platform-specific data

        Returns:
            StatusUpdate record

        Raises:
            ValueError: If submission not found
        """
        if submission_id not in self._submissions:
            raise ValueError(f"Submission not found: {submission_id}")

        tracked = self._submissions[submission_id]
        old_status = tracked.current_status

        update = StatusUpdate(
            submission_id=submission_id,
            old_status=old_status,
            new_status=SubmissionStatus.ACCEPTED,
            platform_data=platform_data or {},
            bounty_amount=bounty_amount,
        )

        tracked.current_status = SubmissionStatus.ACCEPTED
        tracked.last_updated_at = update.updated_at
        tracked.bounty_amount = bounty_amount
        tracked.history.append(update)

        if platform_data:
            tracked.platform_data.update(platform_data)

        return update

    def record_rejection(
        self,
        submission_id: str,
        reason: Optional[str] = None,
        platform_data: Optional[dict[str, Any]] = None,
    ) -> StatusUpdate:
        """
        Record submission rejection with reason.

        Args:
            submission_id: Platform submission ID
            reason: Rejection reason (if provided)
            platform_data: Platform-specific data

        Returns:
            StatusUpdate record

        Raises:
            ValueError: If submission not found
        """
        if submission_id not in self._submissions:
            raise ValueError(f"Submission not found: {submission_id}")

        tracked = self._submissions[submission_id]
        old_status = tracked.current_status

        update = StatusUpdate(
            submission_id=submission_id,
            old_status=old_status,
            new_status=SubmissionStatus.REJECTED,
            platform_data=platform_data or {},
            rejection_reason=reason,
        )

        tracked.current_status = SubmissionStatus.REJECTED
        tracked.last_updated_at = update.updated_at
        tracked.rejection_reason = reason
        tracked.history.append(update)

        if platform_data:
            tracked.platform_data.update(platform_data)

        return update

    def record_payment(
        self,
        submission_id: str,
        bounty_amount: float,
        platform_data: Optional[dict[str, Any]] = None,
    ) -> StatusUpdate:
        """
        Record bounty payment.

        Args:
            submission_id: Platform submission ID
            bounty_amount: Bounty amount paid
            platform_data: Platform-specific data

        Returns:
            StatusUpdate record

        Raises:
            ValueError: If submission not found
        """
        if submission_id not in self._submissions:
            raise ValueError(f"Submission not found: {submission_id}")

        tracked = self._submissions[submission_id]
        old_status = tracked.current_status

        update = StatusUpdate(
            submission_id=submission_id,
            old_status=old_status,
            new_status=SubmissionStatus.PAID,
            platform_data=platform_data or {},
            bounty_amount=bounty_amount,
        )

        tracked.current_status = SubmissionStatus.PAID
        tracked.last_updated_at = update.updated_at
        tracked.bounty_amount = bounty_amount
        tracked.history.append(update)

        if platform_data:
            tracked.platform_data.update(platform_data)

        return update

    def get_history(self, submission_id: str) -> list[StatusUpdate]:
        """
        Get complete status history for a submission.

        Args:
            submission_id: Platform submission ID

        Returns:
            List of StatusUpdate records

        Raises:
            ValueError: If submission not found
        """
        if submission_id not in self._submissions:
            raise ValueError(f"Submission not found: {submission_id}")

        return list(self._submissions[submission_id].history)

    def get_all_submissions(self) -> list[TrackedSubmission]:
        """Get all tracked submissions."""
        return list(self._submissions.values())

    def get_by_status(self, status: SubmissionStatus) -> list[TrackedSubmission]:
        """
        Get submissions with a specific status.

        Args:
            status: Status to filter by

        Returns:
            List of TrackedSubmission objects
        """
        return [s for s in self._submissions.values() if s.current_status == status]

    def get_pending(self) -> list[TrackedSubmission]:
        """Get submissions that are still pending (not accepted/rejected/paid)."""
        terminal_statuses = {
            SubmissionStatus.ACCEPTED,
            SubmissionStatus.REJECTED,
            SubmissionStatus.PAID,
        }
        return [
            s for s in self._submissions.values()
            if s.current_status not in terminal_statuses
        ]

    @property
    def total_count(self) -> int:
        """Get total number of tracked submissions."""
        return len(self._submissions)

    @property
    def accepted_count(self) -> int:
        """Get number of accepted submissions."""
        return len(self.get_by_status(SubmissionStatus.ACCEPTED))

    @property
    def rejected_count(self) -> int:
        """Get number of rejected submissions."""
        return len(self.get_by_status(SubmissionStatus.REJECTED))

    @property
    def paid_count(self) -> int:
        """Get number of paid submissions."""
        return len(self.get_by_status(SubmissionStatus.PAID))

    @property
    def total_bounty(self) -> float:
        """Get total bounty amount from paid submissions."""
        return sum(
            s.bounty_amount or 0.0
            for s in self._submissions.values()
            if s.bounty_amount is not None
        )
