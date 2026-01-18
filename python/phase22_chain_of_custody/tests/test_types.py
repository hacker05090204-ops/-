"""
Phase-22 Type Tests

Tests verifying immutable data structures with no scoring fields.
"""

import pytest
from dataclasses import FrozenInstanceError


class TestCustodyEntryImmutability:
    """Tests verifying CustodyEntry is immutable."""

    def test_custody_entry_is_frozen(self, sample_evidence_hash: str, sample_timestamp: str) -> None:
        """CustodyEntry must be a frozen dataclass."""
        from phase22_chain_of_custody.types import CustodyEntry
        
        entry = CustodyEntry(
            entry_id="entry-123",
            timestamp=sample_timestamp,
            previous_hash="",
            entry_hash="b" * 64,
            evidence_hash=sample_evidence_hash,
            event_type="attestation",
            human_initiated=True,
            actor="HUMAN",
        )
        
        with pytest.raises(FrozenInstanceError):
            entry.entry_id = "modified"

    def test_custody_entry_has_human_initiated(self, sample_evidence_hash: str, sample_timestamp: str) -> None:
        """CustodyEntry must have human_initiated field."""
        from phase22_chain_of_custody.types import CustodyEntry
        
        entry = CustodyEntry(
            entry_id="entry-123",
            timestamp=sample_timestamp,
            previous_hash="",
            entry_hash="b" * 64,
            evidence_hash=sample_evidence_hash,
            event_type="attestation",
            human_initiated=True,
            actor="HUMAN",
        )
        
        assert entry.human_initiated is True

    def test_custody_entry_has_actor_human(self, sample_evidence_hash: str, sample_timestamp: str) -> None:
        """CustodyEntry must have actor='HUMAN'."""
        from phase22_chain_of_custody.types import CustodyEntry
        
        entry = CustodyEntry(
            entry_id="entry-123",
            timestamp=sample_timestamp,
            previous_hash="",
            entry_hash="b" * 64,
            evidence_hash=sample_evidence_hash,
            event_type="attestation",
            human_initiated=True,
            actor="HUMAN",
        )
        
        assert entry.actor == "HUMAN"


class TestAttestationImmutability:
    """Tests verifying Attestation is immutable."""

    def test_attestation_is_frozen(
        self,
        sample_evidence_hash: str,
        sample_timestamp: str,
        sample_attestor_id: str,
        sample_attestation_text: str,
    ) -> None:
        """Attestation must be a frozen dataclass."""
        from phase22_chain_of_custody.types import Attestation
        
        attestation = Attestation(
            attestation_id="att-123",
            timestamp=sample_timestamp,
            attestor_id=sample_attestor_id,
            attestation_text=sample_attestation_text,
            evidence_hash=sample_evidence_hash,
            attestation_hash="c" * 64,
            human_initiated=True,
            actor="HUMAN",
        )
        
        with pytest.raises(FrozenInstanceError):
            attestation.attestation_id = "modified"


class TestCustodyTransferImmutability:
    """Tests verifying CustodyTransfer is immutable."""

    def test_custody_transfer_is_frozen(
        self,
        sample_evidence_hash: str,
        sample_timestamp: str,
        sample_attestor_id: str,
        sample_attestation_text: str,
        sample_from_party: str,
        sample_to_party: str,
    ) -> None:
        """CustodyTransfer must be a frozen dataclass."""
        from phase22_chain_of_custody.types import CustodyTransfer, Attestation
        
        attestation = Attestation(
            attestation_id="att-123",
            timestamp=sample_timestamp,
            attestor_id=sample_attestor_id,
            attestation_text=sample_attestation_text,
            evidence_hash=sample_evidence_hash,
            attestation_hash="c" * 64,
            human_initiated=True,
            actor="HUMAN",
        )
        
        transfer = CustodyTransfer(
            transfer_id="xfer-123",
            timestamp=sample_timestamp,
            from_party=sample_from_party,
            to_party=sample_to_party,
            evidence_hash=sample_evidence_hash,
            attestation=attestation,
            transfer_hash="d" * 64,
            human_initiated=True,
            actor="HUMAN",
        )
        
        with pytest.raises(FrozenInstanceError):
            transfer.transfer_id = "modified"


class TestNoScoringFields:
    """Tests verifying no scoring fields exist."""

    def test_custody_entry_has_no_score_field(self) -> None:
        """CustodyEntry must not have score field."""
        from phase22_chain_of_custody.types import CustodyEntry
        
        assert not hasattr(CustodyEntry, "score")
        assert not hasattr(CustodyEntry, "quality")
        assert not hasattr(CustodyEntry, "validity")

    def test_attestation_has_no_score_field(self) -> None:
        """Attestation must not have score field."""
        from phase22_chain_of_custody.types import Attestation
        
        assert not hasattr(Attestation, "score")
        assert not hasattr(Attestation, "confidence")
        assert not hasattr(Attestation, "validity")

