"""
Phase-22 Attestation Tests

Tests verifying human attestation recording.
"""

import pytest


class TestAttestationCreation:
    """Tests verifying attestation creation."""

    def test_create_attestation(
        self,
        sample_evidence_hash: str,
        sample_timestamp: str,
        sample_attestor_id: str,
        sample_attestation_text: str,
    ) -> None:
        """Attestation must be created with all required fields."""
        from phase22_chain_of_custody.attestation import create_attestation
        
        attestation = create_attestation(
            evidence_hash=sample_evidence_hash,
            attestor_id=sample_attestor_id,
            attestation_text=sample_attestation_text,
            timestamp=sample_timestamp,
        )
        
        assert attestation.evidence_hash == sample_evidence_hash
        assert attestation.attestor_id == sample_attestor_id
        assert attestation.attestation_text == sample_attestation_text

    def test_attestation_hash_is_sha256(
        self,
        sample_evidence_hash: str,
        sample_timestamp: str,
        sample_attestor_id: str,
        sample_attestation_text: str,
    ) -> None:
        """Attestation hash must be SHA-256 format."""
        from phase22_chain_of_custody.attestation import create_attestation
        
        attestation = create_attestation(
            evidence_hash=sample_evidence_hash,
            attestor_id=sample_attestor_id,
            attestation_text=sample_attestation_text,
            timestamp=sample_timestamp,
        )
        
        assert len(attestation.attestation_hash) == 64
        assert all(c in "0123456789abcdef" for c in attestation.attestation_hash)


class TestAttestationTextNotAnalyzed:
    """Tests verifying attestation text is not analyzed."""

    def test_any_text_accepted(
        self,
        sample_evidence_hash: str,
        sample_timestamp: str,
        sample_attestor_id: str,
    ) -> None:
        """Any attestation text must be accepted."""
        from phase22_chain_of_custody.attestation import create_attestation
        
        texts = [
            "",  # Empty
            "Short",
            "A" * 10000,  # Long
            "🔐 Unicode symbols",
            "Line1\nLine2\nLine3",
        ]
        
        for text in texts:
            attestation = create_attestation(
                evidence_hash=sample_evidence_hash,
                attestor_id=sample_attestor_id,
                attestation_text=text,
                timestamp=sample_timestamp,
            )
            assert attestation.attestation_text == text

    def test_text_stored_as_is(
        self,
        sample_evidence_hash: str,
        sample_timestamp: str,
        sample_attestor_id: str,
    ) -> None:
        """Attestation text must be stored exactly as provided."""
        from phase22_chain_of_custody.attestation import create_attestation
        
        text = "  Whitespace preserved  \n\ttabs too  "
        
        attestation = create_attestation(
            evidence_hash=sample_evidence_hash,
            attestor_id=sample_attestor_id,
            attestation_text=text,
            timestamp=sample_timestamp,
        )
        
        assert attestation.attestation_text == text


class TestHumanAttribution:
    """Tests verifying human attribution in attestations."""

    def test_attestation_has_human_initiated_true(
        self,
        sample_evidence_hash: str,
        sample_timestamp: str,
        sample_attestor_id: str,
        sample_attestation_text: str,
    ) -> None:
        """Attestation must have human_initiated=True."""
        from phase22_chain_of_custody.attestation import create_attestation
        
        attestation = create_attestation(
            evidence_hash=sample_evidence_hash,
            attestor_id=sample_attestor_id,
            attestation_text=sample_attestation_text,
            timestamp=sample_timestamp,
        )
        
        assert attestation.human_initiated is True

    def test_attestation_has_actor_human(
        self,
        sample_evidence_hash: str,
        sample_timestamp: str,
        sample_attestor_id: str,
        sample_attestation_text: str,
    ) -> None:
        """Attestation must have actor='HUMAN'."""
        from phase22_chain_of_custody.attestation import create_attestation
        
        attestation = create_attestation(
            evidence_hash=sample_evidence_hash,
            attestor_id=sample_attestor_id,
            attestation_text=sample_attestation_text,
            timestamp=sample_timestamp,
        )
        
        assert attestation.actor == "HUMAN"


class TestNoAutoGeneration:
    """Tests verifying no auto-generation of attestations."""

    def test_no_auto_generate_function(self) -> None:
        """No auto_generate function should exist."""
        import phase22_chain_of_custody.attestation as att_module
        
        assert not hasattr(att_module, "auto_generate")
        assert not hasattr(att_module, "generate_attestation")
        assert not hasattr(att_module, "auto_attest")

