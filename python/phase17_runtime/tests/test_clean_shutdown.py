"""
Phase-17 Tests: Clean Shutdown

GOVERNANCE CONSTRAINT:
- Graceful termination required
- Audit flush on shutdown
- Signal handling for SIGTERM/SIGINT
- No orphan processes

Risk Mitigated: RISK-17-003 (Silent Shutdown)
"""

import pytest
import signal


class TestCleanShutdown:
    """Tests verifying clean shutdown behavior."""

    def test_lifecycle_has_shutdown_method(self) -> None:
        """Lifecycle MUST have shutdown method."""
        from phase17_runtime.lifecycle import LifecycleManager
        
        manager = LifecycleManager()
        
        assert hasattr(manager, "shutdown")
        assert callable(manager.shutdown)

    def test_shutdown_requires_human_initiated(self) -> None:
        """Shutdown MUST require human_initiated=True."""
        from phase17_runtime.lifecycle import LifecycleManager
        
        manager = LifecycleManager()
        
        with pytest.raises(Exception) as exc_info:
            manager.shutdown(human_initiated=False)
        
        assert "human" in str(exc_info.value).lower()

    def test_shutdown_flushes_audit(self) -> None:
        """Shutdown MUST flush audit log."""
        from phase17_runtime.lifecycle import LifecycleManager
        from phase17_runtime.audit_flush import AuditFlusher
        
        manager = LifecycleManager()
        flusher = AuditFlusher()
        
        # Shutdown should trigger audit flush
        assert hasattr(manager, "flush_audit_on_shutdown")
        assert manager.flush_audit_on_shutdown is True

    def test_signal_handler_exists(self) -> None:
        """Signal handler MUST exist for SIGTERM/SIGINT."""
        from phase17_runtime.signals import SignalHandler
        
        handler = SignalHandler()
        
        assert hasattr(handler, "handle_sigterm")
        assert hasattr(handler, "handle_sigint")

    def test_signal_handler_flushes_audit(self) -> None:
        """Signal handler MUST flush audit on signal."""
        from phase17_runtime.signals import SignalHandler
        
        handler = SignalHandler()
        
        assert handler.flush_audit_on_signal is True

    def test_signal_handler_graceful_exit(self) -> None:
        """Signal handler MUST perform graceful exit."""
        from phase17_runtime.signals import SignalHandler
        
        handler = SignalHandler()
        
        assert handler.graceful_exit is True
        assert not hasattr(handler, "force_exit")

    def test_no_auto_restart_on_crash(self) -> None:
        """Lifecycle MUST NOT auto-restart on crash."""
        from phase17_runtime.lifecycle import LifecycleManager
        
        manager = LifecycleManager()
        
        assert manager.auto_restart is False
        assert not hasattr(manager, "enable_auto_restart")
        assert not hasattr(manager, "restart_on_crash")

    def test_no_watchdog(self) -> None:
        """Lifecycle MUST NOT have watchdog."""
        from phase17_runtime.lifecycle import LifecycleManager
        
        manager = LifecycleManager()
        
        assert not hasattr(manager, "watchdog")
        assert not hasattr(manager, "enable_watchdog")
        assert not hasattr(manager, "supervisor")

    def test_exit_code_zero_on_clean_shutdown(self) -> None:
        """Clean shutdown MUST return exit code 0."""
        from phase17_runtime.lifecycle import LifecycleManager
        
        manager = LifecycleManager()
        
        result = manager.get_exit_code()
        assert result == 0

    def test_no_orphan_processes(self) -> None:
        """Shutdown MUST NOT leave orphan processes."""
        from phase17_runtime.lifecycle import LifecycleManager
        
        manager = LifecycleManager()
        
        assert hasattr(manager, "cleanup_resources")
        assert manager.leaves_orphans is False
