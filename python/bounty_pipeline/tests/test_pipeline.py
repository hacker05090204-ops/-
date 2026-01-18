"""
Property tests for Bounty Pipeline orchestrator.

**Feature: bounty-pipeline, Property: End-to-end pipeline respects all boundaries**
**Validates: All requirements**
"""

from datetime import datetime, timedelta, timezone

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from bounty_pipeline.errors import (
    FindingValidationError,
    ArchitecturalViolationError,
)
from bounty_pipeline.types import (
    MCPClassification,
    MCPFinding,
    ProofChain,
    AuthorizationDocument,
)
from bounty_pipeline.pipeline import BountyPipeline


# ============================================================================
# Test Fixtures
# ============================================================================


def create_authorization() -> AuthorizationDocument:
    """Create a test authorization document."""
    now = datetime.now(timezone.utc)
    return AuthorizationDocument(
        program_name="test-program",
        authorized_domains=("example.com", "*.test.com"),
        authorized_ip_ranges=("10.0.0.0/8",),
        excluded_paths=("/admin/*",),
        valid_from=now - timedelta(days=30),
        valid_until=now + timedelta(days=30),
        document_hash="a" * 64,
    )


def create_valid_finding() -> MCPFinding:
    """Create a valid MCP finding with proof including target."""
    proof = ProofChain(
        before_state={"user": "guest", "target": "https://example.com/vulnerable"},
        action_sequence=[
            {"action": "navigate", "target": "https://example.com/vulnerable"},
            {"action": "exploit"},
        ],
        after_state={"user": "admin"},
        causality_chain=[{"cause": "auth_bypass"}],
        replay_instructions=[{"step": "execute exploit", "url": "https://example.com/vulnerable"}],
        invariant_violated="AUTHENTICATION_REQUIRED",
        proof_hash="a" * 64,
    )

    return MCPFinding(
        finding_id="test-finding-1",
        classification=MCPClassification.BUG,
        invariant_violated="AUTHENTICATION_REQUIRED",
        proof=proof,
        severity="high",
        cyfer_brain_observation_id="obs-1",
        timestamp=datetime.now(timezone.utc),
    )


def create_invalid_finding() -> MCPFinding:
    """Create an invalid MCP finding (SIGNAL, no proof)."""
    return MCPFinding(
        finding_id="test-finding-2",
        classification=MCPClassification.SIGNAL,
        invariant_violated=None,
        proof=None,
        severity="medium",
        cyfer_brain_observation_id="obs-2",
        timestamp=datetime.now(timezone.utc),
    )


# ============================================================================
# Property Tests
# ============================================================================


class TestPipelineValidation:
    """Test pipeline validation of findings."""

    def test_valid_finding_proceeds_to_review(self) -> None:
        """Valid finding proceeds to human review."""
        auth = create_authorization()
        pipeline = BountyPipeline(auth, platform="generic")

        finding = create_valid_finding()
        result = pipeline.process_finding(finding)

        assert result.success is True
        assert result.stage == "review_pending"
        assert result.draft is not None
        assert result.review_request is not None

    def test_invalid_finding_rejected(self) -> None:
        """Invalid finding (no proof) is rejected."""
        auth = create_authorization()
        pipeline = BountyPipeline(auth, platform="generic")

        finding = create_invalid_finding()
        result = pipeline.process_finding(finding)

        assert result.success is False
        assert result.stage == "validation"
        assert result.error is not None
        assert isinstance(result.error, FindingValidationError)

    def test_signal_classification_rejected(self) -> None:
        """SIGNAL classification is rejected."""
        auth = create_authorization()
        pipeline = BountyPipeline(auth, platform="generic")

        finding = MCPFinding(
            finding_id="signal-finding",
            classification=MCPClassification.SIGNAL,
            invariant_violated=None,
            proof=None,
            severity="low",
            cyfer_brain_observation_id="obs-3",
            timestamp=datetime.now(timezone.utc),
        )

        result = pipeline.process_finding(finding)

        assert result.success is False
        assert "SIGNAL" in result.message


class TestPipelineApproval:
    """Test pipeline approval workflow."""

    def test_approval_generates_token(self) -> None:
        """Approving a submission generates a token."""
        auth = create_authorization()
        pipeline = BountyPipeline(auth, platform="generic")

        finding = create_valid_finding()
        result = pipeline.process_finding(finding)

        assert result.review_request is not None

        token = pipeline.approve_submission(
            result.review_request.request_id, "reviewer-1"
        )

        assert token is not None
        assert token.approver_id == "reviewer-1"

    def test_rejection_archives_draft(self) -> None:
        """Rejecting a submission archives the draft."""
        auth = create_authorization()
        pipeline = BountyPipeline(auth, platform="generic")

        finding = create_valid_finding()
        result = pipeline.process_finding(finding)

        assert result.review_request is not None

        pipeline.reject_submission(
            result.review_request.request_id,
            "reviewer-1",
            "Not a valid vulnerability",
        )

        # Check audit trail recorded rejection
        records = pipeline.audit_trail.get_records_by_action_type("submission_rejected")
        assert len(records) == 1
        assert records[0].actor == "reviewer-1"


class TestPipelineAuditTrail:
    """Test pipeline audit trail."""

    def test_all_stages_recorded(self) -> None:
        """All pipeline stages are recorded in audit trail."""
        auth = create_authorization()
        pipeline = BountyPipeline(auth, platform="generic")

        finding = create_valid_finding()
        pipeline.process_finding(finding)

        # Check audit trail has records for each stage
        all_records = pipeline.audit_trail.get_all_records()

        action_types = [r.action_type for r in all_records]
        assert "validation_start" in action_types
        assert "validation_complete" in action_types
        assert "scope_validation" in action_types
        assert "duplicate_check" in action_types
        assert "report_generation" in action_types
        assert "review_requested" in action_types

    def test_failed_validation_recorded(self) -> None:
        """Failed validation is recorded in audit trail."""
        auth = create_authorization()
        pipeline = BountyPipeline(auth, platform="generic")

        finding = create_invalid_finding()
        pipeline.process_finding(finding)

        records = pipeline.audit_trail.get_records_by_action_type("validation_failed")
        assert len(records) == 1
        assert records[0].outcome == "rejected"


class TestArchitecturalBoundaryEnforcement:
    """Test that pipeline enforces architectural boundaries."""

    def test_auto_submit_raises_violation(self) -> None:
        """auto_submit raises ArchitecturalViolationError."""
        auth = create_authorization()
        pipeline = BountyPipeline(auth)

        with pytest.raises(ArchitecturalViolationError) as exc_info:
            pipeline.auto_submit()

        assert "cannot auto-submit" in str(exc_info.value).lower()

    def test_bypass_validation_raises_violation(self) -> None:
        """bypass_validation raises ArchitecturalViolationError."""
        auth = create_authorization()
        pipeline = BountyPipeline(auth)

        with pytest.raises(ArchitecturalViolationError) as exc_info:
            pipeline.bypass_validation()

        assert "cannot bypass" in str(exc_info.value).lower()

    def test_compute_bounty_raises_violation(self) -> None:
        """compute_bounty raises ArchitecturalViolationError."""
        auth = create_authorization()
        pipeline = BountyPipeline(auth)

        with pytest.raises(ArchitecturalViolationError) as exc_info:
            pipeline.compute_bounty()

        assert "cannot compute" in str(exc_info.value).lower()


class TestDuplicateDetection:
    """Test duplicate detection in pipeline."""

    def test_duplicate_flagged_for_human_decision(self) -> None:
        """Potential duplicate is flagged for human decision."""
        auth = create_authorization()
        pipeline = BountyPipeline(auth, platform="generic")

        # Process first finding
        finding1 = create_valid_finding()
        result1 = pipeline.process_finding(finding1)
        assert result1.success is True

        # Register it as submitted
        pipeline.duplicate_detector.register_submission(
            result1.draft.finding, "submission-1"
        )

        # Process identical finding
        finding2 = create_valid_finding()
        finding2 = MCPFinding(
            finding_id="test-finding-2",  # Different ID
            classification=finding1.classification,
            invariant_violated=finding1.invariant_violated,
            proof=finding1.proof,  # Same proof
            severity=finding1.severity,
            cyfer_brain_observation_id="obs-2",
            timestamp=datetime.now(timezone.utc),
        )

        result2 = pipeline.process_finding(finding2)

        # Should be flagged as potential duplicate
        assert result2.success is False
        assert result2.stage == "duplicate_check"
        assert "duplicate" in result2.message.lower()


class TestTargetExtraction:
    """Test target extraction from MCP ProofChain.
    
    CRITICAL: Target MUST be extracted from MCP proof, never fabricated.
    """

    def test_target_extracted_from_action_sequence(self) -> None:
        """Target is extracted from action_sequence in ProofChain."""
        proof = ProofChain(
            before_state={"user": "guest"},
            action_sequence=[
                {"action": "navigate", "target": "https://example.com/vulnerable"},
                {"action": "exploit"},
            ],
            after_state={"user": "admin"},
            causality_chain=[{"cause": "auth_bypass"}],
            replay_instructions=[{"step": "execute exploit"}],
            invariant_violated="AUTHENTICATION_REQUIRED",
            proof_hash="a" * 64,
        )

        finding = MCPFinding(
            finding_id="test-finding-target",
            classification=MCPClassification.BUG,
            invariant_violated="AUTHENTICATION_REQUIRED",
            proof=proof,
            severity="high",
            cyfer_brain_observation_id="obs-target",
            timestamp=datetime.now(timezone.utc),
        )

        auth = AuthorizationDocument(
            program_name="test-program",
            authorized_domains=("example.com",),
            authorized_ip_ranges=(),
            excluded_paths=(),
            valid_from=datetime.now(timezone.utc) - timedelta(days=30),
            valid_until=datetime.now(timezone.utc) + timedelta(days=30),
            document_hash="a" * 64,
        )

        pipeline = BountyPipeline(auth, platform="generic")
        result = pipeline.process_finding(finding)

        # Should succeed because target is in authorized domains
        assert result.success is True

    def test_target_extracted_from_before_state(self) -> None:
        """Target is extracted from before_state if not in action_sequence."""
        proof = ProofChain(
            before_state={"user": "guest", "url": "https://example.com/page"},
            action_sequence=[{"action": "exploit"}],
            after_state={"user": "admin"},
            causality_chain=[{"cause": "auth_bypass"}],
            replay_instructions=[{"step": "execute exploit"}],
            invariant_violated="AUTHENTICATION_REQUIRED",
            proof_hash="a" * 64,
        )

        finding = MCPFinding(
            finding_id="test-finding-before",
            classification=MCPClassification.BUG,
            invariant_violated="AUTHENTICATION_REQUIRED",
            proof=proof,
            severity="high",
            cyfer_brain_observation_id="obs-before",
            timestamp=datetime.now(timezone.utc),
        )

        auth = AuthorizationDocument(
            program_name="test-program",
            authorized_domains=("example.com",),
            authorized_ip_ranges=(),
            excluded_paths=(),
            valid_from=datetime.now(timezone.utc) - timedelta(days=30),
            valid_until=datetime.now(timezone.utc) + timedelta(days=30),
            document_hash="a" * 64,
        )

        pipeline = BountyPipeline(auth, platform="generic")
        result = pipeline.process_finding(finding)

        assert result.success is True

    def test_target_extracted_from_replay_instructions(self) -> None:
        """Target is extracted from replay_instructions as fallback."""
        proof = ProofChain(
            before_state={"user": "guest"},
            action_sequence=[{"action": "exploit"}],
            after_state={"user": "admin"},
            causality_chain=[{"cause": "auth_bypass"}],
            replay_instructions=[
                {"step": 1, "url": "https://example.com/replay"},
            ],
            invariant_violated="AUTHENTICATION_REQUIRED",
            proof_hash="a" * 64,
        )

        finding = MCPFinding(
            finding_id="test-finding-replay",
            classification=MCPClassification.BUG,
            invariant_violated="AUTHENTICATION_REQUIRED",
            proof=proof,
            severity="high",
            cyfer_brain_observation_id="obs-replay",
            timestamp=datetime.now(timezone.utc),
        )

        auth = AuthorizationDocument(
            program_name="test-program",
            authorized_domains=("example.com",),
            authorized_ip_ranges=(),
            excluded_paths=(),
            valid_from=datetime.now(timezone.utc) - timedelta(days=30),
            valid_until=datetime.now(timezone.utc) + timedelta(days=30),
            document_hash="a" * 64,
        )

        pipeline = BountyPipeline(auth, platform="generic")
        result = pipeline.process_finding(finding)

        assert result.success is True

    def test_missing_target_causes_hard_fail(self) -> None:
        """Missing target in ProofChain causes HARD FAIL."""
        proof = ProofChain(
            before_state={"user": "guest"},  # No target/url
            action_sequence=[{"action": "exploit"}],  # No target/url
            after_state={"user": "admin"},
            causality_chain=[{"cause": "auth_bypass"}],
            replay_instructions=[{"step": 1}],  # No target/url
            invariant_violated="AUTHENTICATION_REQUIRED",
            proof_hash="a" * 64,
        )

        finding = MCPFinding(
            finding_id="test-finding-no-target",
            classification=MCPClassification.BUG,
            invariant_violated="AUTHENTICATION_REQUIRED",
            proof=proof,
            severity="high",
            cyfer_brain_observation_id="obs-no-target",
            timestamp=datetime.now(timezone.utc),
        )

        auth = AuthorizationDocument(
            program_name="test-program",
            authorized_domains=("example.com",),
            authorized_ip_ranges=(),
            excluded_paths=(),
            valid_from=datetime.now(timezone.utc) - timedelta(days=30),
            valid_until=datetime.now(timezone.utc) + timedelta(days=30),
            document_hash="a" * 64,
        )

        pipeline = BountyPipeline(auth, platform="generic")
        result = pipeline.process_finding(finding)

        # Should fail because target cannot be extracted
        assert result.success is False
        assert "Cannot extract target" in result.message or "HARD STOP" in result.message


class TestNoPlaceholders:
    """Tests to verify NO placeholders exist in production code."""

    def test_no_placeholder_keywords_in_adapters(self) -> None:
        """Verify adapters.py has no placeholder keywords."""
        import bounty_pipeline.adapters as adapters_module
        import inspect
        
        source = inspect.getsource(adapters_module)
        
        # These keywords should NOT appear in production code
        forbidden = ["placeholder", "TODO", "FIXME", "XOR encryption"]
        
        for keyword in forbidden:
            assert keyword.lower() not in source.lower(), \
                f"Found forbidden keyword '{keyword}' in adapters.py"

    def test_no_placeholder_keywords_in_pipeline(self) -> None:
        """Verify pipeline.py has no placeholder keywords."""
        import bounty_pipeline.pipeline as pipeline_module
        import inspect
        
        source = inspect.getsource(pipeline_module)
        
        # These keywords should NOT appear in production code
        forbidden = ["placeholder", "TODO", "FIXME"]
        
        for keyword in forbidden:
            assert keyword.lower() not in source.lower(), \
                f"Found forbidden keyword '{keyword}' in pipeline.py"
