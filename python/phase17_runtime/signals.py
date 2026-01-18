"""
Phase-17 Signal Handler

GOVERNANCE CONSTRAINT:
- Handle SIGTERM and SIGINT for graceful shutdown
- Flush audit on signal
- No force exit without cleanup
- Graceful termination only
"""

import signal
from typing import Any, Callable, Optional


class SignalHandler:
    """
    Signal handler with governance constraints.
    
    GOVERNANCE GUARANTEES:
    - Handle SIGTERM for graceful shutdown
    - Handle SIGINT for graceful shutdown
    - Flush audit on signal
    - Graceful exit only (no force exit)
    """
    
    def __init__(self) -> None:
        """Initialize signal handler."""
        # Audit flush on signal
        self.flush_audit_on_signal = True
        
        # Graceful exit only
        self.graceful_exit = True
        
        # Registered handlers
        self._handlers: dict[int, Callable] = {}
    
    def handle_sigterm(self, signum: int, frame: Any) -> None:
        """
        Handle SIGTERM signal.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        self._graceful_shutdown("SIGTERM")
    
    def handle_sigint(self, signum: int, frame: Any) -> None:
        """
        Handle SIGINT signal.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        self._graceful_shutdown("SIGINT")
    
    def _graceful_shutdown(self, signal_name: str) -> None:
        """
        Perform graceful shutdown.
        
        Args:
            signal_name: Name of signal received
        """
        # Flush audit before exit
        if self.flush_audit_on_signal:
            from phase17_runtime.audit_flush import AuditFlusher
            flusher = AuditFlusher()
            flusher.flush()
        
        # Log shutdown
        from phase15_governance.audit import log_event
        log_event(
            event_type="RUNTIME_SHUTDOWN",
            data={"signal": signal_name, "graceful": True},
            attribution="SYSTEM",
        )
    
    def register_handlers(self) -> None:
        """Register signal handlers."""
        signal.signal(signal.SIGTERM, self.handle_sigterm)
        signal.signal(signal.SIGINT, self.handle_sigint)
        
        self._handlers[signal.SIGTERM] = self.handle_sigterm
        self._handlers[signal.SIGINT] = self.handle_sigint
    
    def unregister_handlers(self) -> None:
        """Unregister signal handlers."""
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        
        self._handlers.clear()
