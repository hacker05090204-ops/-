"""
Phase-16 UI Event Logger Module

GOVERNANCE CONSTRAINT:
- All UI events logged with HUMAN attribution
- Logs via Phase-15 audit trail
- No CVE response body in logs
"""

from typing import Any, Optional
from datetime import datetime, timezone


class UIEventLogger:
    """
    UI event logger with HUMAN attribution.
    
    GOVERNANCE GUARANTEES:
    - All events attributed to HUMAN
    - Logs via Phase-15 audit
    - No CVE response body logged
    - No API keys logged
    """
    
    def __init__(self, session_id: Optional[str] = None) -> None:
        """
        Initialize event logger.
        
        Args:
            session_id: Session identifier for audit trail
        """
        self.session_id = session_id or self._generate_session_id()
    
    def _generate_session_id(self) -> str:
        """Generate session ID."""
        import uuid
        return f"ui-session-{uuid.uuid4().hex[:8]}"
    
    def _log_to_phase15(
        self,
        event_type: str,
        data: dict[str, Any],
    ) -> None:
        """
        Log event to Phase-15 audit trail.
        
        Args:
            event_type: Type of UI event
            data: Event data (no sensitive info)
        """
        from phase15_governance.audit import log_event
        
        log_event(
            event_type=event_type,
            data={
                **data,
                "session_id": self.session_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            attribution="HUMAN",  # Always HUMAN for UI events
        )
    
    def log_click(self, element_id: str) -> None:
        """
        Log UI click event.
        
        Args:
            element_id: ID of clicked element
        """
        self._log_to_phase15(
            event_type="UI_CLICK",
            data={"element_id": element_id},
        )
    
    def log_navigate(self, url: str) -> None:
        """
        Log navigation event.
        
        Args:
            url: Navigation target URL
        """
        self._log_to_phase15(
            event_type="UI_NAVIGATE",
            data={"url": url},
        )
    
    def log_confirm(self, action: str) -> None:
        """
        Log confirmation event.
        
        Args:
            action: Action that was confirmed
        """
        self._log_to_phase15(
            event_type="UI_CONFIRM",
            data={"action": action},
        )
    
    def log_cancel(self, action: str) -> None:
        """
        Log cancellation event.
        
        Args:
            action: Action that was cancelled
        """
        self._log_to_phase15(
            event_type="UI_CANCEL",
            data={"action": action},
        )
    
    def log_veto(self, action: str) -> None:
        """
        Log veto event.
        
        Args:
            action: Action that was vetoed
        """
        self._log_to_phase15(
            event_type="UI_VETO",
            data={"action": action},
        )
    
    def log_cve_view(self, cve_id: str) -> None:
        """
        Log CVE panel view event.
        
        Args:
            cve_id: CVE ID that was viewed
        """
        # No CVE response body - governance constraint
        self._log_to_phase15(
            event_type="UI_CVE_VIEW",
            data={"cve_id": cve_id},
        )
    
    def log_cve_fetch(self, cve_id: str) -> None:
        """
        Log CVE fetch request event.
        
        Args:
            cve_id: CVE ID that was fetched
        """
        # No CVE response body - governance constraint
        # No API key - governance constraint
        self._log_to_phase15(
            event_type="UI_CVE_FETCH",
            data={"cve_id": cve_id},
        )
    
    def log_error(self, error_type: str, message: str) -> None:
        """
        Log UI error event.
        
        Args:
            error_type: Type of error
            message: Error message
        """
        self._log_to_phase15(
            event_type="UI_ERROR",
            data={
                "error_type": error_type,
                "message": message,
            },
        )
    
    def log_loaded(self, component: str) -> None:
        """
        Log UI component loaded event.
        
        Args:
            component: Component that was loaded
        """
        self._log_to_phase15(
            event_type="UI_LOADED",
            data={"component": component},
        )
    
    def log_input(self, element_id: str, input_type: str) -> None:
        """
        Log UI input event (no actual input value for security).
        
        Args:
            element_id: ID of input element
            input_type: Type of input (text, url, etc.)
        """
        # No actual input value logged - security
        self._log_to_phase15(
            event_type="UI_INPUT",
            data={
                "element_id": element_id,
                "input_type": input_type,
            },
        )
