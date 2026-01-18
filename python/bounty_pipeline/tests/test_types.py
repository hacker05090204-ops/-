"""
Property tests for Bounty Pipeline core data types.

**Feature: bounty-pipeline, Property 1: Finding Validation**
**Validates: Requirements 1.1, 1.2, 1.3, 1.4**
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from bounty_pipeline.types import (
    MCPClassification,
    MCPFinding,
    ProofChain,
    ValidatedFinding,
    SourceLinks,
    SubmissionDraft,
    ApprovalToken,
    AuditRecord,
    DraftStatus,
    ReproductionStep,
    AuthorizationDocument,
    DuplicateCandidate,
)


# ============================================================================
# Strategies for generating test data
# ============================================================================


@st.composite
def proof_chain_strategy(draw: st.DrawFn) -> ProofChain:
    """Generate valid ProofChain instances."""
    return ProofChain(
        before_state=draw(st.dictionaries(st.text(min_size=1, max_size=10), st.integers())),
        action_sequence=draw(
            st.lists(st.dictionaries(st.text(min_size=1, max_size=10), st.text()), min_size=1)
        ),
        after_state=draw(st.dictionaries(st.text(min_size=1, max_size=10), st.integers())),
        causality_chain=draw(
            st.lists(st.dictionaries(st.text(min_size=1, max_size=10), st.text()), min_size=1)
        ),
        replay_instructions=draw(
            st.lists(st.dictionaries(st.text(min_size=1, max_size=10), st.text()), min_size=1)
        ),
        invariant_violated=draw(st.text(min_size=1, max_size=50)),
        proof_hash=draw(st.text(min_size=64, max_size=64, alphabet="0123456789abcdef")),
    )


@st.composite
def mcp_finding_strategy(
    draw: st.DrawFn,
    classification: MCPClassification | None = None,
    with_proof: bool | None = None,
) -> MCPFinding:
    """Generate MCPFinding instances with optional constraints."""
    if classification is None:
        classification = draw(st.sampled_from(list(MCPClassification)))

    if with_proof is None:
        with_proof = draw(st.booleans())

    proof = draw(proof_chain_strategy()) if with_proof else None
    invariant = proof.invariant_violated if proof else None

    return MCPFinding(
        finding_id=draw(st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-")),
        classification=classification,
        invariant_violated=invariant,
        proof=proof,
        severity=draw(st.sampled_from(["critical", "high", "medium", "low", "informational"])),
        cyfer_brain_observation_id=draw(st.text(min_size=1, max_size=50)),
        timestamp=draw(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 1, 1))),
    )


@st.composite
def valid_mcp_finding_strategy(draw: st.DrawFn) -> MCPFinding:
    """Generate MCPFinding that is valid for submission (BUG + proof)."""
    return draw(mcp_finding_strategy(classification=MCPClassification.BUG, with_proof=True))


@st.composite
def invalid_mcp_finding_strategy(draw: st.DrawFn) -> MCPFinding:
    """Generate MCPFinding that is NOT valid for submission."""
    # Either non-BUG classification or missing proof
    choice = draw(st.integers(min_value=0, max_value=2))

    if choice == 0:
        # Non-BUG classification
        classification = draw(
            st.sampled_from(
                [MCPClassification.SIGNAL, MCPClassification.NO_ISSUE, MCPClassification.COVERAGE_GAP]
            )
        )
        return draw(mcp_finding_strategy(classification=classification))
    elif choice == 1:
        # BUG but no proof
        return draw(mcp_finding_strategy(classification=MCPClassification.BUG, with_proof=False))
    else:
        # Non-BUG and no proof
        classification = draw(
            st.sampled_from(
                [MCPClassification.SIGNAL, MCPClassification.NO_ISSUE, MCPClassification.COVERAGE_GAP]
            )
        )
        return draw(mcp_finding_strategy(classification=classification, with_proof=False))


# ============================================================================
# Property Tests
# ============================================================================


class TestMCPFindingValidation:
    """
    Property 1: Finding Validation

    *For any* finding received by Bounty Pipeline, the system SHALL only process
    findings with MCP BUG classification AND valid proof chain; all other
    classifications (SIGNAL, NO_ISSUE, COVERAGE_GAP) SHALL be rejected.

    **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
    """

    @given(finding=valid_mcp_finding_strategy())
    @settings(max_examples=100, deadline=5000)
    def test_bug_with_proof_is_valid(self, finding: MCPFinding) -> None:
        """BUG classification with proof is valid for submission."""
        assert finding.has_valid_proof is True
        assert finding.classification == MCPClassification.BUG
        assert finding.proof is not None

    @given(finding=invalid_mcp_finding_strategy())
    @settings(max_examples=100, deadline=5000)
    def test_non_bug_or_no_proof_is_invalid(self, finding: MCPFinding) -> None:
        """Non-BUG classification or missing proof is invalid for submission."""
        assert finding.has_valid_proof is False

    @given(finding=mcp_finding_strategy(classification=MCPClassification.SIGNAL))
    @settings(max_examples=100, deadline=5000)
    def test_signal_is_never_valid(self, finding: MCPFinding) -> None:
        """SIGNAL classification is never valid for submission."""
        assert finding.has_valid_proof is False

    @given(finding=mcp_finding_strategy(classification=MCPClassification.NO_ISSUE))
    @settings(max_examples=100, deadline=5000)
    def test_no_issue_is_never_valid(self, finding: MCPFinding) -> None:
        """NO_ISSUE classification is never valid for submission."""
        assert finding.has_valid_proof is False

    @given(finding=mcp_finding_strategy(classification=MCPClassification.COVERAGE_GAP))
    @settings(max_examples=100, deadline=5000)
    def test_coverage_gap_is_never_valid(self, finding: MCPFinding) -> None:
        """COVERAGE_GAP classification is never valid for submission."""
        assert finding.has_valid_proof is False


class TestValidatedFindingCreation:
    """Test that ValidatedFinding can only be created from valid MCPFinding."""

    @given(finding=valid_mcp_finding_strategy())
    @settings(max_examples=100, deadline=5000)
    def test_validated_finding_from_valid_mcp(self, finding: MCPFinding) -> None:
        """ValidatedFinding can be created from valid MCPFinding."""
        assert finding.proof is not None  # Type narrowing

        source_links = SourceLinks(
            mcp_proof_id=finding.finding_id,
            mcp_proof_hash=finding.proof.proof_hash,
            cyfer_brain_observation_id=finding.cyfer_brain_observation_id,
        )

        validated = ValidatedFinding(
            finding_id=finding.finding_id,
            mcp_finding=finding,
            proof_chain=finding.proof,
            source_links=source_links,
        )

        assert validated.mcp_finding.classification == MCPClassification.BUG
        assert validated.proof_chain is not None

    @given(finding=mcp_finding_strategy(classification=MCPClassification.SIGNAL, with_proof=True))
    @settings(max_examples=100, deadline=5000)
    def test_validated_finding_rejects_signal(self, finding: MCPFinding) -> None:
        """ValidatedFinding rejects SIGNAL classification."""
        assert finding.proof is not None

        source_links = SourceLinks(
            mcp_proof_id=finding.finding_id,
            mcp_proof_hash=finding.proof.proof_hash,
            cyfer_brain_observation_id=finding.cyfer_brain_observation_id,
        )

        with pytest.raises(ValueError, match="requires MCP BUG classification"):
            ValidatedFinding(
                finding_id=finding.finding_id,
                mcp_finding=finding,
                proof_chain=finding.proof,
                source_links=source_links,
            )

    @given(finding=mcp_finding_strategy(classification=MCPClassification.BUG, with_proof=False))
    @settings(max_examples=100, deadline=5000)
    def test_validated_finding_rejects_no_proof(self, finding: MCPFinding) -> None:
        """ValidatedFinding rejects BUG without proof."""
        source_links = SourceLinks(
            mcp_proof_id=finding.finding_id,
            mcp_proof_hash="dummy_hash",
            cyfer_brain_observation_id=finding.cyfer_brain_observation_id,
        )

        with pytest.raises(ValueError, match="requires MCP proof"):
            ValidatedFinding(
                finding_id=finding.finding_id,
                mcp_finding=finding,
                proof_chain=None,  # type: ignore
                source_links=source_links,
            )


class TestApprovalToken:
    """Test ApprovalToken properties."""

    @given(
        approver_id=st.text(min_size=1, max_size=50),
        validity_minutes=st.integers(min_value=1, max_value=60),
    )
    @settings(max_examples=100, deadline=5000)
    def test_token_generation(self, approver_id: str, validity_minutes: int) -> None:
        """Tokens are generated with correct properties."""
        # Create a minimal valid draft
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

        draft = SubmissionDraft(
            draft_id="draft-1",
            finding=validated,
            platform="hackerone",
            report_title="Test Report",
            report_body="Test body",
            severity="high",
            reproduction_steps=[],
            proof_summary="Test proof",
        )

        token = ApprovalToken.generate(approver_id, draft, validity_minutes)

        assert token.approver_id == approver_id
        assert token.matches_draft(draft)
        assert not token.is_expired

    def test_token_expiry(self) -> None:
        """Tokens expire after validity period."""
        now = datetime.now(timezone.utc)
        expired_token = ApprovalToken(
            token_id="test-token",
            approver_id="test-approver",
            approved_at=now - timedelta(hours=2),
            draft_hash="test-hash",
            expires_at=now - timedelta(hours=1),  # Expired 1 hour ago
        )

        assert expired_token.is_expired is True

    def test_token_not_expired(self) -> None:
        """Tokens are valid before expiry."""
        now = datetime.now(timezone.utc)
        valid_token = ApprovalToken(
            token_id="test-token",
            approver_id="test-approver",
            approved_at=now,
            draft_hash="test-hash",
            expires_at=now + timedelta(hours=1),  # Expires in 1 hour
        )

        assert valid_token.is_expired is False


class TestAuditRecordHashChain:
    """Test AuditRecord hash chain integrity."""

    def test_hash_computation_is_deterministic(self) -> None:
        """Hash computation produces same result for same inputs."""
        now = datetime.now(timezone.utc)
        details = {"key": "value"}

        hash1 = AuditRecord.compute_hash(
            record_id="rec-1",
            timestamp=now,
            action_type="test",
            actor="system",
            outcome="success",
            details=details,
            previous_hash="prev-hash",
        )

        hash2 = AuditRecord.compute_hash(
            record_id="rec-1",
            timestamp=now,
            action_type="test",
            actor="system",
            outcome="success",
            details=details,
            previous_hash="prev-hash",
        )

        assert hash1 == hash2

    def test_hash_changes_with_different_inputs(self) -> None:
        """Hash changes when any input changes."""
        now = datetime.now(timezone.utc)
        details = {"key": "value"}

        base_hash = AuditRecord.compute_hash(
            record_id="rec-1",
            timestamp=now,
            action_type="test",
            actor="system",
            outcome="success",
            details=details,
            previous_hash="prev-hash",
        )

        # Change record_id
        different_hash = AuditRecord.compute_hash(
            record_id="rec-2",  # Changed
            timestamp=now,
            action_type="test",
            actor="system",
            outcome="success",
            details=details,
            previous_hash="prev-hash",
        )

        assert base_hash != different_hash


class TestAuthorizationDocument:
    """Test AuthorizationDocument properties."""

    def test_expired_authorization(self) -> None:
        """Expired authorization is detected."""
        now = datetime.now(timezone.utc)
        expired_auth = AuthorizationDocument(
            program_name="test-program",
            authorized_domains=("example.com",),
            authorized_ip_ranges=(),
            excluded_paths=(),
            valid_from=now - timedelta(days=30),
            valid_until=now - timedelta(days=1),  # Expired yesterday
            document_hash="test-hash",
        )

        assert expired_auth.is_expired is True
        assert expired_auth.is_active is False

    def test_active_authorization(self) -> None:
        """Active authorization is detected."""
        now = datetime.now(timezone.utc)
        active_auth = AuthorizationDocument(
            program_name="test-program",
            authorized_domains=("example.com",),
            authorized_ip_ranges=(),
            excluded_paths=(),
            valid_from=now - timedelta(days=30),
            valid_until=now + timedelta(days=30),  # Valid for 30 more days
            document_hash="test-hash",
        )

        assert active_auth.is_expired is False
        assert active_auth.is_active is True


class TestDuplicateCandidate:
    """Test DuplicateCandidate properties."""

    @given(similarity=st.floats(min_value=0.0, max_value=1.0))
    @settings(max_examples=100, deadline=5000)
    def test_valid_similarity_score(self, similarity: float) -> None:
        """Similarity score must be between 0 and 1."""
        candidate = DuplicateCandidate(
            original_finding_id="orig-1",
            original_submission_id="sub-1",
            similarity_score=similarity,
            comparison_details={},
        )
        assert 0.0 <= candidate.similarity_score <= 1.0

    @given(similarity=st.floats().filter(lambda x: x < 0.0 or x > 1.0))
    @settings(max_examples=100, deadline=5000)
    def test_invalid_similarity_score_rejected(self, similarity: float) -> None:
        """Invalid similarity scores are rejected."""
        assume(not (0.0 <= similarity <= 1.0))

        with pytest.raises(ValueError, match="similarity_score must be between"):
            DuplicateCandidate(
                original_finding_id="orig-1",
                original_submission_id="sub-1",
                similarity_score=similarity,
                comparison_details={},
            )


class TestProofChainImmutability:
    """Test that ProofChain is immutable."""

    @given(proof=proof_chain_strategy())
    @settings(max_examples=100, deadline=5000)
    def test_proof_chain_is_frozen(self, proof: ProofChain) -> None:
        """ProofChain instances are immutable."""
        with pytest.raises(AttributeError):
            proof.proof_hash = "new_hash"  # type: ignore

    def test_proof_chain_requires_hash(self) -> None:
        """ProofChain requires proof_hash."""
        with pytest.raises(ValueError, match="must have proof_hash"):
            ProofChain(
                before_state={},
                action_sequence=[],
                after_state={},
                causality_chain=[],
                replay_instructions=[],
                invariant_violated="test",
                proof_hash="",  # Empty hash
            )

    def test_proof_chain_requires_invariant(self) -> None:
        """ProofChain requires invariant_violated."""
        with pytest.raises(ValueError, match="must specify invariant_violated"):
            ProofChain(
                before_state={},
                action_sequence=[],
                after_state={},
                causality_chain=[],
                replay_instructions=[],
                invariant_violated="",  # Empty invariant
                proof_hash="a" * 64,
            )
