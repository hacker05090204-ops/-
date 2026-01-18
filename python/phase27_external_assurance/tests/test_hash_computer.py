"""
Phase-27 Hash Computer Tests

NO AUTHORITY / PROOF ONLY

Tests for hash computation functionality.
Tests MUST fail before implementation (PYTEST-FIRST).
"""

import pytest


class TestHumanInitiationRequired:
    """Tests that human_initiated=True is required."""

    def test_refuses_if_human_initiated_false(self, sample_artifact_path):
        """MUST refuse if human_initiated=False."""
        from phase27_external_assurance.hash_computer import compute_artifact_hash
        from phase27_external_assurance.types import ProofError

        result = compute_artifact_hash(sample_artifact_path, human_initiated=False)

        assert isinstance(result, ProofError)
        assert result.error_type == "HUMAN_INITIATION_REQUIRED"

    def test_refuses_if_human_initiated_missing(self, sample_artifact_path):
        """MUST refuse if human_initiated is not provided."""
        from phase27_external_assurance.hash_computer import compute_artifact_hash

        # Should raise TypeError because human_initiated is keyword-only
        with pytest.raises(TypeError):
            compute_artifact_hash(sample_artifact_path)

    def test_accepts_if_human_initiated_true(self, sample_artifact_path):
        """MUST accept if human_initiated=True."""
        from phase27_external_assurance.hash_computer import compute_artifact_hash
        from phase27_external_assurance.types import ArtifactHash

        result = compute_artifact_hash(sample_artifact_path, human_initiated=True)

        assert isinstance(result, ArtifactHash)


class TestHashComputation:
    """Tests for SHA-256 hash computation."""

    def test_computes_sha256_hash(self, sample_artifact_path):
        """MUST compute SHA-256 hash."""
        from phase27_external_assurance.hash_computer import compute_artifact_hash
        from phase27_external_assurance.types import ArtifactHash

        result = compute_artifact_hash(sample_artifact_path, human_initiated=True)

        assert isinstance(result, ArtifactHash)
        assert result.hash_algorithm == "SHA-256"
        assert len(result.hash_value) == 64  # SHA-256 hex is 64 chars

    def test_hash_is_deterministic(self, sample_artifact_path):
        """Hash computation MUST be deterministic."""
        from phase27_external_assurance.hash_computer import compute_artifact_hash

        result1 = compute_artifact_hash(sample_artifact_path, human_initiated=True)
        result2 = compute_artifact_hash(sample_artifact_path, human_initiated=True)

        assert result1.hash_value == result2.hash_value

    def test_hash_includes_artifact_path(self, sample_artifact_path):
        """Result MUST include artifact path."""
        from phase27_external_assurance.hash_computer import compute_artifact_hash

        result = compute_artifact_hash(sample_artifact_path, human_initiated=True)

        assert result.artifact_path == sample_artifact_path


class TestDisclaimerPresence:
    """Tests that disclaimer is present in output."""

    def test_hash_result_has_disclaimer(self, sample_artifact_path):
        """ArtifactHash result MUST have disclaimer."""
        from phase27_external_assurance.hash_computer import compute_artifact_hash

        result = compute_artifact_hash(sample_artifact_path, human_initiated=True)

        assert "NO AUTHORITY" in result.disclaimer
        assert "PROOF ONLY" in result.disclaimer

    def test_error_result_has_disclaimer(self, sample_artifact_path):
        """ProofError result MUST have disclaimer."""
        from phase27_external_assurance.hash_computer import compute_artifact_hash

        result = compute_artifact_hash(sample_artifact_path, human_initiated=False)

        assert "NO AUTHORITY" in result.disclaimer
        assert "PROOF ONLY" in result.disclaimer


class TestErrorHandling:
    """Tests for error handling."""

    def test_returns_error_for_nonexistent_file(self, nonexistent_path):
        """MUST return ProofError for nonexistent file."""
        from phase27_external_assurance.hash_computer import compute_artifact_hash
        from phase27_external_assurance.types import ProofError

        result = compute_artifact_hash(nonexistent_path, human_initiated=True)

        assert isinstance(result, ProofError)
        assert result.error_type == "FILE_NOT_FOUND"

    def test_error_does_not_raise_exception(self, nonexistent_path):
        """MUST NOT raise exception for errors."""
        from phase27_external_assurance.hash_computer import compute_artifact_hash

        # Should not raise, should return ProofError
        result = compute_artifact_hash(nonexistent_path, human_initiated=True)

        # If we get here without exception, test passes
        assert result is not None
