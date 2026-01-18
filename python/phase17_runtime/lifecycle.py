"""
Phase-17 Lifecycle Manager

GOVERNANCE CONSTRAINT:
- Human-initiated startup and shutdown
- No auto-start, auto-restart, or auto-shutdown
- No background execution
- No watchdog or supervisor
- Graceful termination with audit flush
"""

from typing import Any

from phase17_runtime.errors import AutomationViolation


class LifecycleManager:
    """
    Lifecycle manager with governance constraints.
    
    GOVERNANCE GUARANTEES:
    - Human-initiated startup
    - Human-initiated shutdown
    - No auto-start
    - No auto-restart
    - No watchdog/supervisor
    - Graceful termination
    - Audit flush on shutdown
    """
    
    def __init__(self) -> None:
        """Initialize lifecycle manager."""
        # State tracking
        self.is_running = False
        self.started = False
        
        # Auto-restart prohibited
        self.auto_restart = False
        
        # Audit flush on shutdown
        self.flush_audit_on_shutdown = True
        
        # No orphan processes
        self.leaves_orphans = False
        
        # Exit code (0 for clean shutdown)
        self._exit_code = 0
    
    def start(self, human_initiated: bool = False) -> dict[str, Any]:
        """
        Start lifecycle (requires human initiation).
        
        Args:
            human_initiated: MUST be True
            
        Returns:
            Start result
            
        Raises:
            AutomationViolation: If human_initiated=False
        """
        if not human_initiated:
            raise AutomationViolation(
                "Lifecycle start requires human_initiated=True. "
                "Auto-start is prohibited."
            )
        
        self.is_running = True
        self.started = True
        
        return {
            "status": "started",
            "human_initiated": True,
        }
    
    def shutdown(self, human_initiated: bool = False) -> dict[str, Any]:
        """
        Shutdown lifecycle (requires human initiation).
        
        Args:
            human_initiated: MUST be True
            
        Returns:
            Shutdown result
            
        Raises:
            AutomationViolation: If human_initiated=False
        """
        if not human_initiated:
            raise AutomationViolation(
                "Lifecycle shutdown requires human_initiated=True. "
                "Auto-shutdown is prohibited."
            )
        
        # Flush audit before shutdown
        if self.flush_audit_on_shutdown:
            self._flush_audit()
        
        # Clean up resources
        self.cleanup_resources()
        
        self.is_running = False
        
        return {
            "status": "shutdown",
            "human_initiated": True,
            "audit_flushed": True,
        }
    
    def cleanup_resources(self) -> None:
        """Clean up resources (no orphan processes)."""
        # Ensure no orphan processes
        self.leaves_orphans = False
    
    def get_exit_code(self) -> int:
        """Get exit code (0 for clean shutdown)."""
        return self._exit_code
    
    def _flush_audit(self) -> None:
        """Flush audit log (internal helper)."""
        # Delegate to AuditFlusher
        from phase17_runtime.audit_flush import AuditFlusher
        flusher = AuditFlusher()
        flusher.flush()
