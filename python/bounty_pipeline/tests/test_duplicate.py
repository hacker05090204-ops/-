"""
Property tests for Duplicate Detector.

**Feature: bounty-pipeline, Property 11: Duplicate Detection**
**Validates: Requirements 8.1, 8.2, 8.5**
"""

from datetime import datetime, timezone

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from bounty_pipeline.types import (
    MCPClassification,
    MCPFinding,
    ProofChain,
    ValidatedFinding,
    SourceLinks,
)
from bounty_pipeline.duplicate import DuplicateDetector


# ============================================================================
# Test Fixtures
# ============================================================================


def create_validated_finding(
    finding_id: str = "finding-1",
    invariant: str = "AUTH_BYPASS",
    proof_hash: str = "a" * 64,
) -> ValidatedFinding:
    """Create a test validated finding."""
    proof = ProofChain(
        before_state={"user": "guest"},
        action_sequence=[{"action": "exploit"}],
        after_state={"user": "admin"},
        causality_chain=[{"cause": "auth_bypass"}],
        replay_instructions=[{"step": "execute exploit"}],
        invariant_violated=invariant,
        proof_hash=proof_hash,
    )

    mcp_finding = MCPFinding(
        finding_id=finding_id,
        classification=MCPClassification.BUG,
        invariant_violated=invariant,
        proof=proof,
        severity="high",
        cyfer_brain_observation_id="obs-1",
        timestamp=datetime.now(timezone.utc),
    )

    source_links = SourceLinks(
        mcp_proof_id=finding_id,
        mcp_proof_hash=proof_hash,
        cyfer_brain_observation_id="obs-1",
    )

    return ValidatedFinding(
        finding_id=finding_id,
        mcp_finding=mcp_finding,
        proof_chain=proof,
        source_links=source_links,
    )


# ============================================================================
# Property Tests
# ============================================================================


class TestDuplicateDetection:
    """
    Property 11: Duplicate Detection

    *For any* submission preparation, the system SHALL check against
    previous submissions and require human decision for potential duplicates.

    **Validates: Requirements 8.1, 8.2, 8.5**
    """

    def test_no_duplicate_for_first_submission(self) -> None:
        """First submission has no duplicates."""
        detector = DuplicateDetector()
        finding = create_validated_finding()

        result = detector.check(finding)

        assert result is None

    def test_identical_finding_detected(self) -> None:
        """Identical finding is detected as duplicate."""
        detector = DuplicateDetector()

        # Register first finding
        finding1 = create_validated_finding("finding-1")
        detector.register_submission(finding1, "submission-1")

        # Check identical finding
        finding2 = create_validated_finding("finding-2")  # Same invariant and proof

        result = detector.check(finding2)

        assert result is not None
        assert result.original_finding_id == "finding-1"
        assert result.similarity_score > 0.5

    def test_different_finding_not_detected(self) -> None:
        """Different finding is not detected as duplicate."""
        detector = DuplicateDetector()

        # Register first finding
        finding1 = create_validated_finding("finding-1", invariant="AUTH_BYPASS")
        detector.register_submission(finding1, "submission-1")

        # Check different finding
        finding2 = create_validated_finding(
            "finding-2", invariant="SQL_INJECTION", proof_hash="b" * 64
        )

        result = detector.check(finding2)

        # Should not be detected as duplicate (different invariant and proof)
        # The similarity score should be below threshold
        if result is not None:
            assert result.similarity_score < 0.7

    def test_human_decision_required(self) -> None:
        """Human decision is required for potential duplicates."""
        detector = DuplicateDetector()

        # Register first finding
        finding1 = create_validated_finding("finding-1")
        detector.register_submission(finding1, "submission-1")

        # Check similar finding
        finding2 = create_validated_finding("finding-2")
        duplicate = detector.check(finding2)

        assert duplicate is not None

        # Request human decision
        request = detector.request_human_decision(finding2, duplicate)

        assert request is not None
        assert request.decision is None  # Pending
        assert request.finding == finding2
        assert request.candidate == duplicate


class TestHumanDecisions:
    """Test human decision workflow."""

    def test_decide_unique_allows_submission(self) -> None:
        """Deciding unique allows submission to proceed."""
        detector = DuplicateDetector()

        finding1 = create_validated_finding("finding-1")
        detector.register_submission(finding1, "submission-1")

        finding2 = create_validated_finding("finding-2")
        duplicate = detector.check(finding2)

        request = detector.request_human_decision(finding2, duplicate)
        updated = detector.decide_unique(request.request_id, "reviewer-1")

        assert updated.decision == "unique"
        assert updated.decided_by == "reviewer-1"

    def test_decide_duplicate_archives_finding(self) -> None:
        """Deciding duplicate archives the finding."""
        detector = DuplicateDetector()

        finding1 = create_validated_finding("finding-1")
        detector.register_submission(finding1, "submission-1")

        finding2 = create_validated_finding("finding-2")
        duplicate = detector.check(finding2)

        request = detector.request_human_decision(finding2, duplicate)
        archived = detector.decide_duplicate(request.request_id, "reviewer-1")

        assert archived is not None
        assert archived.original_finding_id == "finding-1"
        assert archived.archived_by == "reviewer-1"

    def test_archived_duplicates_tracked(self) -> None:
        """Archived duplicates are tracked."""
        detector = DuplicateDetector()

        finding1 = create_validated_finding("finding-1")
        detector.register_submission(finding1, "submission-1")

        finding2 = create_validated_finding("finding-2")
        duplicate = detector.check(finding2)

        request = detector.request_human_decision(finding2, duplicate)
        detector.decide_duplicate(request.request_id, "reviewer-1")

        archived = detector.get_archived_duplicates()
        assert len(archived) == 1


class TestSimilarityComputation:
    """Test similarity computation."""

    def test_same_invariant_increases_similarity(self) -> None:
        """Same invariant increases similarity score."""
        detector = DuplicateDetector()

        finding1 = create_validated_finding("finding-1", invariant="AUTH_BYPASS")
        finding2 = create_validated_finding("finding-2", invariant="AUTH_BYPASS")

        # Manually compute similarity
        score = detector._compute_similarity(finding1, finding2)

        # Same invariant should contribute to similarity
        assert score > 0

    def test_different_invariant_decreases_similarity(self) -> None:
        """Different invariant decreases similarity score."""
        detector = DuplicateDetector()

        finding1 = create_validated_finding("finding-1", invariant="AUTH_BYPASS")
        finding2 = create_validated_finding(
            "finding-2", invariant="SQL_INJECTION", proof_hash="b" * 64
        )

        score = detector._compute_similarity(finding1, finding2)

        # Different invariant and proof should result in low similarity
        assert score < 0.5

    def test_same_proof_hash_increases_similarity(self) -> None:
        """Same proof hash increases similarity score."""
        detector = DuplicateDetector()

        finding1 = create_validated_finding("finding-1", proof_hash="a" * 64)
        finding2 = create_validated_finding("finding-2", proof_hash="a" * 64)

        score = detector._compute_similarity(finding1, finding2)

        # Same proof hash should contribute to similarity
        assert score > 0.5


class TestComparisonDetails:
    """Test comparison details generation."""

    def test_comparison_includes_both_findings(self) -> None:
        """Comparison details include both findings."""
        detector = DuplicateDetector()

        finding1 = create_validated_finding("finding-1")
        detector.register_submission(finding1, "submission-1")

        finding2 = create_validated_finding("finding-2")
        duplicate = detector.check(finding2)

        assert duplicate is not None
        details = duplicate.comparison_details

        assert "new_finding" in details
        assert "existing_finding" in details
        assert details["new_finding"]["id"] == "finding-2"
        assert details["existing_finding"]["id"] == "finding-1"


class TestSimilarityScoreBounds:
    """
    Property Test: Similarity Score Bounds

    *For any* DuplicateCandidate, the similarity_score SHALL be
    bounded between 0.0 and 1.0 inclusive.

    **Validates: Requirements 8.1, 8.2 (duplicate detection correctness)**
    """

    @given(
        similarity_score=st.floats(
            min_value=0.0,
            max_value=1.0,
            allow_nan=False,
            allow_infinity=False,
        )
    )
    @settings(max_examples=100)
    def test_valid_similarity_scores_accepted(self, similarity_score: float) -> None:
        """
        **Feature: bounty-pipeline, Property: Similarity Score Bounds**

        *For any* similarity score in [0.0, 1.0], the DuplicateCandidate
        SHALL accept the value without raising an error.
        """
        from bounty_pipeline.types import DuplicateCandidate

        # Should not raise
        candidate = DuplicateCandidate(
            original_finding_id="finding-1",
            original_submission_id="submission-1",
            similarity_score=similarity_score,
            comparison_details={"test": "data"},
        )

        assert candidate.similarity_score == similarity_score
        assert 0.0 <= candidate.similarity_score <= 1.0

    @given(
        similarity_score=st.floats(
            max_value=-0.001,  # Negative values
            allow_nan=False,
            allow_infinity=False,
        )
    )
    @settings(max_examples=100)
    def test_negative_similarity_scores_rejected(self, similarity_score: float) -> None:
        """
        **Feature: bounty-pipeline, Property: Similarity Score Bounds**

        *For any* similarity score < 0.0, the DuplicateCandidate
        SHALL reject the value with a ValueError.
        """
        from bounty_pipeline.types import DuplicateCandidate

        with pytest.raises(ValueError, match="similarity_score must be between 0.0 and 1.0"):
            DuplicateCandidate(
                original_finding_id="finding-1",
                original_submission_id="submission-1",
                similarity_score=similarity_score,
                comparison_details={"test": "data"},
            )

    @given(
        similarity_score=st.floats(
            min_value=1.001,  # Values > 1.0
            allow_nan=False,
            allow_infinity=False,
        )
    )
    @settings(max_examples=100)
    def test_similarity_scores_above_one_rejected(self, similarity_score: float) -> None:
        """
        **Feature: bounty-pipeline, Property: Similarity Score Bounds**

        *For any* similarity score > 1.0, the DuplicateCandidate
        SHALL reject the value with a ValueError.
        """
        from bounty_pipeline.types import DuplicateCandidate

        with pytest.raises(ValueError, match="similarity_score must be between 0.0 and 1.0"):
            DuplicateCandidate(
                original_finding_id="finding-1",
                original_submission_id="submission-1",
                similarity_score=similarity_score,
                comparison_details={"test": "data"},
            )

    @given(
        invariant1=st.text(min_size=1, max_size=50),
        invariant2=st.text(min_size=1, max_size=50),
        proof_hash1=st.text(min_size=64, max_size=64, alphabet="0123456789abcdef"),
        proof_hash2=st.text(min_size=64, max_size=64, alphabet="0123456789abcdef"),
    )
    @settings(max_examples=100)
    def test_computed_similarity_always_bounded(
        self,
        invariant1: str,
        invariant2: str,
        proof_hash1: str,
        proof_hash2: str,
    ) -> None:
        """
        **Feature: bounty-pipeline, Property: Similarity Score Bounds**

        *For any* pair of findings, the computed similarity score
        SHALL always be in the range [0.0, 1.0].
        """
        detector = DuplicateDetector()

        finding1 = create_validated_finding(
            "finding-1",
            invariant=invariant1 or "DEFAULT",
            proof_hash=proof_hash1,
        )
        finding2 = create_validated_finding(
            "finding-2",
            invariant=invariant2 or "DEFAULT",
            proof_hash=proof_hash2,
        )

        score = detector._compute_similarity(finding1, finding2)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0, f"Similarity score {score} out of bounds [0.0, 1.0]"
