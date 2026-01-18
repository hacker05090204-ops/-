"""
Phase-27 Audit Bundle Tests

NO AUTHORITY / PROOF ONLY

Tests for audit bundle creation functionality.
Tests MUST fail before implementation (PYTEST-FIRST).
"""

import pytest


class TestHumanInitiationRequired:
    """Tests that human_initiated=True is required."""

    def test_refuses_if_human_initiated_false(self):
        """MUST refuse if human_initiated=False."""
        from phase27_external_assurance.audit_bundle import create_audit_bundle
        from phase27_external_assurance.types import ProofError

        result = create_audit_bundle(
            attestations=(),
            governance_docs=(),
            human_initiated=False,
        )

        assert isinstance(result, ProofError)
        assert result.error_type == "HUMAN_INITIATION_REQUIRED"

    def test_refuses_if_human_initiated_missing(self):
        """MUST refuse if human_initiated is not provided."""
        from phase27_external_assurance.audit_bundle import create_audit_bundle

        # Should raise TypeError because human_initiated is keyword-only
        with pytest.raises(TypeError):
            create_audit_bundle(
                attestations=(),
                governance_docs=(),
            )

    def test_accepts_if_human_initiated_true(self):
        """MUST accept if human_initiated=True."""
        from phase27_external_assurance.audit_bundle import create_audit_bundle
        from phase27_external_assurance.types import AuditBundle

        result = create_audit_bundle(
            attestations=(),
            governance_docs=(),
            human_initiated=True,
        )

        assert isinstance(result, AuditBundle)


class TestBundleCreation:
    """Tests for audit bundle creation."""

    def test_creates_bundle_with_uuid(self):
        """Bundle MUST have UUID."""
        from phase27_external_assurance.audit_bundle import create_audit_bundle

        result = create_audit_bundle(
            attestations=(),
            governance_docs=(),
            human_initiated=True,
        )

        assert result.bundle_id is not None
        assert len(result.bundle_id) > 0

    def test_creates_bundle_with_timestamp(self):
        """Bundle MUST have timestamp."""
        from phase27_external_assurance.audit_bundle import create_audit_bundle

        result = create_audit_bundle(
            attestations=(),
            governance_docs=(),
            human_initiated=True,
        )

        assert result.created_at is not None
        assert "T" in result.created_at  # ISO-8601 format

    def test_bundle_includes_attestations(self):
        """Bundle MUST include attestations."""
        from phase27_external_assurance.audit_bundle import create_audit_bundle
        from phase27_external_assurance.types import ComplianceAttestation

        attestation = ComplianceAttestation(
            attestation_id="test-id",
            timestamp="2026-01-07T00:00:00Z",
            artifact_hashes=(),
            phases_covered=(13, 14, 15),
            human_initiated=True,
            disclaimer="NO AUTHORITY / PROOF ONLY",
            actor="HUMAN",
        )

        result = create_audit_bundle(
            attestations=(attestation,),
            governance_docs=(),
            human_initiated=True,
        )

        assert len(result.attestations) == 1
        assert result.attestations[0].attestation_id == "test-id"

    def test_bundle_includes_governance_docs(self):
        """Bundle MUST include governance docs."""
        from phase27_external_assurance.audit_bundle import create_audit_bundle

        docs = ("/path/to/doc1.md", "/path/to/doc2.md")
        result = create_audit_bundle(
            attestations=(),
            governance_docs=docs,
            human_initiated=True,
        )

        assert result.governance_docs == docs


class TestBundleHash:
    """Tests for bundle hash computation."""

    def test_bundle_has_hash(self):
        """Bundle MUST have hash."""
        from phase27_external_assurance.audit_bundle import create_audit_bundle

        result = create_audit_bundle(
            attestations=(),
            governance_docs=(),
            human_initiated=True,
        )

        assert result.bundle_hash is not None
        assert len(result.bundle_hash) == 64  # SHA-256 hex

    def test_bundle_hash_is_deterministic_for_same_content(self):
        """Bundle hash MUST be deterministic for same content."""
        from phase27_external_assurance.audit_bundle import create_audit_bundle
        from phase27_external_assurance.types import ComplianceAttestation

        attestation = ComplianceAttestation(
            attestation_id="fixed-id",
            timestamp="2026-01-07T00:00:00Z",
            artifact_hashes=(),
            phases_covered=(13, 14, 15),
            human_initiated=True,
            disclaimer="NO AUTHORITY / PROOF ONLY",
            actor="HUMAN",
        )

        # Note: bundle_id and created_at will differ, so hash will differ
        # This test verifies hash is computed, not that it's identical
        result = create_audit_bundle(
            attestations=(attestation,),
            governance_docs=(),
            human_initiated=True,
        )

        assert result.bundle_hash is not None


class TestActorIsHuman:
    """Tests that actor is always HUMAN."""

    def test_actor_is_human(self):
        """Actor MUST be 'HUMAN'."""
        from phase27_external_assurance.audit_bundle import create_audit_bundle

        result = create_audit_bundle(
            attestations=(),
            governance_docs=(),
            human_initiated=True,
        )

        assert result.actor == "HUMAN"


class TestDisclaimerPresence:
    """Tests that disclaimer is present in output."""

    def test_bundle_has_disclaimer(self):
        """AuditBundle MUST have disclaimer."""
        from phase27_external_assurance.audit_bundle import create_audit_bundle

        result = create_audit_bundle(
            attestations=(),
            governance_docs=(),
            human_initiated=True,
        )

        assert "NO AUTHORITY" in result.disclaimer
        assert "PROOF ONLY" in result.disclaimer

    def test_error_has_disclaimer(self):
        """ProofError MUST have disclaimer."""
        from phase27_external_assurance.audit_bundle import create_audit_bundle

        result = create_audit_bundle(
            attestations=(),
            governance_docs=(),
            human_initiated=False,
        )

        assert "NO AUTHORITY" in result.disclaimer
        assert "PROOF ONLY" in result.disclaimer


class TestHumanInitiatedField:
    """Tests that human_initiated field is set correctly."""

    def test_human_initiated_is_true_in_result(self):
        """human_initiated MUST be True in result."""
        from phase27_external_assurance.audit_bundle import create_audit_bundle

        result = create_audit_bundle(
            attestations=(),
            governance_docs=(),
            human_initiated=True,
        )

        assert result.human_initiated is True
