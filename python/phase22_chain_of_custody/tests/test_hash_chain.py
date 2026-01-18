"""
Phase-22 Hash Chain Tests

Tests verifying hash-chained ledger functionality.
"""

import pytest


class TestHashChainCreation:
    """Tests verifying hash chain creation."""

    def test_first_entry_has_empty_previous_hash(
        self,
        sample_evidence_hash: str,
        sample_timestamp: str,
    ) -> None:
        """First entry must have empty previous_hash."""
        from phase22_chain_of_custody.hash_chain import create_chain_entry
        
        entry = create_chain_entry(
            evidence_hash=sample_evidence_hash,
            event_type="attestation",
            previous_hash="",
            timestamp=sample_timestamp,
        )
        
        assert entry.previous_hash == ""

    def test_subsequent_entry_links_to_previous(
        self,
        sample_evidence_hash: str,
        sample_timestamp: str,
    ) -> None:
        """Subsequent entries must link to previous entry hash."""
        from phase22_chain_of_custody.hash_chain import create_chain_entry
        
        first_entry = create_chain_entry(
            evidence_hash=sample_evidence_hash,
            event_type="attestation",
            previous_hash="",
            timestamp=sample_timestamp,
        )
        
        second_entry = create_chain_entry(
            evidence_hash=sample_evidence_hash,
            event_type="transfer",
            previous_hash=first_entry.entry_hash,
            timestamp=sample_timestamp,
        )
        
        assert second_entry.previous_hash == first_entry.entry_hash

    def test_entry_hash_is_sha256(
        self,
        sample_evidence_hash: str,
        sample_timestamp: str,
    ) -> None:
        """Entry hash must be SHA-256 format."""
        from phase22_chain_of_custody.hash_chain import create_chain_entry
        
        entry = create_chain_entry(
            evidence_hash=sample_evidence_hash,
            event_type="attestation",
            previous_hash="",
            timestamp=sample_timestamp,
        )
        
        assert len(entry.entry_hash) == 64
        assert all(c in "0123456789abcdef" for c in entry.entry_hash)


class TestHashChainVerification:
    """Tests verifying chain integrity verification."""

    def test_verify_valid_chain(
        self,
        sample_evidence_hash: str,
        sample_timestamp: str,
    ) -> None:
        """Valid chain must verify successfully."""
        from phase22_chain_of_custody.hash_chain import create_chain_entry, verify_chain
        
        entries = []
        
        # Create chain of 3 entries
        entry1 = create_chain_entry(
            evidence_hash=sample_evidence_hash,
            event_type="attestation",
            previous_hash="",
            timestamp=sample_timestamp,
        )
        entries.append(entry1)
        
        entry2 = create_chain_entry(
            evidence_hash=sample_evidence_hash,
            event_type="transfer",
            previous_hash=entry1.entry_hash,
            timestamp=sample_timestamp,
        )
        entries.append(entry2)
        
        entry3 = create_chain_entry(
            evidence_hash=sample_evidence_hash,
            event_type="attestation",
            previous_hash=entry2.entry_hash,
            timestamp=sample_timestamp,
        )
        entries.append(entry3)
        
        is_valid = verify_chain(entries)
        
        assert is_valid is True

    def test_detect_broken_chain(
        self,
        sample_evidence_hash: str,
        sample_timestamp: str,
    ) -> None:
        """Broken chain must be detected."""
        from phase22_chain_of_custody.hash_chain import create_chain_entry, verify_chain
        from phase22_chain_of_custody.types import CustodyEntry
        
        entry1 = create_chain_entry(
            evidence_hash=sample_evidence_hash,
            event_type="attestation",
            previous_hash="",
            timestamp=sample_timestamp,
        )
        
        # Create entry with wrong previous hash (broken chain)
        broken_entry = CustodyEntry(
            entry_id="broken-123",
            timestamp=sample_timestamp,
            previous_hash="wrong_hash",  # Should be entry1.entry_hash
            entry_hash="x" * 64,
            evidence_hash=sample_evidence_hash,
            event_type="transfer",
            human_initiated=True,
            actor="HUMAN",
        )
        
        is_valid = verify_chain([entry1, broken_entry])
        
        assert is_valid is False


class TestHumanAttribution:
    """Tests verifying human attribution in chain entries."""

    def test_entry_has_human_initiated_true(
        self,
        sample_evidence_hash: str,
        sample_timestamp: str,
    ) -> None:
        """Chain entry must have human_initiated=True."""
        from phase22_chain_of_custody.hash_chain import create_chain_entry
        
        entry = create_chain_entry(
            evidence_hash=sample_evidence_hash,
            event_type="attestation",
            previous_hash="",
            timestamp=sample_timestamp,
        )
        
        assert entry.human_initiated is True

    def test_entry_has_actor_human(
        self,
        sample_evidence_hash: str,
        sample_timestamp: str,
    ) -> None:
        """Chain entry must have actor='HUMAN'."""
        from phase22_chain_of_custody.hash_chain import create_chain_entry
        
        entry = create_chain_entry(
            evidence_hash=sample_evidence_hash,
            event_type="attestation",
            previous_hash="",
            timestamp=sample_timestamp,
        )
        
        assert entry.actor == "HUMAN"

