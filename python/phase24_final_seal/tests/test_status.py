"""
Phase-24 Status Tests

Tests verifying governance status functionality.
"""

import pytest


class TestGovernanceStatus:
    """Tests verifying governance status."""

    def test_get_active_status(self) -> None:
        """Active status must be retrievable."""
        from phase24_final_seal.status import get_governance_status
        
        status = get_governance_status(
            sealed=False,
            decommissioned=False,
        )
        
        assert status.status == "active"
        assert status.sealed_at is None
        assert status.decommissioned_at is None

    def test_get_sealed_status(self, sample_timestamp: str) -> None:
        """Sealed status must be retrievable."""
        from phase24_final_seal.status import get_governance_status
        
        status = get_governance_status(
            sealed=True,
            decommissioned=False,
            sealed_at=sample_timestamp,
        )
        
        assert status.status == "sealed"
        assert status.sealed_at == sample_timestamp
        assert status.decommissioned_at is None

    def test_get_decommissioned_status(self, sample_timestamp: str) -> None:
        """Decommissioned status must be retrievable."""
        from phase24_final_seal.status import get_governance_status
        
        status = get_governance_status(
            sealed=True,
            decommissioned=True,
            sealed_at=sample_timestamp,
            decommissioned_at=sample_timestamp,
        )
        
        assert status.status == "decommissioned"
        assert status.decommissioned_at == sample_timestamp


class TestFrozenPhases:
    """Tests verifying frozen phases list."""

    def test_phases_frozen_is_tuple(self) -> None:
        """Frozen phases must be immutable tuple."""
        from phase24_final_seal.status import get_governance_status
        
        status = get_governance_status(
            sealed=True,
            decommissioned=False,
        )
        
        assert isinstance(status.phases_frozen, tuple)

    def test_all_phases_frozen_when_sealed(self) -> None:
        """All phases must be frozen when sealed."""
        from phase24_final_seal.status import get_governance_status
        
        status = get_governance_status(
            sealed=True,
            decommissioned=False,
        )
        
        # Phases 13-24 should be frozen
        expected_phases = tuple(range(13, 25))
        assert status.phases_frozen == expected_phases

