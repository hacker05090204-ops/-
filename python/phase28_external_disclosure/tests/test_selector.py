"""
Phase-28 Selector Tests

NO AUTHORITY / PRESENTATION ONLY

Tests for Phase-28 proof selection.
Selection MUST be human-initiated.
Selection MUST NOT filter, rank, or recommend.
"""

import pytest
from datetime import datetime, timezone


class TestSelectRequiresHumanInitiated:
    """Tests that selection requires human_initiated=True."""

    def test_select_requires_human_initiated(self):
        """select_proofs MUST require human_initiated=True."""
        from phase28_external_disclosure import select_proofs
        
        result = select_proofs(
            attestation_ids=["att-001"],
            bundle_ids=["bundle-001"],
            human_initiated=True,
        )
        
        # Should succeed with human_initiated=True
        assert result is not None
        assert not hasattr(result, 'error_type')

    def test_select_refuses_without_human_initiated(self):
        """select_proofs MUST refuse if human_initiated=False."""
        from phase28_external_disclosure import select_proofs, PresentationError
        
        result = select_proofs(
            attestation_ids=["att-001"],
            bundle_ids=["bundle-001"],
            human_initiated=False,
        )
        
        # Should return error
        assert isinstance(result, PresentationError)
        assert result.error_type == "HUMAN_INITIATION_REQUIRED"


class TestSelectNoFiltering:
    """Tests that selection does NOT filter."""

    def test_select_does_not_filter(self):
        """Selection MUST NOT filter proofs."""
        from phase28_external_disclosure import select_proofs, ProofSelection
        
        # Select multiple proofs
        result = select_proofs(
            attestation_ids=["att-001", "att-002", "att-003"],
            bundle_ids=["bundle-001", "bundle-002"],
            human_initiated=True,
        )
        
        # All selected proofs should be included
        assert isinstance(result, ProofSelection)
        assert len(result.attestation_ids) == 3
        assert len(result.bundle_ids) == 2


class TestSelectNoRanking:
    """Tests that selection does NOT rank."""

    def test_select_does_not_rank(self):
        """Selection MUST NOT rank proofs."""
        from phase28_external_disclosure import select_proofs, ProofSelection
        
        # Select proofs in specific order
        result = select_proofs(
            attestation_ids=["att-003", "att-001", "att-002"],
            bundle_ids=["bundle-002", "bundle-001"],
            human_initiated=True,
        )
        
        # Order should be preserved (not reordered by ranking)
        assert isinstance(result, ProofSelection)
        assert result.attestation_ids[0] == "att-003"
        assert result.bundle_ids[0] == "bundle-002"


class TestSelectNoRecommendations:
    """Tests that selection does NOT recommend."""

    def test_select_does_not_recommend(self):
        """Selection MUST NOT recommend proofs."""
        from phase28_external_disclosure import select_proofs, ProofSelection
        
        result = select_proofs(
            attestation_ids=["att-001"],
            bundle_ids=[],
            human_initiated=True,
        )
        
        # Should only contain what was selected, no recommendations
        assert isinstance(result, ProofSelection)
        assert len(result.attestation_ids) == 1
        assert len(result.bundle_ids) == 0


class TestSelectRecordsOnly:
    """Tests that selection only records, does not modify."""

    def test_select_records_selection_only(self):
        """Selection MUST only record human selection."""
        from phase28_external_disclosure import select_proofs, ProofSelection
        
        result = select_proofs(
            attestation_ids=["att-001"],
            bundle_ids=["bundle-001"],
            human_initiated=True,
        )
        
        # Should be ProofSelection with recorded data
        assert isinstance(result, ProofSelection)
        assert result.selected_by == "HUMAN"
        assert result.human_initiated is True


class TestListAvailableProofs:
    """Tests for list_available_proofs function."""

    def test_list_requires_human_initiated(self):
        """list_available_proofs MUST require human_initiated=True."""
        from phase28_external_disclosure import list_available_proofs
        
        result = list_available_proofs(human_initiated=True)
        
        # Should succeed
        assert result is not None

    def test_list_refuses_without_human_initiated(self):
        """list_available_proofs MUST refuse if human_initiated=False."""
        from phase28_external_disclosure import list_available_proofs, PresentationError
        
        result = list_available_proofs(human_initiated=False)
        
        # Should return error
        assert isinstance(result, PresentationError)
        assert result.error_type == "HUMAN_INITIATION_REQUIRED"
