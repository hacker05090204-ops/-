"""
Phase-27 Attestation Tests

NO AUTHORITY / PROOF ONLY

Tests for attestation generation functionality.
Tests MUST fail before implementation (PYTEST-FIRST).
"""

import pytest


class TestHumanInitiationRequired:
    """Tests that human_initiated=True is required."""

    def test_refuses_if_human_initiated_false(self):
        """MUST refuse if human_initiated=False."""
        from phase27_external_assurance.attestation import generate_attestation
        from phase27_external_assurance.types import ProofError

        result = generate_attestation(
            artifact_hashes=(),
            phases_covered=(13, 14, 15),
            human_initiated=False,
        )

        assert isinstance(result, ProofError)
        assert result.error_type == "HUMAN_INITIATION_REQUIRED"

    def test_refuses_if_human_initiated_missing(self):
        """MUST refuse if human_initiated is not provided."""
        from phase27_external_assurance.attestation import generate_attestation

        # Should raise TypeError because human_initiated is keyword-only
        with pytest.raises(TypeError):
            generate_attestation(
                artifact_hashes=(),
                phases_covered=(13, 14, 15),
            )

    def test_accepts_if_human_initiated_true(self):
        """MUST accept if human_initiated=True."""
        from phase27_external_assurance.attestation import generate_attestation
        from phase27_external_assurance.types import ComplianceAttestation

        result = generate_attestation(
            artifact_hashes=(),
            phases_covered=(13, 14, 15),
            human_initiated=True,
        )

        assert isinstance(result, ComplianceAttestation)


class TestAttestationGeneration:
    """Tests for attestation generation."""

    def test_generates_attestation_with_uuid(self):
        """Attestation MUST have UUID."""
        from phase27_external_assurance.attestation import generate_attestation

        result = generate_attestation(
            artifact_hashes=(),
            phases_covered=(13, 14, 15),
            human_initiated=True,
        )

        assert result.attestation_id is not None
        assert len(result.attestation_id) > 0

    def test_generates_attestation_with_timestamp(self):
        """Attestation MUST have timestamp."""
        from phase27_external_assurance.attestation import generate_attestation

        result = generate_attestation(
            artifact_hashes=(),
            phases_covered=(13, 14, 15),
            human_initiated=True,
        )

        assert result.timestamp is not None
        assert "T" in result.timestamp  # ISO-8601 format

    def test_attestation_includes_phases_covered(self):
        """Attestation MUST include phases covered."""
        from phase27_external_assurance.attestation import generate_attestation

        phases = (13, 14, 15, 16)
        result = generate_attestation(
            artifact_hashes=(),
            phases_covered=phases,
            human_initiated=True,
        )

        assert result.phases_covered == phases


class TestActorIsHuman:
    """Tests that actor is always HUMAN."""

    def test_actor_is_human(self):
        """Actor MUST be 'HUMAN'."""
        from phase27_external_assurance.attestation import generate_attestation

        result = generate_attestation(
            artifact_hashes=(),
            phases_covered=(13, 14, 15),
            human_initiated=True,
        )

        assert result.actor == "HUMAN"


class TestDisclaimerPresence:
    """Tests that disclaimer is present in output."""

    def test_attestation_has_disclaimer(self):
        """ComplianceAttestation MUST have disclaimer."""
        from phase27_external_assurance.attestation import generate_attestation

        result = generate_attestation(
            artifact_hashes=(),
            phases_covered=(13, 14, 15),
            human_initiated=True,
        )

        assert "NO AUTHORITY" in result.disclaimer
        assert "PROOF ONLY" in result.disclaimer

    def test_error_has_disclaimer(self):
        """ProofError MUST have disclaimer."""
        from phase27_external_assurance.attestation import generate_attestation

        result = generate_attestation(
            artifact_hashes=(),
            phases_covered=(13, 14, 15),
            human_initiated=False,
        )

        assert "NO AUTHORITY" in result.disclaimer
        assert "PROOF ONLY" in result.disclaimer


class TestHumanInitiatedField:
    """Tests that human_initiated field is set correctly."""

    def test_human_initiated_is_true_in_result(self):
        """human_initiated MUST be True in result."""
        from phase27_external_assurance.attestation import generate_attestation

        result = generate_attestation(
            artifact_hashes=(),
            phases_covered=(13, 14, 15),
            human_initiated=True,
        )

        assert result.human_initiated is True
