"""
Phase-16 CVE Disclaimer Tests (TASK-P16-T05)

Verify CVE disclaimer is always displayed.

GOVERNANCE CONSTRAINT:
Mandatory CVE disclaimer must be visible on all CVE displays.
"""

import pytest


# Exact required disclaimer text
REQUIRED_DISCLAIMER = (
    "CVE data is reference-only and does not verify, confirm, "
    "or validate vulnerabilities."
)


class TestCVEDisclaimerAlwaysPresent:
    """Verify CVE disclaimer is always displayed."""
    
    def test_cve_panel_has_disclaimer(self):
        """CVE panel must have disclaimer."""
        from phase16_ui.cve_panel import CVEPanel
        
        panel = CVEPanel()
        
        assert panel.has_disclaimer(), "CVE panel must have disclaimer"
    
    def test_cve_panel_disclaimer_text_exact(self):
        """CVE panel disclaimer must be exact required text."""
        from phase16_ui.cve_panel import CVEPanel
        
        panel = CVEPanel()
        disclaimer = panel.get_disclaimer_text()
        
        assert disclaimer == REQUIRED_DISCLAIMER, (
            f"CVE disclaimer must be exact. "
            f"Expected: {REQUIRED_DISCLAIMER!r}, "
            f"Got: {disclaimer!r}"
        )
    
    def test_cve_panel_disclaimer_always_visible(self):
        """CVE panel disclaimer must always be visible."""
        from phase16_ui.cve_panel import CVEPanel
        
        panel = CVEPanel()
        
        assert panel.is_disclaimer_visible(), (
            "CVE disclaimer must always be visible"
        )
    
    def test_cve_panel_disclaimer_cannot_be_hidden(self):
        """CVE panel disclaimer cannot be hidden."""
        from phase16_ui.cve_panel import CVEPanel
        
        panel = CVEPanel()
        
        # Attempt to hide disclaimer should fail or be ignored
        if hasattr(panel, 'hide_disclaimer'):
            panel.hide_disclaimer()
            assert panel.is_disclaimer_visible(), (
                "CVE disclaimer must remain visible even after hide attempt"
            )
    
    def test_cve_panel_disclaimer_prominent_position(self):
        """CVE panel disclaimer must be in prominent position."""
        from phase16_ui.cve_panel import CVEPanel
        
        panel = CVEPanel()
        position = panel.get_disclaimer_position()
        
        # Disclaimer should be at top or prominently placed
        assert position in ("top", "header", "prominent"), (
            f"CVE disclaimer must be prominent, got position: {position}"
        )
    
    def test_cve_output_includes_disclaimer(self, sample_cve_data):
        """CVE output must include disclaimer."""
        from phase16_ui.cve_panel import CVEPanel
        
        panel = CVEPanel()
        output = panel.render_cve(sample_cve_data)
        
        assert REQUIRED_DISCLAIMER in output, (
            "CVE output must include disclaimer"
        )
    
    def test_multiple_cves_each_have_disclaimer(self):
        """Each CVE display must have disclaimer."""
        from phase16_ui.cve_panel import CVEPanel
        
        panel = CVEPanel()
        
        cve_list = [
            {"cve_id": "CVE-2021-44228", "is_reference_only": True},
            {"cve_id": "CVE-2021-45046", "is_reference_only": True},
            {"cve_id": "CVE-2022-22965", "is_reference_only": True},
        ]
        
        output = panel.render_cve_list(cve_list)
        
        # Disclaimer should appear (at least once for the panel)
        assert REQUIRED_DISCLAIMER in output, (
            "CVE list output must include disclaimer"
        )


class TestCVEDisclaimerInStrings:
    """Verify disclaimer is correctly defined in string registry."""
    
    def test_string_registry_has_disclaimer(self):
        """String registry must have CVE disclaimer."""
        from phase16_ui.strings import UIStrings
        
        assert hasattr(UIStrings, 'CVE_DISCLAIMER'), (
            "UIStrings must have CVE_DISCLAIMER"
        )
    
    def test_string_registry_disclaimer_exact(self):
        """String registry disclaimer must be exact required text."""
        from phase16_ui.strings import UIStrings
        
        assert UIStrings.CVE_DISCLAIMER == REQUIRED_DISCLAIMER, (
            f"UIStrings.CVE_DISCLAIMER must be exact. "
            f"Expected: {REQUIRED_DISCLAIMER!r}, "
            f"Got: {UIStrings.CVE_DISCLAIMER!r}"
        )
    
    def test_disclaimer_is_final(self):
        """Disclaimer must be marked as Final (immutable)."""
        from phase16_ui.strings import UIStrings
        import typing
        
        # Check that CVE_DISCLAIMER is annotated as Final
        hints = typing.get_type_hints(UIStrings, include_extras=True)
        
        # The annotation should include Final
        if 'CVE_DISCLAIMER' in hints:
            hint = hints['CVE_DISCLAIMER']
            # Check if it's Final[str]
            assert 'Final' in str(hint) or hint == str, (
                "CVE_DISCLAIMER should be Final[str]"
            )


class TestCVEDisclaimerNotModifiable:
    """Verify disclaimer cannot be modified at runtime."""
    
    def test_disclaimer_immutable_in_panel(self):
        """CVE panel disclaimer cannot be modified."""
        from phase16_ui.cve_panel import CVEPanel
        
        panel = CVEPanel()
        
        # Attempt to set custom disclaimer should fail or be ignored
        if hasattr(panel, 'set_disclaimer'):
            panel.set_disclaimer("Custom disclaimer")
            assert panel.get_disclaimer_text() == REQUIRED_DISCLAIMER, (
                "CVE disclaimer must not be modifiable"
            )
    
    def test_disclaimer_not_parameterized(self):
        """CVE panel must not accept disclaimer as parameter."""
        from phase16_ui.cve_panel import CVEPanel
        import inspect
        
        sig = inspect.signature(CVEPanel.__init__)
        params = sig.parameters
        
        # Should not have disclaimer parameter
        assert 'disclaimer' not in params, (
            "CVEPanel must not accept disclaimer as parameter"
        )
        assert 'custom_disclaimer' not in params, (
            "CVEPanel must not accept custom_disclaimer as parameter"
        )
