"""
Tests for Submission Manager.

**Feature: bounty-pipeline**

Property tests validate:
- Property 7: Retry Behavior (exponential backoff, max 3 retries)
- Property 4: Human Approval Enforcement (requires valid token)
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch
from hypothesis import given, strategies as st, settings

from bounty_pipeline.submission import (
    SubmissionManager,
    QueuedSubmission,
    QueuedSubmissionStatus,
)
from bounty_pipeline.types import (
    SubmissionDraft,
    ValidatedFinding,
    MCPFinding,
    MCPClassification,
    ProofChain,
    SourceLinks,
    ReproductionStep,
    DraftStatus,
    ApprovalToken,
    SubmissionReceipt,
)
from bounty_pipeline.errors import (
    HumanApprovalRequired,
    SubmissionFailedError,
    PlatformError,
)
from bounty_pipeline.adapters import (
    PlatformType,
    AuthSession,
    HackerOneAdapter,
)


# =============================================================================
# Test Fixtures
# =============================================================================


def make_proof_chain() -> ProofChain:
    """Create a valid proof chain for testing."""
    return ProofChain(
        before_state={"key": "value"},
        action_sequence=[{"action": "test"}],
        after_state={"key": "changed"},
        causality_chain=[{"cause": "effect"}],
        replay_instructions=[{"step": 1}],
        invariant_violated="test_invariant",
        proof_hash="abc123",
    )


def make_mcp_finding() -> MCPFinding:
    """Create a valid MCP finding for testing."""
    return MCPFinding(
        finding_id="test-finding-001",
        classification=MCPClassification.BUG,
        invariant_violated="test_invariant",
        proof=make_proof_chain(),
        severity="high",
        cyfer_brain_observation_id="obs-001",
        timestamp=datetime.now(timezone.utc),
    )


def make_validated_finding() -> ValidatedFinding:
    """Create a validated finding for testing."""
    mcp_finding = make_mcp_finding()
    return ValidatedFinding(
        finding_id=mcp_finding.finding_id,
        mcp_finding=mcp_finding,
        proof_chain=mcp_finding.proof,
        source_links=SourceLinks(
            mcp_proof_id=mcp_finding.finding_id,
            mcp_proof_hash=mcp_finding.proof.proof_hash,
            cyfer_brain_observation_id=mcp_finding.cyfer_brain_observation_id,
        ),
    )


def make_draft() -> SubmissionDraft:
    """Create a submission draft for testing."""
    return SubmissionDraft(
        draft_id="draft-001",
        finding=make_validated_finding(),
        platform="hackerone",
        report_title="Test Vulnerability Report",
        report_body="This is a test vulnerability report.",
        severity="high",
        reproduction_steps=[
            ReproductionStep(
                step_number=1,
                action="Navigate to target",
                expected_result="Page loads",
            )
        ],
        proof_summary="Proof summary here",
    )


def make_approved_draft() -> SubmissionDraft:
    """Create an approved submission draft for testing."""
    draft = make_draft()
    draft.status = DraftStatus.APPROVED
    draft.approval_token_id = "token-123"
    return draft


def make_valid_token(draft: SubmissionDraft) -> ApprovalToken:
    """Create a valid approval token for a draft."""
    return ApprovalToken.generate(
        approver_id="human-reviewer-001",
        draft=draft,
        validity_minutes=30,
    )


def make_expired_token(draft: SubmissionDraft) -> ApprovalToken:
    """Create an expired approval token."""
    now = datetime.now(timezone.utc)
    return ApprovalToken(
        token_id="expired-token",
        approver_id="human-reviewer-001",
        approved_at=now - timedelta(hours=2),
        draft_hash=draft.compute_hash(),
        expires_at=now - timedelta(hours=1),
    )


def make_session() -> AuthSession:
    """Create a valid auth session."""
    now = datetime.now(timezone.utc)
    return AuthSession(
        platform=PlatformType.HACKERONE,
        session_id="sess-123",
        authenticated_at=now,
        expires_at=now + timedelta(hours=1),
        _token="test-token",
    )


def make_receipt() -> SubmissionReceipt:
    """Create a submission receipt."""
    return SubmissionReceipt(
        platform="hackerone",
        submission_id="h1-test-123",
        submitted_at=datetime.now(timezone.utc),
        receipt_data={"id": "h1-test-123"},
        receipt_hash="abc123",
    )


# =============================================================================
# Property 7: Retry Behavior Tests
# =============================================================================


class TestRetryBehavior:
    """
    **Property 7: Retry Behavior**
    **Validates: Requirements 5.3**

    For any failed submission, the system SHALL retry with
    exponential backoff up to 3 times before failing.
    """

    def test_successful_submission_no_retry(self):
        """Successful submission doesn't retry."""
        manager = SubmissionManager(max_retries=3)
        draft = make_approved_draft()
        token = make_valid_token(draft)
        session = make_session()

        adapter = Mock()
        adapter.submit_report.return_value = make_receipt()

        receipt = manager.submit(draft, token, adapter, session)

        assert receipt is not None
        assert adapter.submit_report.call_count == 1

    def test_retry_on_platform_error(self):
        """Platform errors trigger retry."""
        manager = SubmissionManager(max_retries=3)
        draft = make_approved_draft()
        token = make_valid_token(draft)
        session = make_session()

        adapter = Mock()
        # Fail twice, then succeed
        adapter.submit_report.side_effect = [
            PlatformError("Network error"),
            PlatformError("Timeout"),
            make_receipt(),
        ]

        sleep_calls = []
        def mock_sleep(seconds):
            sleep_calls.append(seconds)

        receipt = manager.submit_with_retry(draft, token, adapter, session, sleep_func=mock_sleep)

        assert receipt is not None
        assert adapter.submit_report.call_count == 3
        # Exponential backoff: 2^0=1, 2^1=2
        assert sleep_calls == [1, 2]

    def test_max_retries_exceeded(self):
        """Submission fails after max retries."""
        manager = SubmissionManager(max_retries=3)
        draft = make_approved_draft()
        token = make_valid_token(draft)
        session = make_session()

        adapter = Mock()
        adapter.submit_report.side_effect = PlatformError("Always fails")

        sleep_calls = []
        def mock_sleep(seconds):
            sleep_calls.append(seconds)

        with pytest.raises(SubmissionFailedError, match="failed after"):
            manager.submit_with_retry(draft, token, adapter, session, sleep_func=mock_sleep)

        # 1 initial + 3 retries = 4 attempts
        assert adapter.submit_report.call_count == 4
        # Exponential backoff: 2^0=1, 2^1=2, 2^2=4
        assert sleep_calls == [1, 2, 4]

    @given(max_retries=st.integers(min_value=1, max_value=5))
    @settings(max_examples=10, deadline=5000)
    def test_retry_count_matches_config(self, max_retries: int):
        """Retry count matches configured max_retries."""
        manager = SubmissionManager(max_retries=max_retries)
        draft = make_approved_draft()
        token = make_valid_token(draft)
        session = make_session()

        adapter = Mock()
        adapter.submit_report.side_effect = PlatformError("Always fails")

        sleep_calls = []
        def mock_sleep(seconds):
            sleep_calls.append(seconds)

        with pytest.raises(SubmissionFailedError):
            manager.submit_with_retry(draft, token, adapter, session, sleep_func=mock_sleep)

        # 1 initial + max_retries = total attempts
        assert adapter.submit_report.call_count == max_retries + 1

    def test_exponential_backoff_values(self):
        """Backoff follows exponential pattern."""
        queued = QueuedSubmission(
            queue_id="q-001",
            draft=make_approved_draft(),
            token=make_valid_token(make_approved_draft()),
            reason="test",
        )

        # Test backoff values for different retry counts
        queued.retry_count = 0
        assert queued.compute_backoff_seconds() == 1.0  # 2^0

        queued.retry_count = 1
        assert queued.compute_backoff_seconds() == 2.0  # 2^1

        queued.retry_count = 2
        assert queued.compute_backoff_seconds() == 4.0  # 2^2

        queued.retry_count = 3
        assert queued.compute_backoff_seconds() == 8.0  # 2^3


# =============================================================================
# Human Approval Enforcement Tests
# =============================================================================


class TestHumanApprovalEnforcement:
    """
    **Property 4: Human Approval Enforcement**
    **Validates: Requirements 3.1, 3.3, 3.5, 11.2**

    For any submission to a bug bounty platform, the system
    SHALL block until human approval is received; no submission
    SHALL proceed without a valid ApprovalToken.
    """

    def test_submission_requires_valid_token(self):
        """Submission requires valid approval token."""
        manager = SubmissionManager()
        draft = make_approved_draft()
        token = make_valid_token(draft)
        session = make_session()

        adapter = Mock()
        adapter.submit_report.return_value = make_receipt()

        # Should succeed with valid token
        receipt = manager.submit(draft, token, adapter, session)
        assert receipt is not None

    def test_expired_token_rejected(self):
        """Expired tokens are rejected."""
        manager = SubmissionManager()
        draft = make_approved_draft()
        token = make_expired_token(draft)
        session = make_session()

        adapter = Mock()

        with pytest.raises(HumanApprovalRequired, match="expired"):
            manager.submit(draft, token, adapter, session)

        # Adapter should never be called
        adapter.submit_report.assert_not_called()

    def test_mismatched_token_rejected(self):
        """Token for different draft is rejected."""
        manager = SubmissionManager()
        draft1 = make_approved_draft()
        draft2 = make_approved_draft()
        draft2.report_title = "Different Title"  # Different content

        token = make_valid_token(draft1)  # Token for draft1
        session = make_session()

        adapter = Mock()

        with pytest.raises(HumanApprovalRequired, match="does not match"):
            manager.submit(draft2, token, adapter, session)

        adapter.submit_report.assert_not_called()

    def test_unapproved_draft_rejected(self):
        """Unapproved drafts are rejected."""
        manager = SubmissionManager()
        draft = make_draft()  # Not approved
        token = make_valid_token(draft)
        session = make_session()

        adapter = Mock()

        with pytest.raises(HumanApprovalRequired, match="not approved"):
            manager.submit(draft, token, adapter, session)

        adapter.submit_report.assert_not_called()

    def test_queue_requires_valid_token(self):
        """Queueing requires valid token."""
        manager = SubmissionManager()
        draft = make_approved_draft()
        token = make_valid_token(draft)

        # Should succeed with valid token
        queued = manager.queue_for_retry(draft, token, "test reason")
        assert queued is not None
        assert queued.queue_id

    def test_queue_rejects_expired_token(self):
        """Queueing rejects expired token."""
        manager = SubmissionManager()
        draft = make_approved_draft()
        token = make_expired_token(draft)

        with pytest.raises(HumanApprovalRequired, match="expired"):
            manager.queue_for_retry(draft, token, "test reason")


# =============================================================================
# Queue Management Tests
# =============================================================================


class TestQueueManagement:
    """Tests for submission queue management."""

    def test_queue_submission(self):
        """Submissions can be queued."""
        manager = SubmissionManager()
        draft = make_approved_draft()
        token = make_valid_token(draft)

        queued = manager.queue_for_retry(draft, token, "Platform unavailable")

        assert queued.queue_id
        assert queued.draft == draft
        assert queued.token == token
        assert queued.reason == "Platform unavailable"
        assert queued.status == QueuedSubmissionStatus.PENDING

    def test_get_queued_submissions(self):
        """Can retrieve queued submissions."""
        manager = SubmissionManager()
        draft1 = make_approved_draft()
        draft2 = make_approved_draft()
        draft2.draft_id = "draft-002"

        token1 = make_valid_token(draft1)
        token2 = make_valid_token(draft2)

        manager.queue_for_retry(draft1, token1, "reason1")
        manager.queue_for_retry(draft2, token2, "reason2")

        queued = manager.get_queued()
        assert len(queued) == 2

    def test_process_queued_success(self):
        """Queued submission can be processed."""
        manager = SubmissionManager()
        draft = make_approved_draft()
        token = make_valid_token(draft)
        session = make_session()

        queued = manager.queue_for_retry(draft, token, "test")

        adapter = Mock()
        adapter.submit_report.return_value = make_receipt()

        receipt = manager.process_queued(queued.queue_id, adapter, session)

        assert receipt is not None
        assert queued.status == QueuedSubmissionStatus.COMPLETED

    def test_process_queued_failure(self):
        """Failed queue processing updates status."""
        manager = SubmissionManager()
        draft = make_approved_draft()
        token = make_valid_token(draft)
        session = make_session()

        queued = manager.queue_for_retry(draft, token, "test")

        adapter = Mock()
        adapter.submit_report.side_effect = PlatformError("Failed")

        receipt = manager.process_queued(queued.queue_id, adapter, session)

        assert receipt is None
        assert queued.retry_count == 1
        assert queued.last_error == "Failed"

    def test_process_queued_expired_token(self):
        """Processing with expired token fails."""
        manager = SubmissionManager()
        draft = make_approved_draft()
        # Create token that will expire
        token = ApprovalToken(
            token_id="will-expire",
            approver_id="human",
            approved_at=datetime.now(timezone.utc) - timedelta(hours=1),
            draft_hash=draft.compute_hash(),
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )

        # Manually add to queue (bypassing validation for test)
        queued = QueuedSubmission(
            queue_id="q-test",
            draft=draft,
            token=token,
            reason="test",
        )
        manager._queue["q-test"] = queued

        adapter = Mock()
        session = make_session()

        with pytest.raises(HumanApprovalRequired, match="expired"):
            manager.process_queued("q-test", adapter, session)

        assert queued.status == QueuedSubmissionStatus.FAILED

    def test_can_retry_logic(self):
        """can_retry correctly evaluates retry eligibility."""
        draft = make_approved_draft()
        token = make_valid_token(draft)

        queued = QueuedSubmission(
            queue_id="q-001",
            draft=draft,
            token=token,
            reason="test",
            max_retries=3,
        )

        # Initially can retry
        assert queued.can_retry

        # After max retries, cannot retry
        queued.retry_count = 3
        assert not queued.can_retry

        # Reset and mark as failed
        queued.retry_count = 0
        queued.status = QueuedSubmissionStatus.FAILED
        assert not queued.can_retry


class TestSubmissionReceipts:
    """Tests for submission receipt handling."""

    def test_receipt_stored_on_success(self):
        """Successful submission stores receipt."""
        manager = SubmissionManager()
        draft = make_approved_draft()
        token = make_valid_token(draft)
        session = make_session()

        expected_receipt = make_receipt()
        adapter = Mock()
        adapter.submit_report.return_value = expected_receipt

        receipt = manager.submit(draft, token, adapter, session)

        stored = manager.get_receipt(receipt.submission_id)
        assert stored == expected_receipt

    def test_receipt_not_stored_on_failure(self):
        """Failed submission doesn't store receipt."""
        manager = SubmissionManager()
        draft = make_approved_draft()
        token = make_valid_token(draft)
        session = make_session()

        adapter = Mock()
        adapter.submit_report.side_effect = PlatformError("Failed")

        with pytest.raises(SubmissionFailedError):
            manager.submit_with_retry(draft, token, adapter, session, sleep_func=lambda x: None)

        # No receipts stored
        assert manager.get_receipt("any-id") is None
