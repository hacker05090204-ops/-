"""
Phase-6 Session Management

Handles authentication and session lifecycle. Session state is derived
from audit events, not stored directly.

ARCHITECTURAL CONSTRAINTS:
- Sessions are immutable (frozen dataclass)
- Session lifecycle derived from audit log
- No auto-authentication or auto-session creation
"""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional
import uuid

from decision_workflow.types import Credentials, ReviewSession, Role, AuditEntry
from decision_workflow.errors import AuthenticationError, SessionExpiredError
from decision_workflow.audit import AuditLogger, create_audit_entry


class SessionManager:
    """
    Manages authentication and session lifecycle.
    
    Session lifecycle is derived from audit events:
    - SESSION_START: Session created
    - SESSION_END: Session ended
    - Session is active if no SESSION_END exists
    
    This ensures session state cannot be corrupted independently of audit log.
    """
    
    def __init__(
        self,
        audit_logger: AuditLogger,
        session_timeout: timedelta = timedelta(hours=8),
        valid_users: Optional[dict[str, Role]] = None,
    ):
        """
        Initialize session manager.
        
        Args:
            audit_logger: The audit logger for recording session events.
            session_timeout: Session timeout duration (default 8 hours).
            valid_users: Dict of valid user_id -> role mappings.
                        SECURITY: If None, authentication FAILS CLOSED (denies all).
                        This is a security-critical change from previous behavior.
        """
        self._audit_logger = audit_logger
        self._session_timeout = session_timeout
        # SECURITY FIX: Fail closed if no users configured
        # Previous behavior (valid_users=None accepts all) was a security risk
        self._valid_users = valid_users if valid_users is not None else {}
        self._active_sessions: dict[str, ReviewSession] = {}
    
    def authenticate(self, credentials: Credentials) -> ReviewSession:
        """
        Authenticate user and create a new session.
        
        Args:
            credentials: The user's credentials.
            
        Returns:
            A new ReviewSession.
            
        Raises:
            AuthenticationError: If authentication fails.
        """
        # Validate credentials
        # SECURITY FIX: Always validate - empty dict means deny all (fail closed)
        if credentials.user_id not in self._valid_users:
            raise AuthenticationError(f"Unknown user: {credentials.user_id}")
        if self._valid_users[credentials.user_id] != credentials.role:
            raise AuthenticationError(
                f"Role mismatch for user {credentials.user_id}: "
                f"expected {self._valid_users[credentials.user_id].value}, "
                f"got {credentials.role.value}"
            )
        
        # Create session
        session = ReviewSession(
            session_id=str(uuid.uuid4()),
            reviewer_id=credentials.user_id,
            role=credentials.role,
            start_time=datetime.now(),
        )
        
        # Log session start
        entry = create_audit_entry(
            session_id=session.session_id,
            reviewer_id=session.reviewer_id,
            role=session.role,
            action="SESSION_START",
        )
        self._audit_logger.log(entry)
        
        # Track active session
        self._active_sessions[session.session_id] = session
        
        return session
    
    def validate_session(self, session: ReviewSession) -> bool:
        """
        Check if a session is valid and not expired.
        
        Args:
            session: The session to validate.
            
        Returns:
            True if the session is valid, False otherwise.
        """
        # Check if session exists
        if session.session_id not in self._active_sessions:
            return False
        
        # Check if session has ended (via audit log)
        session_entries = self._audit_logger.get_entries_for_session(session.session_id)
        for entry in session_entries:
            if entry.action == "SESSION_END":
                return False
        
        # Check if session has expired
        elapsed = datetime.now() - session.start_time
        if elapsed > self._session_timeout:
            return False
        
        return True
    
    def require_valid_session(self, session: ReviewSession) -> None:
        """
        Require a valid session, raising if invalid or expired.
        
        Args:
            session: The session to validate.
            
        Raises:
            SessionExpiredError: If the session is invalid or expired.
        """
        if not self.validate_session(session):
            raise SessionExpiredError(session.session_id)
    
    def end_session(self, session: ReviewSession) -> None:
        """
        End a session.
        
        Args:
            session: The session to end.
        """
        if session.session_id not in self._active_sessions:
            return
        
        # Count decisions made
        decisions_count = self._audit_logger.count_decisions_for_session(session.session_id)
        
        # Log session end
        entry = create_audit_entry(
            session_id=session.session_id,
            reviewer_id=session.reviewer_id,
            role=session.role,
            action="SESSION_END",
        )
        self._audit_logger.log(entry)
        
        # Remove from active sessions
        del self._active_sessions[session.session_id]
    
    def get_session_decisions_count(self, session: ReviewSession) -> int:
        """
        Get the number of decisions made in a session.
        
        This is derived from the audit log, not stored.
        
        Args:
            session: The session to count for.
            
        Returns:
            Number of decisions made.
        """
        return self._audit_logger.count_decisions_for_session(session.session_id)
    
    def is_session_ended(self, session: ReviewSession) -> bool:
        """
        Check if a session has ended (via audit log).
        
        Args:
            session: The session to check.
            
        Returns:
            True if the session has ended, False otherwise.
        """
        session_entries = self._audit_logger.get_entries_for_session(session.session_id)
        return any(entry.action == "SESSION_END" for entry in session_entries)
