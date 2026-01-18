"""
Phase-19 Submission Logger

GOVERNANCE CONSTRAINTS:
- All actions logged with attribution="HUMAN"
- No system attribution
- No AI attribution
- Visible audit trail

This module logs all submission-related actions.
All logs MUST have HUMAN attribution.
"""

from typing import List
from datetime import datetime

from .types import SubmissionLog, SubmissionAction


class SubmissionLogger:
    """
    Logger for submission actions.
    
    GOVERNANCE:
    - All logs have HUMAN attribution
    - No system or AI attribution allowed
    - Complete audit trail
    """
    
    def __init__(self):
        """Initialize logger."""
        self._logs: List[SubmissionLog] = []
    
    def log_action(
        self,
        action: SubmissionAction,
        details: str = "",
    ) -> SubmissionLog:
        """
        Log a submission action.
        
        Args:
            action: The action being logged
            details: Additional details
            
        Returns:
            The created log entry
            
        Note:
            Attribution is ALWAYS "HUMAN".
            This cannot be overridden.
        """
        # GOVERNANCE: Attribution is ALWAYS "HUMAN"
        # This is enforced by the SubmissionLog dataclass
        log = SubmissionLog(
            timestamp=datetime.now(),
            action=action,
            attribution="HUMAN",  # ALWAYS HUMAN
            details=details,
        )
        
        self._logs.append(log)
        return log
    
    def get_logs(self) -> List[SubmissionLog]:
        """
        Get all logs.
        
        Returns:
            Copy of all log entries
        """
        return list(self._logs)
    
    def get_logs_by_action(
        self,
        action: SubmissionAction,
    ) -> List[SubmissionLog]:
        """
        Get logs filtered by action type.
        
        Args:
            action: Action type to filter by
            
        Returns:
            Logs matching the action type
        """
        return [log for log in self._logs if log.action == action]
    
    def get_log_count(self) -> int:
        """Get total log count."""
        return len(self._logs)
    
    def clear_logs(self) -> None:
        """
        Clear all logs.
        
        Note: This is for testing purposes only.
        In production, logs should be preserved.
        """
        self._logs.clear()
