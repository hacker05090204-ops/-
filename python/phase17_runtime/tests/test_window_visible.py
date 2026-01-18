"""
Phase-17 Tests: Window Visibility

GOVERNANCE CONSTRAINT:
- Window MUST be visible on screen
- No minimized, hidden, or offscreen windows

Risk Mitigated: RISK-17-003 (Silent Startup)
"""

import pytest


class TestWindowVisibility:
    """Tests verifying window visibility requirements."""

    def test_window_not_minimized_on_start(self) -> None:
        """Window MUST NOT start minimized."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert launcher.allow_minimized is False
        assert launcher.start_minimized is False

    def test_window_not_hidden_on_start(self) -> None:
        """Window MUST NOT start hidden."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert launcher.allow_hidden is False
        assert launcher.start_hidden is False

    def test_window_not_tray_only(self) -> None:
        """Window MUST NOT be tray-only."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert launcher.tray_only is False
        assert not hasattr(launcher, "enable_tray_only")

    def test_window_on_screen(self) -> None:
        """Window MUST be on screen (not offscreen)."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert launcher.allow_offscreen is False

    def test_window_has_focus_capability(self) -> None:
        """Window MUST be focusable."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert launcher.focusable is True

    def test_config_rejects_minimized_start(self) -> None:
        """Config MUST reject start_minimized=True."""
        from phase17_runtime.config import RuntimeConfig
        
        with pytest.raises(Exception) as exc_info:
            RuntimeConfig(start_minimized=True)
        
        assert "minimized" in str(exc_info.value).lower()

    def test_config_rejects_hidden_start(self) -> None:
        """Config MUST reject start_hidden=True."""
        from phase17_runtime.config import RuntimeConfig
        
        with pytest.raises(Exception) as exc_info:
            RuntimeConfig(start_hidden=True)
        
        assert "hidden" in str(exc_info.value).lower()

    def test_config_rejects_tray_only(self) -> None:
        """Config MUST reject tray_only=True."""
        from phase17_runtime.config import RuntimeConfig
        
        with pytest.raises(Exception) as exc_info:
            RuntimeConfig(tray_only=True)
        
        assert "tray" in str(exc_info.value).lower()

    def test_launcher_visibility_check_method(self) -> None:
        """Launcher MUST have visibility check method."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert hasattr(launcher, "check_visibility")
        result = launcher.check_visibility()
        assert result["visible"] is True
        assert result["minimized"] is False
        assert result["hidden"] is False
