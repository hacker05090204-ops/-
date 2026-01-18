"""
Human Review Gate - Mandatory checkpoint requiring human approval.

This module implements the human review gate that blocks all submissions
until a human explicitly approves them. This is a NON-NEGOTIABLE requirement.

CRITICAL: NO submission proceeds without human approval.
This is the core safety mechanism of Bounty Pipeline.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import secrets

from bounty_pipeline.errors import HumanApprovalRequired, ArchitecturalViolationError
from bounty_pipeline.types import (
    SubmissionDraft,
    ApprovalToken,
    DraftStatus,
)


class ReviewDecision(str, Enum):
    """Human review decision."""

    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_EDIT = "needs_edit"
    PENDING = "pending"


@dataclass
class ReviewRequest:
    """Request for human review."""

    request_id: str
    draft: SubmissionDraft
    requested_at: datetime
    status: ReviewDecision = ReviewDecision.PENDING
    reviewer_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    edit_instructions: Optional[str] = None


@dataclass
class ArchivedDraft:
    """Draft that was rejected and archived."""

    draft: SubmissionDraft
    rejection_reason: str
    rejected_by: str
    rejected_at: datetime
    archive_id: str


class HumanReviewGate:
    """
    Mandatory checkpoint requiring human approval before submission.

    This gate ensures:
    - All submissions are reviewed by a human
    - Approval tokens are one-time and expiring
    - Rejected drafts are archived
    - No bypass is possible

    ARCHITECTURAL CONSTRAINT:
    This gate CANNOT be bypassed. Human approval is MANDATORY.
    Any attempt to bypass raises ArchitecturalViolationError.
    """

    def __init__(self, token_validity_minutes: int = 30) -> None:
        """
        Initialize the review gate.

        Args:
            token_validity_minutes: How long approval tokens are valid
        """
        self._token_validity_minutes = token_validity_minutes
        self._pending_reviews: dict[str, ReviewRequest] = {}
        self._used_tokens: set[str] = set()  # Track used tokens
        self._archived_drafts: dict[str, ArchivedDraft] = {}

    def request_review(self, draft: SubmissionDraft) -> ReviewRequest:
        """
        Request human review of submission draft.

        Args:
            draft: The submission draft to review

        Returns:
            ReviewRequest for tracking the review
        """
        request_id = secrets.token_urlsafe(16)
        request = ReviewRequest(
            request_id=request_id,
            draft=draft,
            requested_at=datetime.now(timezone.utc),
        )
        self._pending_reviews[request_id] = request
        return request

    def await_approval(self, request: ReviewRequest) -> ApprovalToken:
        """
        Block until human approves or rejects.

        Args:
            request: The review request

        Returns:
            ApprovalToken if approved

        Raises:
            HumanApprovalRequired: If approval not yet given
        """
        if request.status == ReviewDecision.PENDING:
            raise HumanApprovalRequired(
                f"Review request {request.request_id} is pending human approval. "
                f"Draft: {request.draft.report_title}"
            )

        if request.status == ReviewDecision.REJECTED:
            raise HumanApprovalRequired(
                f"Review request {request.request_id} was rejected. "
                f"Reason: {request.rejection_reason}"
            )

        if request.status == ReviewDecision.NEEDS_EDIT:
            raise HumanApprovalRequired(
                f"Review request {request.request_id} needs editing. "
                f"Instructions: {request.edit_instructions}"
            )

        if request.status != ReviewDecision.APPROVED:
            raise HumanApprovalRequired(
                f"Review request {request.request_id} has unexpected status: {request.status}"
            )

        # Generate approval token
        return ApprovalToken.generate(
            approver_id=request.reviewer_id or "unknown",
            draft=request.draft,
            validity_minutes=self._token_validity_minutes,
        )

    def approve(
        self, request_id: str, reviewer_id: str
    ) -> ApprovalToken:
        """
        Human approves a review request.

        Args:
            request_id: The review request ID
            reviewer_id: ID of the human approving

        Returns:
            ApprovalToken for submission

        Raises:
            ValueError: If request not found
        """
        if request_id not in self._pending_reviews:
            raise ValueError(f"Review request {request_id} not found")

        request = self._pending_reviews[request_id]
        request.status = ReviewDecision.APPROVED
        request.reviewer_id = reviewer_id
        request.reviewed_at = datetime.now(timezone.utc)

        # Update draft status
        request.draft.status = DraftStatus.APPROVED
        request.draft.approved_at = request.reviewed_at

        # Generate token
        token = ApprovalToken.generate(
            approver_id=reviewer_id,
            draft=request.draft,
            validity_minutes=self._token_validity_minutes,
        )

        request.draft.approval_token_id = token.token_id

        return token

    def reject(
        self, request_id: str, reviewer_id: str, reason: str
    ) -> ArchivedDraft:
        """
        Human rejects a review request.

        Args:
            request_id: The review request ID
            reviewer_id: ID of the human rejecting
            reason: Reason for rejection

        Returns:
            ArchivedDraft with rejection details

        Raises:
            ValueError: If request not found
        """
        if request_id not in self._pending_reviews:
            raise ValueError(f"Review request {request_id} not found")

        request = self._pending_reviews[request_id]
        request.status = ReviewDecision.REJECTED
        request.reviewer_id = reviewer_id
        request.reviewed_at = datetime.now(timezone.utc)
        request.rejection_reason = reason

        # Update draft status
        request.draft.status = DraftStatus.REJECTED
        request.draft.rejection_reason = reason

        # Archive the draft
        archived = self.archive_rejected(request.draft, reason, reviewer_id)

        # Remove from pending
        del self._pending_reviews[request_id]

        return archived

    def request_edit(
        self, request_id: str, reviewer_id: str, instructions: str
    ) -> ReviewRequest:
        """
        Human requests edits to a draft.

        Args:
            request_id: The review request ID
            reviewer_id: ID of the human requesting edits
            instructions: Edit instructions

        Returns:
            Updated ReviewRequest

        Raises:
            ValueError: If request not found
        """
        if request_id not in self._pending_reviews:
            raise ValueError(f"Review request {request_id} not found")

        request = self._pending_reviews[request_id]
        request.status = ReviewDecision.NEEDS_EDIT
        request.reviewer_id = reviewer_id
        request.reviewed_at = datetime.now(timezone.utc)
        request.edit_instructions = instructions

        return request

    def validate_token(self, token: ApprovalToken, draft: SubmissionDraft) -> bool:
        """
        Validate approval token matches draft and hasn't expired.

        Args:
            token: The approval token
            draft: The submission draft

        Returns:
            True if token is valid

        Raises:
            HumanApprovalRequired: If token is invalid or expired
        """
        # Check if token was already used
        if token.token_id in self._used_tokens:
            raise HumanApprovalRequired(
                f"Approval token {token.token_id} has already been used. "
                f"Tokens are one-time use only."
            )

        # Check expiry
        if token.is_expired:
            raise HumanApprovalRequired(
                f"Approval token {token.token_id} has expired. "
                f"Request new approval."
            )

        # Check draft match
        if not token.matches_draft(draft):
            raise HumanApprovalRequired(
                f"Approval token {token.token_id} does not match draft. "
                f"Draft may have been modified after approval."
            )

        return True

    def consume_token(self, token: ApprovalToken) -> None:
        """
        Mark token as used (one-time use).

        Args:
            token: The token to consume
        """
        self._used_tokens.add(token.token_id)

    def archive_rejected(
        self, draft: SubmissionDraft, reason: str, rejected_by: str = "system"
    ) -> ArchivedDraft:
        """
        Archive rejected draft without submission.

        Args:
            draft: The rejected draft
            reason: Rejection reason
            rejected_by: Who rejected it

        Returns:
            ArchivedDraft with rejection details
        """
        archive_id = secrets.token_urlsafe(16)
        archived = ArchivedDraft(
            draft=draft,
            rejection_reason=reason,
            rejected_by=rejected_by,
            rejected_at=datetime.now(timezone.utc),
            archive_id=archive_id,
        )
        self._archived_drafts[archive_id] = archived
        return archived

    def get_pending_reviews(self) -> list[ReviewRequest]:
        """Get all pending review requests."""
        return [r for r in self._pending_reviews.values() if r.status == ReviewDecision.PENDING]

    def get_archived_drafts(self) -> list[ArchivedDraft]:
        """Get all archived (rejected) drafts."""
        return list(self._archived_drafts.values())

    # =========================================================================
    # ARCHITECTURAL BOUNDARY ENFORCEMENT
    # =========================================================================

    def bypass_review(self, *args, **kwargs) -> None:
        """
        FORBIDDEN: Cannot bypass human review.

        Raises:
            ArchitecturalViolationError: Always - human approval is mandatory
        """
        raise ArchitecturalViolationError(
            "Cannot bypass human review. "
            "Human approval is MANDATORY for all submissions. "
            "This is a non-negotiable safety requirement."
        )

    def auto_approve(self, *args, **kwargs) -> None:
        """
        FORBIDDEN: Cannot auto-approve submissions.

        Raises:
            ArchitecturalViolationError: Always - human approval is mandatory
        """
        raise ArchitecturalViolationError(
            "Cannot auto-approve submissions. "
            "Human approval is MANDATORY for all submissions. "
            "Automated approval is not permitted."
        )

    def submit_without_approval(self, *args, **kwargs) -> None:
        """
        FORBIDDEN: Cannot submit without approval.

        Raises:
            ArchitecturalViolationError: Always - human approval is mandatory
        """
        raise ArchitecturalViolationError(
            "Cannot submit without human approval. "
            "All submissions MUST be approved by a human. "
            "This is a non-negotiable safety requirement."
        )
