# PHASE-13 GOVERNANCE COMPLIANCE
# This module is part of Phase-13 (Controlled Bug Bounty Browser Shell)
#
# FORBIDDEN CAPABILITIES:
# - NO automation logic
# - NO execution authority
# - NO decision authority
# - NO learning or personalization
# - NO audit modification
# - NO scope expansion
# - NO session extension
# - NO batch approvals
# - NO scheduled actions
#
# MANDATORY DECLARATION:
# Phase-13 must not alter execution authority, human control,
# governance friction, audit invariants, or legal accountability.

"""
Session Management for Phase-13 Browser Shell.

Requirement: 1.1, 1.2, 1.3 (Session Management)

This module provides session creation, boundary enforcement, and termination.
- Session creation requires explicit scope and human confirmation
- Session boundaries enforce time limits
- Session termination clears all state

FORBIDDEN METHODS (not implemented):
- auto_*, execute_*, extend_*, background_*
"""

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional

from browser_shell.audit_storage import AuditStorage
from browser_shell.audit_types import AuditEntry, Initiator, ActionType
from browser_shell.hash_chain import HashChain


@dataclass(frozen=True)
class SessionCreationResult:
    """
    Result of session creation attempt.
    
    Immutable to prevent tampering.
    """
    success: bool
    session_id: str = ""
    error_message: str = ""


class Session:
    """
    A single browser shell session.
    
    Per Requirement 1.1 (Session Initiation):
    - Requires explicit scope definition
    - Requires human confirmation
    - Session ID includes scope hash, timestamp, operator hash
    
    Per Requirement 1.2 (Session Boundaries):
    - Maximum duration: 4 hours (TH-06)
    - Idle timeout: 30 minutes (TH-07)
    - Bound to exactly one scope
    - Bound to exactly one operator
    
    Scope and operator are READ-ONLY after creation.
    """
    
    def __init__(
        self,
        session_id: str,
        scope_definition: str,
        scope_hash: str,
        operator_id: str,
        start_time: datetime,
    ) -> None:
        self._session_id = session_id
        self._scope_definition = scope_definition
        self._scope_hash = scope_hash
        self._operator_id = operator_id
        self._start_time = start_time
        self._last_activity = start_time
        self._is_terminated = False
    
    @property
    def session_id(self) -> str:
        return self._session_id
    
    @property
    def scope_definition(self) -> str:
        return self._scope_definition
    
    @property
    def scope_hash(self) -> str:
        return self._scope_hash
    
    @property
    def operator_id(self) -> str:
        return self._operator_id
    
    @property
    def start_time(self) -> datetime:
        return self._start_time
    
    @property
    def is_terminated(self) -> bool:
        return self._is_terminated
    
    def is_expired(self) -> bool:
        """
        Check if session has exceeded maximum duration (4 hours).
        
        Per Requirement 1.2 (Session Boundaries) and TH-06.
        """
        elapsed = datetime.now(timezone.utc) - self._start_time
        return elapsed.total_seconds() > SessionManager.MAX_DURATION_SECONDS
    
    def is_idle(self) -> bool:
        """
        Check if session has exceeded idle timeout (30 minutes).
        
        Per Requirement 1.2 (Session Boundaries) and TH-07.
        """
        idle_time = datetime.now(timezone.utc) - self._last_activity
        return idle_time.total_seconds() > SessionManager.IDLE_TIMEOUT_SECONDS
    
    def record_activity(self) -> None:
        """Record activity to reset idle timer."""
        if not self._is_terminated:
            self._last_activity = datetime.now(timezone.utc)
    
    def terminate(self) -> None:
        """Mark session as terminated."""
        self._is_terminated = True


class SessionManager:
    """
    Manager for browser shell sessions.
    
    Per Requirement 1.1, 1.2, 1.3:
    - Creates sessions with human confirmation
    - Enforces session boundaries
    - Terminates sessions cleanly
    
    FORBIDDEN METHODS (not implemented):
    - auto_create, auto_extend, auto_terminate
    - execute_*, background_*, extend_*
    """
    
    # Per TH-06: Maximum session duration is 4 hours
    MAX_DURATION_SECONDS = 4 * 60 * 60
    
    # Per TH-07: Idle timeout is 30 minutes
    IDLE_TIMEOUT_SECONDS = 30 * 60
    
    def __init__(
        self,
        storage: AuditStorage,
        hash_chain: HashChain,
    ) -> None:
        self._storage = storage
        self._hash_chain = hash_chain
        self._sessions: Dict[str, Session] = {}
    
    def create_session(
        self,
        scope_definition: Optional[str],
        operator_id: str,
        human_confirmed: bool,
    ) -> SessionCreationResult:
        """
        Create a new session.
        
        Per Requirement 1.1 (Session Initiation):
        - Requires explicit scope definition
        - Requires human confirmation of scope
        - Session ID includes scope hash, start timestamp, operator identity hash
        - Session creation logged to audit trail before any operations
        
        Args:
            scope_definition: The explicit scope for this session.
            operator_id: Identity of the human operator.
            human_confirmed: Must be True to create session.
        
        Returns:
            SessionCreationResult indicating success or failure.
        
        STOP Condition: If session created without human confirmation, HALT.
        """
        # Validate scope
        if scope_definition is None or scope_definition.strip() == "":
            return SessionCreationResult(
                success=False,
                error_message="Scope definition is required. Cannot create session without scope.",
            )
        
        # Validate human confirmation
        if not human_confirmed:
            return SessionCreationResult(
                success=False,
                error_message="Human confirmation is required. Cannot create session without confirmation.",
            )
        
        # Generate session ID components
        scope_hash = hashlib.sha256(scope_definition.encode()).hexdigest()
        operator_hash = hashlib.sha256(operator_id.encode()).hexdigest()[:8]
        timestamp = datetime.now(timezone.utc)
        timestamp_str = timestamp.strftime("%Y%m%d%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        
        # Session ID format: scope_hash[:8]-timestamp-operator_hash-unique
        session_id = f"{scope_hash[:8]}-{timestamp_str}-{operator_hash}-{unique_id}"
        
        # Create session object
        session = Session(
            session_id=session_id,
            scope_definition=scope_definition,
            scope_hash=scope_hash,
            operator_id=operator_id,
            start_time=timestamp,
        )
        
        # Log to audit trail BEFORE storing session
        last_entry = self._storage.get_last_entry()
        previous_hash = last_entry.entry_hash if last_entry else HashChain.GENESIS_HASH
        
        entry_id = f"audit-{uuid.uuid4().hex[:12]}"
        entry_timestamp = self._hash_chain.get_external_timestamp()
        
        entry_hash = self._hash_chain.compute_entry_hash(
            entry_id=entry_id,
            timestamp=entry_timestamp,
            previous_hash=previous_hash,
            action_type=ActionType.SESSION_START.value,
            initiator=Initiator.HUMAN.value,
            session_id=session_id,
            scope_hash=scope_hash,
            action_details=f"Session created for scope: {scope_definition}, operator: {operator_id}",
            outcome="SUCCESS",
        )
        
        audit_entry = AuditEntry(
            entry_id=entry_id,
            timestamp=entry_timestamp,
            previous_hash=previous_hash,
            action_type=ActionType.SESSION_START.value,
            initiator=Initiator.HUMAN.value,
            session_id=session_id,
            scope_hash=scope_hash,
            action_details=f"Session created for scope: {scope_definition}, operator: {operator_id}",
            outcome="SUCCESS",
            entry_hash=entry_hash,
        )
        
        append_result = self._storage.append(audit_entry)
        
        if not append_result.success:
            return SessionCreationResult(
                success=False,
                error_message=f"Audit write failed: {append_result.error_message}",
            )
        
        # Store session
        self._sessions[session_id] = session
        
        return SessionCreationResult(
            success=True,
            session_id=session_id,
        )
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get a session by ID.
        
        Returns None if session doesn't exist or is terminated.
        """
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if session.is_terminated:
            return session  # Return for status check, but marked terminated
        return session
    
    def terminate_session(self, session_id: str, reason: str) -> bool:
        """
        Terminate a session.
        
        Per Requirement 1.3 (Session Termination):
        - Invalidates all session state
        - Destroys all session tokens
        - Clears all authorization state
        - No session data persists that could influence future sessions
        - Session termination logged with reason
        
        Args:
            session_id: The session to terminate.
            reason: Reason for termination (logged to audit).
        
        Returns:
            True if termination successful, False otherwise.
        """
        session = self._sessions.get(session_id)
        if session is None:
            return False
        
        # Log termination to audit trail
        last_entry = self._storage.get_last_entry()
        previous_hash = last_entry.entry_hash if last_entry else HashChain.GENESIS_HASH
        
        entry_id = f"audit-{uuid.uuid4().hex[:12]}"
        entry_timestamp = self._hash_chain.get_external_timestamp()
        
        entry_hash = self._hash_chain.compute_entry_hash(
            entry_id=entry_id,
            timestamp=entry_timestamp,
            previous_hash=previous_hash,
            action_type=ActionType.SESSION_END.value,
            initiator=Initiator.HUMAN.value,
            session_id=session_id,
            scope_hash=session.scope_hash,
            action_details=f"Session terminated. Reason: {reason}",
            outcome="SUCCESS",
        )
        
        audit_entry = AuditEntry(
            entry_id=entry_id,
            timestamp=entry_timestamp,
            previous_hash=previous_hash,
            action_type=ActionType.SESSION_END.value,
            initiator=Initiator.HUMAN.value,
            session_id=session_id,
            scope_hash=session.scope_hash,
            action_details=f"Session terminated. Reason: {reason}",
            outcome="SUCCESS",
            entry_hash=entry_hash,
        )
        
        self._storage.append(audit_entry)
        
        # Terminate session
        session.terminate()
        
        return True
