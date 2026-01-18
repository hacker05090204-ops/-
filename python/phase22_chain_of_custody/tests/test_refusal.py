"""
Phase-22 Refusal Tests

Tests verifying refusal to attest is always allowed.
"""

import pytest


class TestRefusalAllowed:
    """Tests verifying refusal is always allowed."""

    def test_refusal_is_recorded(
        self,
        sample_evidence_hash: str,
        sample_timestamp: str,
        sample_attestor_id: str,
        sample_refusal_reason: str,
    ) -> None:
        """Refusal must be recorded."""
        from phase22_chain_of_custody.refusal import record_refusal
        
        refusal = record_refusal(
            evidence_hash=sample_evidence_hash,
            attestor_id=sample_attestor_id,
            reason=sample_refusal_reason,
            timestamp=sample_timestamp,
        )
        
        assert refusal.refused is True
        assert refusal.reason == sample_refusal_reason

    def test_refusal_accepts_any_reason(
        self,
        sample_evidence_hash: str,
        sample_timestamp: str,
        sample_attestor_id: str,
    ) -> None:
        """Refusal must accept any reason (not analyzed)."""
        from phase22_chain_of_custody.refusal import record_refusal
        
        reasons = [
            "",  # Empty is valid
            "No.",
            "I cannot attest.",
            "🚫",
            "a" * 10000,
        ]
        
        for reason in reasons:
            refusal = record_refusal(
                evidence_hash=sample_evidence_hash,
                attestor_id=sample_attestor_id,
                reason=reason,
                timestamp=sample_timestamp,
            )
            assert refusal.refused is True
            assert refusal.reason == reason


class TestRefusalHumanAttribution:
    """Tests verifying human attribution in refusals."""

    def test_refusal_has_human_initiated_true(
        self,
        sample_evidence_hash: str,
        sample_timestamp: str,
        sample_attestor_id: str,
        sample_refusal_reason: str,
    ) -> None:
        """Refusal must have human_initiated=True."""
        from phase22_chain_of_custody.refusal import record_refusal
        
        refusal = record_refusal(
            evidence_hash=sample_evidence_hash,
            attestor_id=sample_attestor_id,
            reason=sample_refusal_reason,
            timestamp=sample_timestamp,
        )
        
        assert refusal.human_initiated is True

    def test_refusal_has_actor_human(
        self,
        sample_evidence_hash: str,
        sample_timestamp: str,
        sample_attestor_id: str,
        sample_refusal_reason: str,
    ) -> None:
        """Refusal must have actor='HUMAN'."""
        from phase22_chain_of_custody.refusal import record_refusal
        
        refusal = record_refusal(
            evidence_hash=sample_evidence_hash,
            attestor_id=sample_attestor_id,
            reason=sample_refusal_reason,
            timestamp=sample_timestamp,
        )
        
        assert refusal.actor == "HUMAN"


class TestRefusalDoesNotBlock:
    """Tests verifying refusal does not block operation."""

    def test_refusal_is_valid_response(
        self,
        sample_evidence_hash: str,
        sample_timestamp: str,
        sample_attestor_id: str,
        sample_refusal_reason: str,
    ) -> None:
        """Refusal must be a valid, complete response."""
        from phase22_chain_of_custody.refusal import record_refusal
        
        # Should not raise any exception
        refusal = record_refusal(
            evidence_hash=sample_evidence_hash,
            attestor_id=sample_attestor_id,
            reason=sample_refusal_reason,
            timestamp=sample_timestamp,
        )
        
        # Refusal is a valid response
        assert refusal is not None
        assert refusal.refused is True

