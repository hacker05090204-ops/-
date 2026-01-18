"""
Phase-17 Tests: No Headless Mode

GOVERNANCE CONSTRAINT:
- Visible browser window required
- Headless mode is PROHIBITED

Risk Mitigated: RISK-17-003 (Silent Startup)
"""

import pytest


class TestNoHeadlessMode:
    """Tests verifying headless mode is prohibited."""

    def test_launcher_rejects_headless_true(self) -> None:
        """Launcher MUST reject headless=True."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        with pytest.raises(Exception) as exc_info:
            launcher.launch(headless=True)
        
        assert "headless" in str(exc_info.value).lower()

    def test_launcher_default_is_visible(self) -> None:
        """Launcher default MUST be visible (not headless)."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert launcher.headless is False
        assert launcher.is_headless is False

    def test_launcher_has_no_headless_option(self) -> None:
        """Launcher MUST NOT have enable_headless method."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert not hasattr(launcher, "enable_headless")
        assert not hasattr(launcher, "set_headless")

    def test_config_rejects_headless(self) -> None:
        """Runtime config MUST reject headless setting."""
        from phase17_runtime.config import RuntimeConfig
        
        with pytest.raises(Exception) as exc_info:
            RuntimeConfig(headless=True)
        
        assert "headless" in str(exc_info.value).lower()

    def test_config_default_visible(self) -> None:
        """Runtime config default MUST be visible."""
        from phase17_runtime.config import RuntimeConfig
        
        config = RuntimeConfig()
        
        assert config.headless is False
        assert config.visible is True

    def test_launcher_requires_visible_true(self) -> None:
        """Launcher MUST require visible=True."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert launcher.requires_visible() is True

    def test_no_headless_in_source_code(self, forbidden_patterns: list[str]) -> None:
        """Source code MUST NOT set headless=True as default or assignment."""
        import inspect
        from phase17_runtime import launcher
        
        source = inspect.getsource(launcher)
        
        # Check that headless is never set to True as a default value
        # (it may appear in docstrings or error messages)
        lines = source.split('\n')
        for line in lines:
            # Skip comments and docstrings
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('"') or stripped.startswith("'"):
                continue
            # Check actual code assignments
            if 'self.headless = True' in line or 'self.is_headless = True' in line:
                assert False, f"Found headless=True assignment: {line}"

    def test_launcher_visible_window_check(self) -> None:
        """Launcher MUST have visible window check."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert hasattr(launcher, "is_window_visible")
        assert launcher.is_window_visible() is True
