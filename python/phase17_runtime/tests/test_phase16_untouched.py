"""
Phase-17 Tests: Phase-16 Untouched

GOVERNANCE CONSTRAINT:
- Phase-16 UI code MUST NOT be modified
- Phase-16 behavior MUST NOT change
- Runtime loads Phase-16 exactly as-is

Risk Mitigated: RISK-17-004 (UI Mutation)
"""

import pytest
import inspect


class TestPhase16Untouched:
    """Tests verifying Phase-16 is not modified."""

    def test_no_phase16_modification_methods(self) -> None:
        """Launcher MUST NOT have Phase-16 modification methods."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert not hasattr(launcher, "modify_ui")
        assert not hasattr(launcher, "inject_code")
        assert not hasattr(launcher, "patch_phase16")
        assert not hasattr(launcher, "override_renderer")

    def test_no_dom_manipulation(self) -> None:
        """Launcher MUST NOT have DOM manipulation."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert not hasattr(launcher, "manipulate_dom")
        assert not hasattr(launcher, "inject_script")
        assert not hasattr(launcher, "modify_element")

    def test_no_style_injection(self) -> None:
        """Launcher MUST NOT inject styles."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert not hasattr(launcher, "inject_style")
        assert not hasattr(launcher, "add_css")
        assert not hasattr(launcher, "modify_style")

    def test_loads_phase16_as_is(self) -> None:
        """Launcher MUST load Phase-16 as-is."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert hasattr(launcher, "load_ui")
        assert launcher.modifies_ui is False

    def test_no_ui_element_addition(self) -> None:
        """Launcher MUST NOT add UI elements."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert not hasattr(launcher, "add_element")
        assert not hasattr(launcher, "insert_component")
        assert launcher.adds_ui_elements is False

    def test_no_ui_element_removal(self) -> None:
        """Launcher MUST NOT remove UI elements."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert not hasattr(launcher, "remove_element")
        assert not hasattr(launcher, "hide_component")
        assert launcher.removes_ui_elements is False

    def test_no_monkey_patching(self) -> None:
        """Runtime MUST NOT monkey-patch Phase-16."""
        from phase17_runtime import launcher
        
        source = inspect.getsource(launcher)
        
        # No monkey-patching patterns
        assert "phase16_ui." not in source or "import" in source
        assert "setattr(phase16" not in source
        assert "__dict__" not in source

    def test_phase16_renderer_unchanged(self) -> None:
        """Phase-16 renderer MUST be unchanged."""
        from phase16_ui.renderer import UIRenderer
        
        # Verify Phase-16 renderer still has original constraints
        renderer = UIRenderer()
        assert renderer.headless is False
        assert renderer.requires_visible_browser() is True

    def test_phase16_strings_unchanged(self) -> None:
        """Phase-16 strings MUST be unchanged."""
        from phase16_ui.strings import UIStrings
        
        # Verify mandatory disclaimer still exists
        assert hasattr(UIStrings, "CVE_DISCLAIMER")
        assert "reference-only" in UIStrings.CVE_DISCLAIMER.lower()

    def test_runtime_uses_phase16_public_interface_only(self) -> None:
        """Runtime MUST use Phase-16 public interface only."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        # Should only use public interface
        assert launcher.uses_public_interface_only is True
        assert not hasattr(launcher, "_access_phase16_internals")
