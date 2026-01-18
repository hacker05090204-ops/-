"""
Phase-23 Jurisdiction Tests

Tests verifying human jurisdiction selection.
"""

import pytest


class TestJurisdictionSelection:
    """Tests verifying jurisdiction selection."""

    def test_select_jurisdiction(
        self,
        sample_jurisdiction_code: str,
        sample_jurisdiction_name: str,
        sample_selected_by: str,
        sample_timestamp: str,
    ) -> None:
        """Jurisdiction must be selected by human."""
        from phase23_regulatory_export.jurisdiction import select_jurisdiction
        
        selection = select_jurisdiction(
            jurisdiction_code=sample_jurisdiction_code,
            jurisdiction_name=sample_jurisdiction_name,
            selected_by=sample_selected_by,
            timestamp=sample_timestamp,
        )
        
        assert selection.jurisdiction_code == sample_jurisdiction_code
        assert selection.jurisdiction_name == sample_jurisdiction_name
        assert selection.selected_by == sample_selected_by

    def test_selection_has_human_initiated_true(
        self,
        sample_jurisdiction_code: str,
        sample_jurisdiction_name: str,
        sample_selected_by: str,
        sample_timestamp: str,
    ) -> None:
        """Selection must have human_initiated=True."""
        from phase23_regulatory_export.jurisdiction import select_jurisdiction
        
        selection = select_jurisdiction(
            jurisdiction_code=sample_jurisdiction_code,
            jurisdiction_name=sample_jurisdiction_name,
            selected_by=sample_selected_by,
            timestamp=sample_timestamp,
        )
        
        assert selection.human_initiated is True

    def test_selection_has_actor_human(
        self,
        sample_jurisdiction_code: str,
        sample_jurisdiction_name: str,
        sample_selected_by: str,
        sample_timestamp: str,
    ) -> None:
        """Selection must have actor='HUMAN'."""
        from phase23_regulatory_export.jurisdiction import select_jurisdiction
        
        selection = select_jurisdiction(
            jurisdiction_code=sample_jurisdiction_code,
            jurisdiction_name=sample_jurisdiction_name,
            selected_by=sample_selected_by,
            timestamp=sample_timestamp,
        )
        
        assert selection.actor == "HUMAN"


class TestNoAutoSelection:
    """Tests verifying no auto-selection of jurisdiction."""

    def test_no_auto_select_function(self) -> None:
        """No auto_select function should exist."""
        import phase23_regulatory_export.jurisdiction as jur_module
        
        assert not hasattr(jur_module, "auto_select")
        assert not hasattr(jur_module, "detect_jurisdiction")
        assert not hasattr(jur_module, "recommend_jurisdiction")

    def test_no_default_jurisdiction(self) -> None:
        """No default jurisdiction should exist."""
        import phase23_regulatory_export.jurisdiction as jur_module
        
        assert not hasattr(jur_module, "DEFAULT_JURISDICTION")
        assert not hasattr(jur_module, "default_jurisdiction")


class TestAvailableJurisdictions:
    """Tests verifying available jurisdictions list."""

    def test_get_available_jurisdictions(self) -> None:
        """Available jurisdictions must be retrievable."""
        from phase23_regulatory_export.jurisdiction import get_available_jurisdictions
        
        jurisdictions = get_available_jurisdictions()
        
        assert isinstance(jurisdictions, tuple)
        assert len(jurisdictions) > 0

    def test_jurisdictions_are_static(self) -> None:
        """Jurisdictions list must be static (immutable)."""
        from phase23_regulatory_export.jurisdiction import get_available_jurisdictions
        
        jurisdictions = get_available_jurisdictions()
        
        # Should be tuple (immutable)
        assert isinstance(jurisdictions, tuple)

