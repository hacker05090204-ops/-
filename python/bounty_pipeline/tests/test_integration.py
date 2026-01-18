"""
Integration Tests for Bounty Pipeline.

**Feature: bounty-pipeline**

Property tests validate:
- End-to-end pipeline respects all boundaries
- All architectural constraints are enforced
- Human approval is mandatory at all submission points
"""

import pytest
from datetime import datetime, timezone, timedelta
from hypothesis import given, strategies as st, settings

from bounty_pipeline import (
    # Main orchestrator
    BountyPipeline,
    # Components
    FindingValidator,
    LegalScopeValidator,
    HumanReviewGate,
    ReportGenerator,
    AuditTrail,
    DuplicateDetector,
    SubmissionManager,
    StatusTracker,
    RecoveryManager,
    ProgramManager,
    # Platform Adapters
    HackerOneAdapter,
    BugcrowdAdapter,
    GenericMarkdownAdapter,
    EncryptedCredentials,
    PlatformType,
    get_adapter,
    # Types
    MCPClassification,
    MCPFinding,
    ValidatedFinding,
    SubmissionDraft,
    ProofChain,
    ApprovalToken,
    AuthorizationDocument,
    DraftStatus,
    SubmissionStatus,
    SourceLinks,
    ReproductionStep,
    # Errors
    FindingValidationError,
    ScopeViolationError,
    HumanApprovalRequired,
    ArchitecturalViolationError,
    SubmissionFailedError,
    is_hard_stop,
)
from bounty_pipeline.program import ProgramPolicy


# =============================================================================
# Test Fixtures
# =============================================================================


def make_proof_chain() -> ProofChain:
    """Create a valid proof chain for testing.
    
    CRITICAL: ProofChain MUST contain target information for scope validation.
    Target is extracted from action_sequence, before_state, after_state, or replay_instructions.
    """
    return ProofChain(
        before_state={"key": "value", "target": "https://example.com/api/test"},
        action_sequence=[{"action": "test", "target": "https://example.com/api/test"}],
        after_state={"key": "changed", "target": "https://example.com/api/test"},
        causality_chain=[{"cause": "effect"}],
        replay_instructions=[{"step": 1, "target": "https://example.com/api/test"}],
        invariant_violated="test_invariant",
        proof_hash="abc123",
    )


def make_mcp_finding(
    classification: MCPClassification = MCPClassification.BUG,
    has_proof: bool = True,
) -> MCPFinding:
    """Create an MCP finding for testing."""
    return MCPFinding(
        finding_id=f"finding-{datetime.now(timezone.utc).timestamp()}",
        classification=classification,
        invariant_violated="test_invariant" if has_proof else None,
        proof=make_proof_chain() if has_proof else None,
        severity="high",
        cyfer_brain_observation_id="obs-001",
        timestamp=datetime.now(timezone.utc),
    )


def make_authorization(
    program_name: str = "test-program",
    valid_days: int = 30,
) -> AuthorizationDocument:
    """Create an authorization document for testing."""
    now = datetime.now(timezone.utc)
    return AuthorizationDocument(
        program_name=program_name,
        authorized_domains=("example.com", "test.example.com"),
        authorized_ip_ranges=("10.0.0.0/8",),
        excluded_paths=("/admin",),
        valid_from=now - timedelta(days=1),
        valid_until=now + timedelta(days=valid_days),
        document_hash="auth-hash-123",
    )


# =============================================================================
# End-to-End Pipeline Tests
# =============================================================================


class TestEndToEndPipeline:
    """
    **Property: End-to-end pipeline respects all boundaries**
    **Validates: All requirements**

    Tests that the complete pipeline flow enforces all
    architectural constraints and requires human approval.
    """

    def test_valid_finding_flows_through_pipeline(self):
        """Valid MCP BUG finding flows through pipeline to review."""
        auth = make_authorization()
        pipeline = BountyPipeline(auth, platform="generic")

        finding = make_mcp_finding(MCPClassification.BUG, has_proof=True)
        result = pipeline.process_finding(finding)

        assert result.success
        assert result.stage == "review_pending"
        assert result.draft is not None
        assert result.review_request is not None

    def test_signal_finding_rejected(self):
        """SIGNAL classification is rejected."""
        auth = make_authorization()
        pipeline = BountyPipeline(auth, platform="generic")

        finding = make_mcp_finding(MCPClassification.SIGNAL, has_proof=False)
        result = pipeline.process_finding(finding)

        assert not result.success
        assert result.stage == "validation"
        assert isinstance(result.error, FindingValidationError)

    def test_no_issue_finding_rejected(self):
        """NO_ISSUE classification is rejected."""
        auth = make_authorization()
        pipeline = BountyPipeline(auth, platform="generic")

        finding = make_mcp_finding(MCPClassification.NO_ISSUE, has_proof=False)
        result = pipeline.process_finding(finding)

        assert not result.success
        assert isinstance(result.error, FindingValidationError)

    def test_coverage_gap_finding_rejected(self):
        """COVERAGE_GAP classification is rejected."""
        auth = make_authorization()
        pipeline = BountyPipeline(auth, platform="generic")

        finding = make_mcp_finding(MCPClassification.COVERAGE_GAP, has_proof=False)
        result = pipeline.process_finding(finding)

        assert not result.success
        assert isinstance(result.error, FindingValidationError)

    def test_bug_without_proof_rejected(self):
        """BUG without proof is rejected."""
        auth = make_authorization()
        pipeline = BountyPipeline(auth, platform="generic")

        finding = make_mcp_finding(MCPClassification.BUG, has_proof=False)
        result = pipeline.process_finding(finding)

        assert not result.success
        assert isinstance(result.error, FindingValidationError)

    def test_human_approval_required_for_submission(self):
        """Human approval is required before submission."""
        auth = make_authorization()
        pipeline = BountyPipeline(auth, platform="generic")

        finding = make_mcp_finding()
        result = pipeline.process_finding(finding)

        # Draft is pending review, not submitted
        assert result.draft.status == DraftStatus.PENDING_REVIEW
        assert not result.draft.is_approved

    def test_approval_creates_valid_token(self):
        """Approving a submission creates a valid token."""
        auth = make_authorization()
        pipeline = BountyPipeline(auth, platform="generic")

        finding = make_mcp_finding()
        result = pipeline.process_finding(finding)

        token = pipeline.approve_submission(
            result.review_request.request_id,
            approver_id="human-001",
        )

        assert token is not None
        assert not token.is_expired
        assert token.approver_id == "human-001"

    def test_rejection_archives_draft(self):
        """Rejecting a submission archives the draft."""
        auth = make_authorization()
        pipeline = BountyPipeline(auth, platform="generic")

        finding = make_mcp_finding()
        result = pipeline.process_finding(finding)

        pipeline.reject_submission(
            result.review_request.request_id,
            rejector_id="human-001",
            reason="Not a valid vulnerability",
        )

        # Check audit trail records rejection
        all_records = pipeline.audit_trail._records
        rejection_records = [r for r in all_records if r.action_type == "submission_rejected"]
        assert len(rejection_records) == 1
        assert rejection_records[0].actor == "human-001"


# =============================================================================
# Architectural Boundary Tests
# =============================================================================


class TestArchitecturalBoundaries:
    """Tests that architectural boundaries are enforced."""

    def test_auto_submit_forbidden(self):
        """Auto-submit is forbidden."""
        auth = make_authorization()
        pipeline = BountyPipeline(auth)

        with pytest.raises(ArchitecturalViolationError, match="auto-submit"):
            pipeline.auto_submit()

    def test_bypass_validation_forbidden(self):
        """Bypassing validation is forbidden."""
        auth = make_authorization()
        pipeline = BountyPipeline(auth)

        with pytest.raises(ArchitecturalViolationError, match="bypass"):
            pipeline.bypass_validation()

    def test_compute_bounty_forbidden(self):
        """Computing bounty is forbidden."""
        auth = make_authorization()
        pipeline = BountyPipeline(auth)

        with pytest.raises(ArchitecturalViolationError, match="bounty"):
            pipeline.compute_bounty()

    def test_validator_cannot_classify(self):
        """FindingValidator cannot classify findings."""
        validator = FindingValidator()

        with pytest.raises(ArchitecturalViolationError):
            validator.classify_finding({})

    def test_validator_cannot_generate_proof(self):
        """FindingValidator cannot generate proofs."""
        validator = FindingValidator()

        with pytest.raises(ArchitecturalViolationError):
            validator.generate_proof({})

    def test_validator_cannot_compute_confidence(self):
        """FindingValidator cannot compute confidence."""
        validator = FindingValidator()

        with pytest.raises(ArchitecturalViolationError):
            validator.compute_confidence({})


# =============================================================================
# Human Approval Enforcement Tests
# =============================================================================


class TestHumanApprovalEnforcement:
    """Tests that human approval is mandatory."""

    def test_submission_manager_requires_token(self):
        """SubmissionManager requires valid token."""
        manager = SubmissionManager()

        # Create an unapproved draft
        mcp_finding = make_mcp_finding()
        validated = ValidatedFinding(
            finding_id=mcp_finding.finding_id,
            mcp_finding=mcp_finding,
            proof_chain=mcp_finding.proof,
            source_links=SourceLinks(
                mcp_proof_id=mcp_finding.finding_id,
                mcp_proof_hash=mcp_finding.proof.proof_hash,
                cyfer_brain_observation_id=mcp_finding.cyfer_brain_observation_id,
            ),
        )

        draft = SubmissionDraft(
            draft_id="draft-001",
            finding=validated,
            platform="generic",
            report_title="Test",
            report_body="Test body",
            severity="high",
            reproduction_steps=[],
            proof_summary="Proof",
        )

        # Create expired token
        expired_token = ApprovalToken(
            token_id="expired",
            approver_id="human",
            approved_at=datetime.now(timezone.utc) - timedelta(hours=2),
            draft_hash=draft.compute_hash(),
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )

        adapter = GenericMarkdownAdapter()
        master_secret = b"test_secret_32_bytes_long_xxxxx"
        creds = EncryptedCredentials.encrypt(
            PlatformType.GENERIC, "key", "secret", master_secret
        )
        session = adapter.authenticate(creds, master_secret)

        with pytest.raises(HumanApprovalRequired, match="expired"):
            manager.submit(draft, expired_token, adapter, session)

    def test_token_must_match_draft(self):
        """Token must match the draft content."""
        manager = SubmissionManager()

        mcp_finding = make_mcp_finding()
        validated = ValidatedFinding(
            finding_id=mcp_finding.finding_id,
            mcp_finding=mcp_finding,
            proof_chain=mcp_finding.proof,
            source_links=SourceLinks(
                mcp_proof_id=mcp_finding.finding_id,
                mcp_proof_hash=mcp_finding.proof.proof_hash,
                cyfer_brain_observation_id=mcp_finding.cyfer_brain_observation_id,
            ),
        )

        draft = SubmissionDraft(
            draft_id="draft-001",
            finding=validated,
            platform="generic",
            report_title="Original Title",
            report_body="Test body",
            severity="high",
            reproduction_steps=[],
            proof_summary="Proof",
            status=DraftStatus.APPROVED,
            approval_token_id="token-123",
        )

        # Create token for original draft
        token = ApprovalToken.generate("human", draft)

        # Modify draft after approval
        draft.report_title = "Modified Title"

        adapter = GenericMarkdownAdapter()
        master_secret = b"test_secret_32_bytes_long_xxxxx"
        creds = EncryptedCredentials.encrypt(
            PlatformType.GENERIC, "key", "secret", master_secret
        )
        session = adapter.authenticate(creds, master_secret)

        with pytest.raises(HumanApprovalRequired, match="does not match"):
            manager.submit(draft, token, adapter, session)


# =============================================================================
# Audit Trail Tests
# =============================================================================


class TestAuditTrailIntegration:
    """Tests for audit trail integration."""

    def test_pipeline_records_all_actions(self):
        """Pipeline records all actions in audit trail."""
        auth = make_authorization()
        pipeline = BountyPipeline(auth, platform="generic")

        finding = make_mcp_finding()
        pipeline.process_finding(finding)

        records = pipeline.audit_trail.get_records_for_finding(finding.finding_id)

        # Should have records for: validation_start, validation_complete,
        # scope_validation, duplicate_check, report_generation, review_requested
        assert len(records) >= 5

        action_types = {r.action_type for r in records}
        assert "validation_start" in action_types
        assert "validation_complete" in action_types
        assert "scope_validation" in action_types

    def test_audit_trail_is_hash_chained(self):
        """Audit trail maintains hash chain integrity."""
        auth = make_authorization()
        pipeline = BountyPipeline(auth, platform="generic")

        finding = make_mcp_finding()
        pipeline.process_finding(finding)

        assert pipeline.audit_trail.verify_chain()


# =============================================================================
# Multi-Component Integration Tests
# =============================================================================


class TestMultiComponentIntegration:
    """Tests for integration between multiple components."""

    def test_program_manager_with_pipeline(self):
        """ProgramManager integrates with pipeline."""
        program_manager = ProgramManager()

        auth = make_authorization("program-a")
        program_manager.register_program(auth)

        # Create pipeline for the program
        pipeline = BountyPipeline(auth, platform="generic")

        finding = make_mcp_finding()
        result = pipeline.process_finding(finding)

        assert result.success

    def test_status_tracker_with_submission(self):
        """StatusTracker integrates with submission flow."""
        tracker = StatusTracker()

        # Register a submission
        tracked = tracker.register_submission(
            submission_id="test-001",
            platform="hackerone",
        )

        assert tracked.current_status == SubmissionStatus.SUBMITTED

        # Update status
        tracker.update_status("test-001", SubmissionStatus.TRIAGED)
        assert tracker.get_status("test-001") == SubmissionStatus.TRIAGED

    def test_recovery_manager_preserves_state(self):
        """RecoveryManager preserves pipeline state."""
        recovery = RecoveryManager()

        # Create state with pending work
        state = recovery.create_state(
            pending_drafts=[{"draft_id": "d1", "title": "Test"}],
            pending_reviews=[{"review_id": "r1"}],
        )

        recovery.save_state(state)

        # Recover state
        recovered = recovery.recover_state(state.state_id)

        assert recovered.pending_drafts == state.pending_drafts
        assert recovered.pending_reviews == state.pending_reviews


# =============================================================================
# Error Classification Tests
# =============================================================================


class TestErrorClassification:
    """Tests for error classification."""

    def test_hard_stop_errors_identified(self):
        """HARD STOP errors are correctly identified."""
        assert is_hard_stop(FindingValidationError("test"))
        assert is_hard_stop(ScopeViolationError("test"))
        assert is_hard_stop(ArchitecturalViolationError("test"))

    def test_non_hard_stop_errors_identified(self):
        """Non-HARD STOP errors are correctly identified."""
        assert not is_hard_stop(HumanApprovalRequired("test"))
        assert not is_hard_stop(SubmissionFailedError("test"))
        assert not is_hard_stop(ValueError("test"))
