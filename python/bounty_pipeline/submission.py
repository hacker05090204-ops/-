"""
Submission Manager - Handles platform API interactions for report submission.

This module manages the submission of approved reports to bug bounty platforms.

CRITICAL CONSTRAINTS:
- REQUIRES valid ApprovalToken for ALL submissions
- NO submission without human approval
- Retries with exponential backoff (max 3 times)
- Queues submissions when API unavailable
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import time

from bounty_pipeline.types import (
    SubmissionDraft,
    ApprovalToken,
    SubmissionReceipt,
    DraftStatus,
)
from bounty_pipeline.errors import (
    HumanApprovalRequired,
    SubmissionFailedError,
    PlatformError,
)
from bounty_pipeline.adapters import (
    PlatformAdapter,
    AuthSession,
    get_adapter,
)


class QueuedSubmissionStatus(str, Enum):
    """Status of a queued submission."""

    PENDING = "pending"
    RETRYING = "retrying"
    FAILED = "failed"
    COMPLETED = "completed"


@dataclass
class QueuedSubmission:
    """Submission queued for retry."""

    queue_id: str
    draft: SubmissionDraft
    token: ApprovalToken
    reason: str
    retry_count: int = 0
    max_retries: int = 3
    queued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_attempt_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None
    status: QueuedSubmissionStatus = QueuedSubmissionStatus.PENDING
    last_error: Optional[str] = None

    @property
    def can_retry(self) -> bool:
        """Check if submission can be retried."""
        return (
            self.retry_count < self.max_retries
            and self.status in (QueuedSubmissionStatus.PENDING, QueuedSubmissionStatus.RETRYING)
            and not self.token.is_expired
        )

    def compute_backoff_seconds(self) -> float:
        """Compute exponential backoff delay in seconds."""
        # Exponential backoff: 2^retry_count seconds (1, 2, 4, ...)
        return float(2 ** self.retry_count)


class SubmissionManager:
    """
    Manages submission of approved reports to platforms.

    CRITICAL: ALL submissions REQUIRE a valid ApprovalToken.
    There are NO exceptions to this rule.

    Features:
    - Validates approval token before submission
    - Retries with exponential backoff (max 3 times)
    - Queues submissions when platform unavailable
    - Records all submission attempts
    """

    def __init__(self, max_retries: int = 3) -> None:
        """
        Initialize submission manager.

        Args:
            max_retries: Maximum retry attempts (default 3)
        """
        self._max_retries = max_retries
        self._queue: dict[str, QueuedSubmission] = {}
        self._receipts: dict[str, SubmissionReceipt] = {}
        self._queue_counter = 0

    def submit(
        self,
        draft: SubmissionDraft,
        token: ApprovalToken,
        adapter: PlatformAdapter,
        session: AuthSession,
    ) -> SubmissionReceipt:
        """
        Submit approved draft to platform.

        Args:
            draft: The submission draft
            token: Valid human approval token (REQUIRED)
            adapter: Platform adapter to use
            session: Authenticated session

        Returns:
            SubmissionReceipt confirming submission

        Raises:
            HumanApprovalRequired: If token is invalid or expired
            SubmissionFailedError: If submission fails after retries
        """
        # CRITICAL: Validate approval token
        self._validate_token(token, draft)

        # Attempt submission with retries
        last_error: Optional[Exception] = None

        for attempt in range(self._max_retries + 1):
            try:
                receipt = adapter.submit_report(draft, session)

                # Mark draft as submitted
                draft.status = DraftStatus.SUBMITTED

                # Store receipt
                self._receipts[receipt.submission_id] = receipt

                return receipt

            except PlatformError as e:
                last_error = e

                if attempt < self._max_retries:
                    # Exponential backoff
                    backoff = 2 ** attempt
                    time.sleep(backoff)
                else:
                    # Max retries exceeded
                    break

        # All retries failed
        raise SubmissionFailedError(
            f"Submission failed after {self._max_retries + 1} attempts. "
            f"Last error: {last_error}"
        )

    def submit_with_retry(
        self,
        draft: SubmissionDraft,
        token: ApprovalToken,
        adapter: PlatformAdapter,
        session: AuthSession,
        sleep_func=time.sleep,
    ) -> SubmissionReceipt:
        """
        Submit with explicit retry control (for testing).

        Args:
            draft: The submission draft
            token: Valid human approval token (REQUIRED)
            adapter: Platform adapter to use
            session: Authenticated session
            sleep_func: Sleep function (for testing)

        Returns:
            SubmissionReceipt confirming submission

        Raises:
            HumanApprovalRequired: If token is invalid or expired
            SubmissionFailedError: If submission fails after retries
        """
        # CRITICAL: Validate approval token
        self._validate_token(token, draft)

        last_error: Optional[Exception] = None

        for attempt in range(self._max_retries + 1):
            try:
                receipt = adapter.submit_report(draft, session)
                draft.status = DraftStatus.SUBMITTED
                self._receipts[receipt.submission_id] = receipt
                return receipt

            except PlatformError as e:
                last_error = e

                if attempt < self._max_retries:
                    backoff = 2 ** attempt
                    sleep_func(backoff)
                else:
                    break

        raise SubmissionFailedError(
            f"Submission failed after {self._max_retries + 1} attempts. "
            f"Last error: {last_error}"
        )

    def queue_for_retry(
        self,
        draft: SubmissionDraft,
        token: ApprovalToken,
        reason: str,
    ) -> QueuedSubmission:
        """
        Queue submission for later retry.

        Args:
            draft: The submission draft
            token: Valid approval token
            reason: Reason for queueing

        Returns:
            QueuedSubmission object

        Raises:
            HumanApprovalRequired: If token is invalid or expired
        """
        # Validate token
        self._validate_token(token, draft)

        self._queue_counter += 1
        queue_id = f"queue-{self._queue_counter:06d}"

        queued = QueuedSubmission(
            queue_id=queue_id,
            draft=draft,
            token=token,
            reason=reason,
            max_retries=self._max_retries,
        )

        self._queue[queue_id] = queued
        return queued

    def get_queued(self) -> list[QueuedSubmission]:
        """Get all queued submissions awaiting retry."""
        return list(self._queue.values())

    def get_pending_queued(self) -> list[QueuedSubmission]:
        """Get queued submissions that can still be retried."""
        return [q for q in self._queue.values() if q.can_retry]

    def process_queued(
        self,
        queue_id: str,
        adapter: PlatformAdapter,
        session: AuthSession,
    ) -> Optional[SubmissionReceipt]:
        """
        Process a queued submission.

        Args:
            queue_id: ID of queued submission
            adapter: Platform adapter
            session: Authenticated session

        Returns:
            SubmissionReceipt if successful, None if failed

        Raises:
            ValueError: If queue_id not found
            HumanApprovalRequired: If token expired
        """
        if queue_id not in self._queue:
            raise ValueError(f"Queue ID not found: {queue_id}")

        queued = self._queue[queue_id]

        # Check if token expired
        if queued.token.is_expired:
            queued.status = QueuedSubmissionStatus.FAILED
            queued.last_error = "Approval token expired"
            raise HumanApprovalRequired(
                "Approval token has expired. New human approval required."
            )

        # Check if can retry
        if not queued.can_retry:
            return None

        queued.status = QueuedSubmissionStatus.RETRYING
        queued.last_attempt_at = datetime.now(timezone.utc)
        queued.retry_count += 1

        try:
            receipt = adapter.submit_report(queued.draft, session)
            queued.draft.status = DraftStatus.SUBMITTED
            queued.status = QueuedSubmissionStatus.COMPLETED
            self._receipts[receipt.submission_id] = receipt
            return receipt

        except PlatformError as e:
            queued.last_error = str(e)

            if queued.can_retry:
                # Schedule next retry
                from datetime import timedelta
                backoff = queued.compute_backoff_seconds()
                queued.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=backoff)
            else:
                queued.status = QueuedSubmissionStatus.FAILED

            return None

    def get_receipt(self, submission_id: str) -> Optional[SubmissionReceipt]:
        """Get receipt for a submission."""
        return self._receipts.get(submission_id)

    def _validate_token(self, token: ApprovalToken, draft: SubmissionDraft) -> None:
        """
        Validate approval token.

        CRITICAL: This is the enforcement point for human approval.

        Raises:
            HumanApprovalRequired: If token is invalid
        """
        # Check token expiry
        if token.is_expired:
            raise HumanApprovalRequired(
                "Approval token has expired. New human approval required."
            )

        # Check token matches draft
        if not token.matches_draft(draft):
            raise HumanApprovalRequired(
                "Approval token does not match draft content. "
                "Draft may have been modified after approval. "
                "New human approval required."
            )

        # Check draft status
        if draft.status != DraftStatus.APPROVED:
            raise HumanApprovalRequired(
                f"Draft status is {draft.status.value}, not approved. "
                "Human approval required before submission."
            )

    @property
    def queue_size(self) -> int:
        """Get number of queued submissions."""
        return len(self._queue)

    @property
    def pending_count(self) -> int:
        """Get number of pending submissions."""
        return len(self.get_pending_queued())
