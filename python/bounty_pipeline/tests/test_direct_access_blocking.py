"""
Property Test: Blocking Direct SubmissionManager Access

**Feature: bounty-pipeline**
**Property: Direct SubmissionManager access is blocked**
**Validates: Requirements 3.1, 3.5, 11.2**

This test validates that direct access to SubmissionManager
(bypassing the BountyPipeline orchestrator) is blocked.

ARCHITECTURAL CONSTRAINT:
All submissions MUST go through the BountyPipeline orchestrator
which enforces:
- MCP proof validation
- Legal scope validation
- Human approval requirement
- Audit trail recording

Direct SubmissionManager access attempts MUST fail because:
1. ApprovalToken requires human approval through HumanReviewGate
2. SubmissionDraft must be in APPROVED status
3. Token must match draft content (hash verification)
4. Token must not be expired
"""

import pytest
from datetime import datetime, timezone, timedelta
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock

from bounty_pipeline.submission import SubmissionManager
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
)
from bounty_pipeline.errors import HumanApprovalRequired, PlatformError
from bounty_pipeline.adapters import (
    GenericMarkdownAdapter,
    PlatformType,
    EncryptedCredentials,
)


# =============================================================================
# Test Fixtures
# =============================================================================


def make_proof_chain() -> ProofChain:
    """Create a valid proof chain for testing."""
    return ProofChain(
        before_state={"key": "value", "target": "https://example.com/api/test"},
        action_sequence=[{"action": "test", "target": "https://example.com/api/test"}],
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


def make_draft(status: DraftStatus = DraftStatus.PENDING_REVIEW) -> SubmissionDraft:
    """Create a submission draft for testing."""
    return SubmissionDraft(
        draft_id="draft-001",
        finding=make_validated_finding(),
        platform="generic",
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
        status=status,
    )


def make_adapter_and_session():
    """Create adapter and session for testing."""
    adapter = GenericMarkdownAdapter()
    master_secret = b"test_secret_32_bytes_long_xxxxx"
    creds = EncryptedCredentials.encrypt(
        PlatformType.GENERIC, "key", "secret", master_secret
    )
    session = adapter.authenticate(creds, master_secret)
    return adapter, session


# =============================================================================
# Property Test: Direct SubmissionManager Access Blocked
# =============================================================================


class TestDirectSubmissionManagerAccessBlocked:
    """
    **Property: Direct SubmissionManager access is blocked**
    **Validates: Requirements 3.1, 3.5, 11.2**

    For any attempt to use SubmissionManager directly (bypassing
    BountyPipeline), the system SHALL reject the submission because:
    - Unapproved drafts are rejected
    - Fabricated tokens are rejected (hash mismatch)
    - Expired tokens are rejected
    - Modified drafts after approval are rejected

    This ensures ALL submissions MUST go through the proper
    human approval workflow.
    """

    @given(
        title=st.text(min_size=1, max_size=100),
        body=st.text(min_size=1, max_size=500),
    )
    @settings(max_examples=100, deadline=5000)
    def test_unapproved_draft_rejected(self, title: str, body: str):
        """
        **Feature: bounty-pipeline, Property: Direct access blocked - unapproved draft**
        **Validates: Requirements 3.1, 3.5**

        For any draft that is not in APPROVED status, direct submission
        to SubmissionManager SHALL be rejected with HumanApprovalRequired.
        """
        assume(title.strip())  # Non-empty title
        assume(body.strip())  # Non-empty body

        manager = SubmissionManager()
        draft = make_draft(status=DraftStatus.PENDING_REVIEW)
        draft.report_title = title
        draft.report_body = body

        # Create a token that matches the draft hash but draft is not approved
        token = ApprovalToken(
            token_id="fabricated-token",
            approver_id="attacker",
            approved_at=datetime.now(timezone.utc),
            draft_hash=draft.compute_hash(),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        adapter, session = make_adapter_and_session()

        # Direct access MUST be rejected
        with pytest.raises(HumanApprovalRequired, match="not approved"):
            manager.submit(draft, token, adapter, session)

    @given(
        hours_expired=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=100, deadline=5000)
    def test_expired_token_rejected(self, hours_expired: int):
        """
        **Feature: bounty-pipeline, Property: Direct access blocked - expired token**
        **Validates: Requirements 3.5**

        For any expired ApprovalToken, direct submission to
        SubmissionManager SHALL be rejected with HumanApprovalRequired.
        """
        manager = SubmissionManager()
        draft = make_draft(status=DraftStatus.APPROVED)
        draft.approval_token_id = "token-123"

        # Create an expired token
        now = datetime.now(timezone.utc)
        token = ApprovalToken(
            token_id="expired-token",
            approver_id="human",
            approved_at=now - timedelta(hours=hours_expired + 1),
            draft_hash=draft.compute_hash(),
            expires_at=now - timedelta(hours=hours_expired),
        )

        adapter, session = make_adapter_and_session()

        # Direct access with expired token MUST be rejected
        with pytest.raises(HumanApprovalRequired, match="expired"):
            manager.submit(draft, token, adapter, session)

    @given(
        modification=st.text(min_size=1, max_size=50),
    )
    @settings(max_examples=100, deadline=5000)
    def test_modified_draft_after_approval_rejected(self, modification: str):
        """
        **Feature: bounty-pipeline, Property: Direct access blocked - modified draft**
        **Validates: Requirements 3.5, 11.2**

        For any draft modified after approval, direct submission to
        SubmissionManager SHALL be rejected because the token hash
        no longer matches the draft content.
        """
        assume(modification.strip())  # Non-empty modification

        manager = SubmissionManager()
        draft = make_draft(status=DraftStatus.APPROVED)
        draft.approval_token_id = "token-123"

        # Create a valid token for the original draft
        original_hash = draft.compute_hash()
        token = ApprovalToken(
            token_id="valid-token",
            approver_id="human",
            approved_at=datetime.now(timezone.utc),
            draft_hash=original_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        # Modify the draft after approval (tampering attempt)
        draft.report_title = f"Modified: {modification}"

        adapter, session = make_adapter_and_session()

        # Direct access with modified draft MUST be rejected
        with pytest.raises(HumanApprovalRequired, match="does not match"):
            manager.submit(draft, token, adapter, session)

    @given(
        fake_hash=st.text(min_size=10, max_size=64, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'))),
    )
    @settings(max_examples=100, deadline=5000)
    def test_fabricated_token_rejected(self, fake_hash: str):
        """
        **Feature: bounty-pipeline, Property: Direct access blocked - fabricated token**
        **Validates: Requirements 3.1, 3.5, 11.2**

        For any fabricated ApprovalToken (with incorrect hash),
        direct submission to SubmissionManager SHALL be rejected.
        """
        manager = SubmissionManager()
        draft = make_draft(status=DraftStatus.APPROVED)
        draft.approval_token_id = "token-123"

        # Create a fabricated token with wrong hash
        token = ApprovalToken(
            token_id="fabricated-token",
            approver_id="attacker",
            approved_at=datetime.now(timezone.utc),
            draft_hash=fake_hash,  # Wrong hash
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        adapter, session = make_adapter_and_session()

        # Direct access with fabricated token MUST be rejected
        with pytest.raises(HumanApprovalRequired, match="does not match"):
            manager.submit(draft, token, adapter, session)

    def test_queue_also_requires_valid_token(self):
        """
        **Feature: bounty-pipeline, Property: Direct access blocked - queue**
        **Validates: Requirements 3.1, 3.5**

        Even queueing for retry requires a valid ApprovalToken.
        Direct queue access with invalid token SHALL be rejected.
        """
        manager = SubmissionManager()
        draft = make_draft(status=DraftStatus.PENDING_REVIEW)

        # Create a token for unapproved draft
        token = ApprovalToken(
            token_id="fabricated-token",
            approver_id="attacker",
            approved_at=datetime.now(timezone.utc),
            draft_hash=draft.compute_hash(),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        # Direct queue access MUST be rejected
        with pytest.raises(HumanApprovalRequired, match="not approved"):
            manager.queue_for_retry(draft, token, "test reason")

    @given(
        status=st.sampled_from([
            DraftStatus.PENDING_REVIEW,
            DraftStatus.REJECTED,
            DraftStatus.SUBMITTED,
        ])
    )
    @settings(max_examples=100, deadline=5000)
    def test_non_approved_status_rejected(self, status: DraftStatus):
        """
        **Feature: bounty-pipeline, Property: Direct access blocked - wrong status**
        **Validates: Requirements 3.1, 3.5, 11.2**

        For any draft with status other than APPROVED, direct submission
        to SubmissionManager SHALL be rejected.
        """
        manager = SubmissionManager()
        draft = make_draft(status=status)

        # Create a token that matches the draft hash
        token = ApprovalToken(
            token_id="token",
            approver_id="human",
            approved_at=datetime.now(timezone.utc),
            draft_hash=draft.compute_hash(),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        adapter, session = make_adapter_and_session()

        # Direct access MUST be rejected for non-APPROVED status
        with pytest.raises(HumanApprovalRequired, match="not approved"):
            manager.submit(draft, token, adapter, session)


class TestOnlyPipelineCanProvideValidToken:
    """
    Tests that valid ApprovalTokens can ONLY be obtained through
    the proper BountyPipeline workflow.
    """

    def test_approval_token_requires_review_gate(self):
        """
        ApprovalToken.generate() creates tokens, but the proper workflow
        requires going through HumanReviewGate which tracks review requests.
        """
        from bounty_pipeline.review import HumanReviewGate

        gate = HumanReviewGate()
        draft = make_draft(status=DraftStatus.PENDING_REVIEW)

        # Request review through proper channel
        request = gate.request_review(draft)
        assert request.request_id

        # Approve through proper channel
        token = gate.approve(request.request_id, "human-reviewer")

        # Token is valid and matches draft
        assert not token.is_expired
        assert token.matches_draft(draft)

        # Draft status is now APPROVED
        assert draft.status == DraftStatus.APPROVED

    def test_direct_token_generation_without_review_fails(self):
        """
        Even if someone generates a token directly, the draft status
        check will fail because the draft was never properly approved.
        """
        manager = SubmissionManager()
        draft = make_draft(status=DraftStatus.PENDING_REVIEW)

        # Generate token directly (bypassing review gate)
        token = ApprovalToken.generate("attacker", draft)

        adapter, session = make_adapter_and_session()

        # Submission fails because draft status is not APPROVED
        with pytest.raises(HumanApprovalRequired, match="not approved"):
            manager.submit(draft, token, adapter, session)

