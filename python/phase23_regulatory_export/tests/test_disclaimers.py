"""
Phase-23 Disclaimer Tests

Tests verifying static disclaimer injection.
"""

import pytest


class TestDisclaimerInjection:
    """Tests verifying disclaimer injection."""

    def test_get_disclaimers_for_jurisdiction(
        self,
        sample_jurisdiction_code: str,
    ) -> None:
        """Disclaimers must be retrievable for jurisdiction."""
        from phase23_regulatory_export.disclaimers import get_disclaimers
        
        disclaimers = get_disclaimers(sample_jurisdiction_code)
        
        assert isinstance(disclaimers, tuple)

    def test_disclaimers_are_static(
        self,
        sample_jurisdiction_code: str,
    ) -> None:
        """Disclaimers must be static (same every time)."""
        from phase23_regulatory_export.disclaimers import get_disclaimers
        
        disclaimers1 = get_disclaimers(sample_jurisdiction_code)
        disclaimers2 = get_disclaimers(sample_jurisdiction_code)
        
        assert disclaimers1 == disclaimers2

    def test_disclaimers_are_immutable(
        self,
        sample_jurisdiction_code: str,
    ) -> None:
        """Disclaimers must be immutable (tuple)."""
        from phase23_regulatory_export.disclaimers import get_disclaimers
        
        disclaimers = get_disclaimers(sample_jurisdiction_code)
        
        assert isinstance(disclaimers, tuple)


class TestNoDisclaimerGeneration:
    """Tests verifying no disclaimer generation."""

    def test_no_generate_disclaimer_function(self) -> None:
        """No generate_disclaimer function should exist."""
        import phase23_regulatory_export.disclaimers as disc_module
        
        assert not hasattr(disc_module, "generate_disclaimer")
        assert not hasattr(disc_module, "create_disclaimer")
        assert not hasattr(disc_module, "auto_disclaimer")


class TestDisclaimerContent:
    """Tests verifying disclaimer content is not analyzed."""

    def test_disclaimer_stored_as_is(
        self,
        sample_jurisdiction_code: str,
    ) -> None:
        """Disclaimers must be stored exactly as defined."""
        from phase23_regulatory_export.disclaimers import get_disclaimers
        
        disclaimers = get_disclaimers(sample_jurisdiction_code)
        
        # Each disclaimer should be a non-empty string
        for disclaimer in disclaimers:
            assert isinstance(disclaimer, str)

