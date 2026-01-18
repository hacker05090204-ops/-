"""
Property tests for Finding Validator.

**Feature: bounty-pipeline, Property 1: Finding Validation**
**Validates: Requirements 1.1, 1.2, 1.3, 1.4**

**Feature: bounty-pipeline, Property 2: Proof Inclusion**
**Validates: Requirements 1.5**
"""

from datetime import datetime, timezone

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from bounty_pipeline.errors import FindingValidationError, ArchitecturalViolationError
from bounty_pipeline.types import (
    MCPClassification,
    MCPFinding,
    ProofChain,
    ValidatedFinding,
)
from bounty_pipeline.validator import FindingValidator


# ============================================================================
# Strategies for generating test data
# ============================================================================


@st.composite
def proof_chain_strategy(draw: st.DrawFn) -> ProofChain:
    """Generate valid ProofChain instances."""
    return ProofChain(
        before_state=draw(st.dictionaries(st.text(min_size=1, max_size=10), st.integers())),
        action_sequence=draw(
            st.lists(
                st.dictionaries(st.text(min_size=1, max_size=10), st.text(min_size=1)),
                min_size=1,
                max_size=5,
            )
        ),
        after_state=draw(st.dictionaries(st.text(min_size=1, max_size=10), st.integers())),
        causality_chain=draw(
            st.lists(
                st.dictionaries(st.text(min_size=1, max_size=10), st.text(min_size=1)),
                min_size=1,
                max_size=5,
            )
        ),
        replay_instructions=draw(
            st.lists(
                st.dictionaries(st.text(min_size=1, max_size=10), st.text(min_size=1)),
                min_size=1,
                max_size=5,
            )
        ),
        invariant_violated=draw(st.text(min_size=1, max_size=50)),
        proof_hash=draw(st.text(min_size=64, max_size=64, alphabet="0123456789abcdef")),
    )


@st.composite
def valid_mcp_finding_strategy(draw: st.DrawFn) -> MCPFinding:
    """Generate MCPFinding that is valid for submission (BUG + proof)."""
    proof = draw(proof_chain_strategy())
    return MCPFinding(
        finding_id=draw(
            st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-")
        ),
        classification=MCPClassification.BUG,
        invariant_violated=proof.invariant_violated,
        proof=proof,
        severity=draw(st.sampled_from(["critical", "high", "medium", "low", "informational"])),
        cyfer_brain_observation_id=draw(st.text(min_size=1, max_size=50)),
        timestamp=draw(
            st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 1, 1))
        ),
    )


@st.composite
def signal_finding_strategy(draw: st.DrawFn) -> MCPFinding:
    """Generate MCPFinding with SIGNAL classification."""
    return MCPFinding(
        finding_id=draw(
            st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-")
        ),
        classification=MCPClassification.SIGNAL,
        invariant_violated=None,
        proof=None,
        severity=draw(st.sampled_from(["critical", "high", "medium", "low", "informational"])),
        cyfer_brain_observation_id=draw(st.text(min_size=1, max_size=50)),
        timestamp=draw(
            st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 1, 1))
        ),
    )


@st.composite
def no_issue_finding_strategy(draw: st.DrawFn) -> MCPFinding:
    """Generate MCPFinding with NO_ISSUE classification."""
    return MCPFinding(
        finding_id=draw(
            st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-")
        ),
        classification=MCPClassification.NO_ISSUE,
        invariant_violated=None,
        proof=None,
        severity=draw(st.sampled_from(["critical", "high", "medium", "low", "informational"])),
        cyfer_brain_observation_id=draw(st.text(min_size=1, max_size=50)),
        timestamp=draw(
            st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 1, 1))
        ),
    )


@st.composite
def coverage_gap_finding_strategy(draw: st.DrawFn) -> MCPFinding:
    """Generate MCPFinding with COVERAGE_GAP classification."""
    return MCPFinding(
        finding_id=draw(
            st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-")
        ),
        classification=MCPClassification.COVERAGE_GAP,
        invariant_violated=None,
        proof=None,
        severity=draw(st.sampled_from(["critical", "high", "medium", "low", "informational"])),
        cyfer_brain_observation_id=draw(st.text(min_size=1, max_size=50)),
        timestamp=draw(
            st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 1, 1))
        ),
    )


@st.composite
def bug_without_proof_strategy(draw: st.DrawFn) -> MCPFinding:
    """Generate MCPFinding with BUG classification but no proof."""
    return MCPFinding(
        finding_id=draw(
            st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-")
        ),
        classification=MCPClassification.BUG,
        invariant_violated=None,
        proof=None,
        severity=draw(st.sampled_from(["critical", "high", "medium", "low", "informational"])),
        cyfer_brain_observation_id=draw(st.text(min_size=1, max_size=50)),
        timestamp=draw(
            st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 1, 1))
        ),
    )


# ============================================================================
# Property Tests
# ============================================================================


class TestFindingValidation:
    """
    Property 1: Finding Validation

    *For any* finding received by Bounty Pipeline, the system SHALL only process
    findings with MCP BUG classification AND valid proof chain; all other
    classifications (SIGNAL, NO_ISSUE, COVERAGE_GAP) SHALL be rejected.

    **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
    """

    @given(finding=valid_mcp_finding_strategy())
    @settings(max_examples=100, deadline=5000)
    def test_valid_bug_with_proof_passes(self, finding: MCPFinding) -> None:
        """BUG classification with valid proof passes validation."""
        validator = FindingValidator()
        validated = validator.validate(finding)

        assert validated is not None
        assert validated.mcp_finding.classification == MCPClassification.BUG
        assert validated.proof_chain is not None
        assert validated.finding_id == finding.finding_id

    @given(finding=signal_finding_strategy())
    @settings(max_examples=100, deadline=5000)
    def test_signal_is_rejected(self, finding: MCPFinding) -> None:
        """SIGNAL classification is rejected."""
        validator = FindingValidator()

        with pytest.raises(FindingValidationError) as exc_info:
            validator.validate(finding)

        assert "SIGNAL" in str(exc_info.value)
        assert "Only BUG classification" in str(exc_info.value)

    @given(finding=no_issue_finding_strategy())
    @settings(max_examples=100, deadline=5000)
    def test_no_issue_is_rejected(self, finding: MCPFinding) -> None:
        """NO_ISSUE classification is rejected."""
        validator = FindingValidator()

        with pytest.raises(FindingValidationError) as exc_info:
            validator.validate(finding)

        assert "NO_ISSUE" in str(exc_info.value)
        assert "Only BUG classification" in str(exc_info.value)

    @given(finding=coverage_gap_finding_strategy())
    @settings(max_examples=100, deadline=5000)
    def test_coverage_gap_is_rejected(self, finding: MCPFinding) -> None:
        """COVERAGE_GAP classification is rejected."""
        validator = FindingValidator()

        with pytest.raises(FindingValidationError) as exc_info:
            validator.validate(finding)

        assert "COVERAGE_GAP" in str(exc_info.value)
        assert "Only BUG classification" in str(exc_info.value)

    @given(finding=bug_without_proof_strategy())
    @settings(max_examples=100, deadline=5000)
    def test_bug_without_proof_is_rejected(self, finding: MCPFinding) -> None:
        """BUG classification without proof is rejected."""
        validator = FindingValidator()

        with pytest.raises(FindingValidationError) as exc_info:
            validator.validate(finding)

        assert "no proof chain" in str(exc_info.value).lower()


class TestProofInclusion:
    """
    Property 2: Proof Inclusion

    *For any* report generated from a validated finding, the report SHALL
    include the complete proof chain from MCP.

    **Validates: Requirements 1.5**
    """

    @given(finding=valid_mcp_finding_strategy())
    @settings(max_examples=100, deadline=5000)
    def test_validated_finding_includes_proof(self, finding: MCPFinding) -> None:
        """Validated finding includes complete proof chain."""
        validator = FindingValidator()
        validated = validator.validate(finding)

        # Proof chain must be present
        assert validated.proof_chain is not None

        # Proof chain must match original
        assert validated.proof_chain == finding.proof

        # All proof components must be present
        assert validated.proof_chain.before_state is not None
        assert validated.proof_chain.after_state is not None
        assert validated.proof_chain.action_sequence is not None
        assert validated.proof_chain.causality_chain is not None
        assert validated.proof_chain.replay_instructions is not None
        assert validated.proof_chain.invariant_violated is not None
        assert validated.proof_chain.proof_hash is not None

    @given(finding=valid_mcp_finding_strategy())
    @settings(max_examples=100, deadline=5000)
    def test_extract_proof_chain_returns_complete_proof(self, finding: MCPFinding) -> None:
        """extract_proof_chain returns complete proof."""
        validator = FindingValidator()
        proof = validator.extract_proof_chain(finding)

        assert proof == finding.proof
        assert proof.proof_hash == finding.proof.proof_hash
        assert proof.invariant_violated == finding.proof.invariant_violated

    @given(finding=valid_mcp_finding_strategy())
    @settings(max_examples=100, deadline=5000)
    def test_source_links_reference_original(self, finding: MCPFinding) -> None:
        """Source links reference original MCP proof and Cyfer Brain observation."""
        validator = FindingValidator()
        links = validator.link_to_sources(finding)

        assert links.mcp_proof_id == finding.finding_id
        assert links.mcp_proof_hash == finding.proof.proof_hash
        assert links.cyfer_brain_observation_id == finding.cyfer_brain_observation_id


class TestValidationResult:
    """Test check_valid method returns proper results."""

    @given(finding=valid_mcp_finding_strategy())
    @settings(max_examples=100, deadline=5000)
    def test_check_valid_returns_true_for_valid(self, finding: MCPFinding) -> None:
        """check_valid returns is_valid=True for valid findings."""
        validator = FindingValidator()
        result = validator.check_valid(finding)

        assert result.is_valid is True
        assert result.validated_finding is not None
        assert "valid" in result.reason.lower()

    @given(finding=signal_finding_strategy())
    @settings(max_examples=100, deadline=5000)
    def test_check_valid_returns_false_for_invalid(self, finding: MCPFinding) -> None:
        """check_valid returns is_valid=False for invalid findings."""
        validator = FindingValidator()
        result = validator.check_valid(finding)

        assert result.is_valid is False
        assert result.validated_finding is None
        assert "SIGNAL" in result.reason


class TestArchitecturalBoundaryEnforcement:
    """
    Test that validator enforces architectural boundaries.

    Bounty Pipeline MUST NOT:
    - Classify findings (MCP's responsibility)
    - Generate proofs (MCP's responsibility)
    - Compute confidence (MCP's responsibility)
    - Override MCP classifications
    """

    def test_classify_finding_raises_violation(self) -> None:
        """classify_finding raises ArchitecturalViolationError."""
        validator = FindingValidator()

        with pytest.raises(ArchitecturalViolationError) as exc_info:
            validator.classify_finding()

        assert "cannot classify" in str(exc_info.value).lower()
        assert "MCP" in str(exc_info.value)

    def test_generate_proof_raises_violation(self) -> None:
        """generate_proof raises ArchitecturalViolationError."""
        validator = FindingValidator()

        with pytest.raises(ArchitecturalViolationError) as exc_info:
            validator.generate_proof()

        assert "cannot generate proof" in str(exc_info.value).lower()
        assert "MCP" in str(exc_info.value)

    def test_compute_confidence_raises_violation(self) -> None:
        """compute_confidence raises ArchitecturalViolationError."""
        validator = FindingValidator()

        with pytest.raises(ArchitecturalViolationError) as exc_info:
            validator.compute_confidence()

        assert "cannot compute confidence" in str(exc_info.value).lower()
        assert "MCP" in str(exc_info.value)

    def test_override_classification_raises_violation(self) -> None:
        """override_classification raises ArchitecturalViolationError."""
        validator = FindingValidator()

        with pytest.raises(ArchitecturalViolationError) as exc_info:
            validator.override_classification()

        assert "cannot override" in str(exc_info.value).lower()
        assert "MCP" in str(exc_info.value)


class TestProofChainValidation:
    """Test proof chain validation."""

    def test_empty_action_sequence_rejected(self) -> None:
        """Proof with empty action_sequence is rejected."""
        proof = ProofChain(
            before_state={},
            action_sequence=[],  # Empty
            after_state={},
            causality_chain=[{"cause": "test"}],
            replay_instructions=[{"step": "test"}],
            invariant_violated="test_invariant",
            proof_hash="a" * 64,
        )

        finding = MCPFinding(
            finding_id="test-finding",
            classification=MCPClassification.BUG,
            invariant_violated="test_invariant",
            proof=proof,
            severity="high",
            cyfer_brain_observation_id="obs-1",
            timestamp=datetime.now(timezone.utc),
        )

        validator = FindingValidator()

        with pytest.raises(FindingValidationError) as exc_info:
            validator.validate(finding)

        assert "empty action_sequence" in str(exc_info.value)

    def test_empty_causality_chain_rejected(self) -> None:
        """Proof with empty causality_chain is rejected."""
        proof = ProofChain(
            before_state={},
            action_sequence=[{"action": "test"}],
            after_state={},
            causality_chain=[],  # Empty
            replay_instructions=[{"step": "test"}],
            invariant_violated="test_invariant",
            proof_hash="a" * 64,
        )

        finding = MCPFinding(
            finding_id="test-finding",
            classification=MCPClassification.BUG,
            invariant_violated="test_invariant",
            proof=proof,
            severity="high",
            cyfer_brain_observation_id="obs-1",
            timestamp=datetime.now(timezone.utc),
        )

        validator = FindingValidator()

        with pytest.raises(FindingValidationError) as exc_info:
            validator.validate(finding)

        assert "empty causality_chain" in str(exc_info.value)

    def test_empty_replay_instructions_rejected(self) -> None:
        """Proof with empty replay_instructions is rejected."""
        proof = ProofChain(
            before_state={},
            action_sequence=[{"action": "test"}],
            after_state={},
            causality_chain=[{"cause": "test"}],
            replay_instructions=[],  # Empty
            invariant_violated="test_invariant",
            proof_hash="a" * 64,
        )

        finding = MCPFinding(
            finding_id="test-finding",
            classification=MCPClassification.BUG,
            invariant_violated="test_invariant",
            proof=proof,
            severity="high",
            cyfer_brain_observation_id="obs-1",
            timestamp=datetime.now(timezone.utc),
        )

        validator = FindingValidator()

        with pytest.raises(FindingValidationError) as exc_info:
            validator.validate(finding)

        assert "empty replay_instructions" in str(exc_info.value)
