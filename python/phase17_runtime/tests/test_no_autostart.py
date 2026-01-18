"""
Phase-17 Tests: No Auto-Start

GOVERNANCE CONSTRAINT:
- Explicit user launch required
- No auto-start on boot
- No scheduled start
- No daemon mode

Risk Mitigated: RISK-17-001 (Automation), RISK-17-003 (Silent Startup)
"""

import pytest
import inspect


class TestNoAutoStart:
    """Tests verifying no auto-start capability."""

    def test_no_auto_start_config(self) -> None:
        """Config MUST have auto_start=False (never True)."""
        from phase17_runtime.config import RuntimeConfig
        
        config = RuntimeConfig()
        
        # auto_start exists but is always False
        assert config.auto_start is False
        assert not hasattr(config, "start_on_boot")
        assert not hasattr(config, "start_on_login")

    def test_config_rejects_auto_start(self) -> None:
        """Config MUST reject auto_start=True."""
        from phase17_runtime.config import RuntimeConfig
        
        with pytest.raises(Exception) as exc_info:
            RuntimeConfig(auto_start=True)
        
        assert "auto" in str(exc_info.value).lower()

    def test_no_boot_service_registration(self) -> None:
        """Launcher MUST NOT register boot service."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert not hasattr(launcher, "register_boot_service")
        assert not hasattr(launcher, "install_service")
        assert not hasattr(launcher, "enable_autostart")

    def test_no_login_item_registration(self) -> None:
        """Launcher MUST NOT register login item."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert not hasattr(launcher, "register_login_item")
        assert not hasattr(launcher, "add_to_startup")

    def test_no_scheduled_start(self) -> None:
        """Launcher MUST NOT have scheduled start."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert not hasattr(launcher, "schedule_start")
        assert not hasattr(launcher, "delayed_start")
        assert not hasattr(launcher, "timed_start")

    def test_no_daemon_mode(self) -> None:
        """Launcher MUST NOT have daemon mode."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert not hasattr(launcher, "run_as_daemon")
        assert not hasattr(launcher, "daemonize")
        assert launcher.daemon_mode is False

    def test_lifecycle_requires_explicit_start(self) -> None:
        """Lifecycle MUST require explicit start call."""
        from phase17_runtime.lifecycle import LifecycleManager
        
        manager = LifecycleManager()
        
        # Manager should not auto-start
        assert manager.is_running is False
        assert manager.started is False

    def test_lifecycle_start_requires_human(self) -> None:
        """Lifecycle start MUST require human_initiated=True."""
        from phase17_runtime.lifecycle import LifecycleManager
        
        manager = LifecycleManager()
        
        with pytest.raises(Exception) as exc_info:
            manager.start(human_initiated=False)
        
        assert "human" in str(exc_info.value).lower()

    def test_no_auto_start_in_source(self) -> None:
        """Source MUST NOT contain auto-start patterns."""
        from phase17_runtime import launcher
        
        source = inspect.getsource(launcher)
        
        assert "auto_start" not in source.lower()
        assert "autostart" not in source.lower()
        assert "start_on_boot" not in source.lower()
        assert "boot_service" not in source.lower()

    def test_explicit_launch_required(self) -> None:
        """Launch MUST be explicit (not automatic)."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert hasattr(launcher, "launch")
        assert launcher.requires_explicit_launch() is True
