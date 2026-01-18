"""
Property tests for Human Review Gate.

**Feature: bounty-pipeline, Property 4: Human Approval Enforcement**
**Validates: Requirements 3.1, 3.3, 3.5, 11.2**
"""

from datetime import datetime, timedelta, timezone

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from bounty_pipeline.errors import HumanApprovalRequired, ArchitecturalViolationError
from bounty_pipeline.types import (
    MCPClassification,
    MCPFinding,
    ProofChain,
    ValidatedFinding,
    SourceLinks,
    SubmissionDraft,
    ApprovalToken,
    DraftStatus,
)
from bounty_pipeline.review import HumanReviewGate, ReviewDecision


# ============================================================================
# Test Fixtures
# ============================================================================


def create_test_draft() -> SubmissionDraft:
    """Create a test submission draft."""
    proof = ProofChain(
        before_state={},
        action_sequence=[{"action": "test"}],
        after_state={},
        causality_chain=[{"cause": "test"}],
        replay_instructions=[{"step": "test"}],
        invariant_violated="test_invariant",
        proof_hash="a" * 64,
    )

    mcp_finding = MCPFinding(
        finding_id="test-finding",
        classification=MCPClassification.BUG,
        invariant_violated="test_invariant",
        proof=proof,
        severity="high",
        cyfer_brain_observation_id="obs-1",
        timestamp=datetime.now(timezone.utc),
    )

    source_links = SourceLinks(
        mcp_proof_id="test-finding",
        mcp_proof_hash="a" * 64,
        cyfer_brain_observation_id="obs-1",
    )

    validated = ValidatedFinding(
        finding_id="test-finding",
        mcp_finding=mcp_finding,
        proof_chain=proof,
        source_links=source_links,
    )

    return SubmissionDraft(
        draft_id="draft-1",
        finding=validated,
        platform="hackerone",
        report_title="Test XSS Vulnerability",
        report_body="A reflected XSS vulnerability was found...",
        severity="high",
        reproduction_steps=[],
        proof_summary="MCP proof shows invariant violation",
    )


# ============================================================================
# Property Tests
# ============================================================================


class TestHumanApprovalEnforcement:
    """
    Property 4: Human Approval Enforcement

    *For any* submission to a bug bounty platform, the system SHALL block
    until human approval is received; no submission SHALL proceed without
    a valid ApprovalToken.

    **Validates: Requirements 3.1, 3.3, 3.5, 11.2**
    """

    def test_pending_review_blocks(self) -> None:
        """Pending review blocks submission."""
        gate = HumanReviewGate()
        draft = create_test_draft()

        request = gate.request_review(draft)

        # Attempting to get approval should raise
        with pytest.raises(HumanApprovalRequired) as exc_info:
            gate.await_approval(request)

        assert "pending" in str(exc_info.value).lower()

    def test_approval_generates_token(self) -> None:
        """Human approval generates valid token."""
        gate = HumanReviewGate()
        draft = create_test_draft()

        request = gate.request_review(draft)
        token = gate.approve(request.request_id, "reviewer-1")

        assert token is not None
        assert token.approver_id == "reviewer-1"
        assert token.matches_draft(draft)
        assert not token.is_expired

    def test_rejection_archives_draft(self) -> None:
        """Rejection archives draft without submission."""
        gate = HumanReviewGate()
        draft = create_test_draft()

        request = gate.request_review(draft)
        archived = gate.reject(request.request_id, "reviewer-1", "Not a valid vulnerability")

        assert archived is not None
        assert archived.rejection_reason == "Not a valid vulnerability"
        assert archived.rejected_by == "reviewer-1"
        assert draft.status == DraftStatus.REJECTED

    def test_rejected_review_blocks(self) -> None:
        """Rejected review blocks submission."""
        gate = HumanReviewGate()
        draft = create_test_draft()

        request = gate.request_review(draft)
        gate.reject(request.request_id, "reviewer-1", "Invalid")

        # Request is removed after rejection, so we need to check the draft status
        assert draft.status == DraftStatus.REJECTED

    def test_edit_request_blocks(self) -> None:
        """Edit request blocks submission until re-review."""
        gate = HumanReviewGate()
        draft = create_test_draft()

        request = gate.request_review(draft)
        updated = gate.request_edit(request.request_id, "reviewer-1", "Add more details")

        assert updated.status == ReviewDecision.NEEDS_EDIT
        assert updated.edit_instructions == "Add more details"

        # Attempting to get approval should raise
        with pytest.raises(HumanApprovalRequired) as exc_info:
            gate.await_approval(updated)

        assert "needs editing" in str(exc_info.value).lower()


class TestTokenValidation:
    """Test approval token validation."""

    def test_valid_token_passes(self) -> None:
        """Valid token passes validation."""
        gate = HumanReviewGate()
        draft = create_test_draft()

        request = gate.request_review(draft)
        token = gate.approve(request.request_id, "reviewer-1")

        assert gate.validate_token(token, draft) is True

    def test_expired_token_fails(self) -> None:
        """Expired token fails validation."""
        gate = HumanReviewGate()
        draft = create_test_draft()

        # Create an expired token
        now = datetime.now(timezone.utc)
        expired_token = ApprovalToken(
            token_id="expired-token",
            approver_id="reviewer-1",
            approved_at=now - timedelta(hours=2),
            draft_hash=draft.compute_hash(),
            expires_at=now - timedelta(hours=1),  # Expired 1 hour ago
        )

        with pytest.raises(HumanApprovalRequired) as exc_info:
            gate.validate_token(expired_token, draft)

        assert "expired" in str(exc_info.value).lower()

    def test_mismatched_token_fails(self) -> None:
        """Token for different draft fails validation."""
        gate = HumanReviewGate()
        draft1 = create_test_draft()
        draft2 = create_test_draft()
        draft2.report_title = "Different Title"  # Modify to change hash

        request = gate.request_review(draft1)
        token = gate.approve(request.request_id, "reviewer-1")

        with pytest.raises(HumanApprovalRequired) as exc_info:
            gate.validate_token(token, draft2)

        assert "does not match" in str(exc_info.value).lower()

    def test_used_token_fails(self) -> None:
        """Used token fails validation (one-time use)."""
        gate = HumanReviewGate()
        draft = create_test_draft()

        request = gate.request_review(draft)
        token = gate.approve(request.request_id, "reviewer-1")

        # First use should pass
        assert gate.validate_token(token, draft) is True
        gate.consume_token(token)

        # Second use should fail
        with pytest.raises(HumanApprovalRequired) as exc_info:
            gate.validate_token(token, draft)

        assert "already been used" in str(exc_info.value).lower()


class TestArchitecturalBoundaryEnforcement:
    """Test that review gate enforces architectural boundaries."""

    def test_bypass_review_raises_violation(self) -> None:
        """bypass_review raises ArchitecturalViolationError."""
        gate = HumanReviewGate()

        with pytest.raises(ArchitecturalViolationError) as exc_info:
            gate.bypass_review()

        assert "cannot bypass" in str(exc_info.value).lower()
        assert "mandatory" in str(exc_info.value).lower()

    def test_auto_approve_raises_violation(self) -> None:
        """auto_approve raises ArchitecturalViolationError."""
        gate = HumanReviewGate()

        with pytest.raises(ArchitecturalViolationError) as exc_info:
            gate.auto_approve()

        assert "cannot auto-approve" in str(exc_info.value).lower()

    def test_submit_without_approval_raises_violation(self) -> None:
        """submit_without_approval raises ArchitecturalViolationError."""
        gate = HumanReviewGate()

        with pytest.raises(ArchitecturalViolationError) as exc_info:
            gate.submit_without_approval()

        assert "cannot submit without" in str(exc_info.value).lower()


class TestReviewManagement:
    """Test review request management."""

    def test_get_pending_reviews(self) -> None:
        """get_pending_reviews returns only pending requests."""
        gate = HumanReviewGate()

        draft1 = create_test_draft()
        draft2 = create_test_draft()
        draft2.draft_id = "draft-2"

        request1 = gate.request_review(draft1)
        request2 = gate.request_review(draft2)

        # Approve one
        gate.approve(request1.request_id, "reviewer-1")

        pending = gate.get_pending_reviews()
        assert len(pending) == 1
        assert pending[0].request_id == request2.request_id

    def test_get_archived_drafts(self) -> None:
        """get_archived_drafts returns rejected drafts."""
        gate = HumanReviewGate()

        draft = create_test_draft()
        request = gate.request_review(draft)
        gate.reject(request.request_id, "reviewer-1", "Invalid")

        archived = gate.get_archived_drafts()
        assert len(archived) == 1
        assert archived[0].rejection_reason == "Invalid"


class TestTokenGeneration:
    """Test approval token generation."""

    @given(validity_minutes=st.integers(min_value=1, max_value=120))
    @settings(max_examples=50, deadline=5000)
    def test_token_validity_period(self, validity_minutes: int) -> None:
        """Token validity period is respected."""
        gate = HumanReviewGate(token_validity_minutes=validity_minutes)
        draft = create_test_draft()

        request = gate.request_review(draft)
        token = gate.approve(request.request_id, "reviewer-1")

        # Token should not be expired immediately
        assert not token.is_expired

        # Token expiry should be approximately validity_minutes from now
        now = datetime.now(timezone.utc)
        expected_expiry = now + timedelta(minutes=validity_minutes)
        # Allow 1 second tolerance
        assert abs((token.expires_at - expected_expiry).total_seconds()) < 1


class TestApprovalTokenSingleUseEnforcement:
    """
    Property Test: ApprovalToken Single-Use Enforcement

    *For any* ApprovalToken, once consumed, the token SHALL NOT be valid
    for subsequent use; attempting to validate a consumed token SHALL raise
    HumanApprovalRequired.

    **Validates: Requirements 3.5 (one-time, expiring tokens)**
    """

    @given(
        reviewer_id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N'))),
        num_reuse_attempts=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=100, deadline=5000)
    def test_consumed_token_cannot_be_reused(
        self, reviewer_id: str, num_reuse_attempts: int
    ) -> None:
        """
        Property: Once a token is consumed, it cannot be reused.

        *For any* valid ApprovalToken that has been consumed,
        all subsequent validation attempts SHALL fail with HumanApprovalRequired.

        **Feature: bounty-pipeline, Property: ApprovalToken Single-Use Enforcement**
        **Validates: Requirements 3.5**
        """
        gate = HumanReviewGate()
        draft = create_test_draft()

        # Create and approve a review request
        request = gate.request_review(draft)
        token = gate.approve(request.request_id, reviewer_id or "reviewer")

        # First validation should succeed
        assert gate.validate_token(token, draft) is True

        # Consume the token (mark as used)
        gate.consume_token(token)

        # All subsequent validation attempts should fail
        for _ in range(num_reuse_attempts):
            with pytest.raises(HumanApprovalRequired) as exc_info:
                gate.validate_token(token, draft)

            assert "already been used" in str(exc_info.value).lower()
            assert token.token_id in str(exc_info.value)

    @given(
        num_tokens=st.integers(min_value=2, max_value=5),
    )
    @settings(max_examples=50, deadline=5000)
    def test_each_token_is_independently_single_use(self, num_tokens: int) -> None:
        """
        Property: Each token is independently single-use.

        *For any* set of ApprovalTokens, consuming one token SHALL NOT
        affect the validity of other tokens.

        **Feature: bounty-pipeline, Property: ApprovalToken Single-Use Enforcement**
        **Validates: Requirements 3.5**
        """
        gate = HumanReviewGate()

        # Create multiple drafts and tokens
        drafts_and_tokens = []
        for i in range(num_tokens):
            draft = create_test_draft()
            draft.draft_id = f"draft-{i}"
            draft.report_title = f"Test Vulnerability {i}"

            request = gate.request_review(draft)
            token = gate.approve(request.request_id, f"reviewer-{i}")
            drafts_and_tokens.append((draft, token))

        # Consume the first token
        first_draft, first_token = drafts_and_tokens[0]
        gate.consume_token(first_token)

        # First token should now be invalid
        with pytest.raises(HumanApprovalRequired):
            gate.validate_token(first_token, first_draft)

        # All other tokens should still be valid
        for draft, token in drafts_and_tokens[1:]:
            assert gate.validate_token(token, draft) is True

    @given(
        reviewer_id=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'))),
    )
    @settings(max_examples=100, deadline=5000)
    def test_token_single_use_is_idempotent(self, reviewer_id: str) -> None:
        """
        Property: Consuming a token multiple times is idempotent.

        *For any* ApprovalToken, calling consume_token multiple times
        SHALL have the same effect as calling it once - the token remains invalid.

        **Feature: bounty-pipeline, Property: ApprovalToken Single-Use Enforcement**
        **Validates: Requirements 3.5**
        """
        gate = HumanReviewGate()
        draft = create_test_draft()

        request = gate.request_review(draft)
        token = gate.approve(request.request_id, reviewer_id or "reviewer")

        # Consume the token multiple times
        gate.consume_token(token)
        gate.consume_token(token)
        gate.consume_token(token)

        # Token should still be invalid (idempotent)
        with pytest.raises(HumanApprovalRequired) as exc_info:
            gate.validate_token(token, draft)

        assert "already been used" in str(exc_info.value).lower()
