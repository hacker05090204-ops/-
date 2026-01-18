"""
Phase-27 Types Tests

NO AUTHORITY / PROOF ONLY

Tests for immutable data structures.
Tests MUST fail before implementation (PYTEST-FIRST).
"""

import pytest


class TestArtifactHash:
    """Tests for ArtifactHash immutability and structure."""

    def test_artifact_hash_is_immutable(self):
        """ArtifactHash MUST be immutable (frozen dataclass)."""
        from phase27_external_assurance.types import ArtifactHash

        h = ArtifactHash(
            artifact_path="/path/to/artifact",
            hash_algorithm="SHA-256",
            hash_value="abc123",
            computed_at="2026-01-07T00:00:00Z",
            human_initiated=True,
            disclaimer="NO AUTHORITY / PROOF ONLY",
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            h.hash_value = "modified"

    def test_artifact_hash_has_disclaimer_field(self):
        """ArtifactHash MUST have disclaimer field."""
        from phase27_external_assurance.types import ArtifactHash

        h = ArtifactHash(
            artifact_path="/path/to/artifact",
            hash_algorithm="SHA-256",
            hash_value="abc123",
            computed_at="2026-01-07T00:00:00Z",
            human_initiated=True,
            disclaimer="NO AUTHORITY / PROOF ONLY",
        )

        assert hasattr(h, "disclaimer")
        assert "NO AUTHORITY" in h.disclaimer

    def test_artifact_hash_has_human_initiated_field(self):
        """ArtifactHash MUST have human_initiated field."""
        from phase27_external_assurance.types import ArtifactHash

        h = ArtifactHash(
            artifact_path="/path/to/artifact",
            hash_algorithm="SHA-256",
            hash_value="abc123",
            computed_at="2026-01-07T00:00:00Z",
            human_initiated=True,
            disclaimer="NO AUTHORITY / PROOF ONLY",
        )

        assert hasattr(h, "human_initiated")
        assert h.human_initiated is True


class TestComplianceAttestation:
    """Tests for ComplianceAttestation immutability and structure."""

    def test_compliance_attestation_is_immutable(self):
        """ComplianceAttestation MUST be immutable (frozen dataclass)."""
        from phase27_external_assurance.types import ComplianceAttestation

        a = ComplianceAttestation(
            attestation_id="test-id",
            timestamp="2026-01-07T00:00:00Z",
            artifact_hashes=(),
            phases_covered=(13, 14, 15),
            human_initiated=True,
            disclaimer="NO AUTHORITY / PROOF ONLY",
            actor="HUMAN",
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            a.attestation_id = "modified"

    def test_compliance_attestation_has_disclaimer_field(self):
        """ComplianceAttestation MUST have disclaimer field."""
        from phase27_external_assurance.types import ComplianceAttestation

        a = ComplianceAttestation(
            attestation_id="test-id",
            timestamp="2026-01-07T00:00:00Z",
            artifact_hashes=(),
            phases_covered=(13, 14, 15),
            human_initiated=True,
            disclaimer="NO AUTHORITY / PROOF ONLY",
            actor="HUMAN",
        )

        assert hasattr(a, "disclaimer")
        assert "NO AUTHORITY" in a.disclaimer

    def test_compliance_attestation_actor_is_human(self):
        """ComplianceAttestation actor MUST be 'HUMAN'."""
        from phase27_external_assurance.types import ComplianceAttestation

        a = ComplianceAttestation(
            attestation_id="test-id",
            timestamp="2026-01-07T00:00:00Z",
            artifact_hashes=(),
            phases_covered=(13, 14, 15),
            human_initiated=True,
            disclaimer="NO AUTHORITY / PROOF ONLY",
            actor="HUMAN",
        )

        assert a.actor == "HUMAN"


class TestAuditBundle:
    """Tests for AuditBundle immutability and structure."""

    def test_audit_bundle_is_immutable(self):
        """AuditBundle MUST be immutable (frozen dataclass)."""
        from phase27_external_assurance.types import AuditBundle

        b = AuditBundle(
            bundle_id="test-bundle",
            created_at="2026-01-07T00:00:00Z",
            attestations=(),
            governance_docs=(),
            bundle_hash="abc123",
            human_initiated=True,
            disclaimer="NO AUTHORITY / PROOF ONLY",
            actor="HUMAN",
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            b.bundle_id = "modified"

    def test_audit_bundle_has_disclaimer_field(self):
        """AuditBundle MUST have disclaimer field."""
        from phase27_external_assurance.types import AuditBundle

        b = AuditBundle(
            bundle_id="test-bundle",
            created_at="2026-01-07T00:00:00Z",
            attestations=(),
            governance_docs=(),
            bundle_hash="abc123",
            human_initiated=True,
            disclaimer="NO AUTHORITY / PROOF ONLY",
            actor="HUMAN",
        )

        assert hasattr(b, "disclaimer")
        assert "NO AUTHORITY" in b.disclaimer

    def test_audit_bundle_actor_is_human(self):
        """AuditBundle actor MUST be 'HUMAN'."""
        from phase27_external_assurance.types import AuditBundle

        b = AuditBundle(
            bundle_id="test-bundle",
            created_at="2026-01-07T00:00:00Z",
            attestations=(),
            governance_docs=(),
            bundle_hash="abc123",
            human_initiated=True,
            disclaimer="NO AUTHORITY / PROOF ONLY",
            actor="HUMAN",
        )

        assert b.actor == "HUMAN"


class TestProofError:
    """Tests for ProofError immutability and structure."""

    def test_proof_error_is_immutable(self):
        """ProofError MUST be immutable (frozen dataclass)."""
        from phase27_external_assurance.types import ProofError

        e = ProofError(
            error_type="TEST_ERROR",
            message="Test error message",
            timestamp="2026-01-07T00:00:00Z",
            disclaimer="NO AUTHORITY / PROOF ONLY",
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            e.error_type = "modified"

    def test_proof_error_has_disclaimer_field(self):
        """ProofError MUST have disclaimer field."""
        from phase27_external_assurance.types import ProofError

        e = ProofError(
            error_type="TEST_ERROR",
            message="Test error message",
            timestamp="2026-01-07T00:00:00Z",
            disclaimer="NO AUTHORITY / PROOF ONLY",
        )

        assert hasattr(e, "disclaimer")
        assert "NO AUTHORITY" in e.disclaimer
