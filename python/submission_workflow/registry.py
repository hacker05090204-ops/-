"""
Phase-7 Confirmation Consumption Registry

Records confirmation_id as USED immediately after transmission attempt
(success or failure). Ensures each confirmation can only be used once.

SECURITY INVARIANTS:
- A confirmation_id can only be used once
- Reuse raises TokenAlreadyUsedError
- State survives process restart (in-memory + persisted audit check)
- All replay attempts are logged to audit trail

ARCHITECTURAL CONSTRAINTS:
- Confirmation is marked USED before transmission result is known
- This prevents race conditions where a failure could allow replay
- Registry checks both in-memory cache and audit log for persistence
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional

from submission_workflow.types import (
    SubmissionConfirmation,
    UsedConfirmation,
    SubmissionAction,
)
from submission_workflow.errors import TokenAlreadyUsedError, AuditLogFailure
from submission_workflow.audit import SubmissionAuditLogger, create_audit_entry


class ConfirmationRegistry:
    """
    Registry tracking consumed confirmations to prevent replay attacks.
    
    SECURITY: Each SubmissionConfirmation authorizes exactly ONE network
    request. After the request completes (success or failure), the
    confirmation is invalidated and cannot be reused.
    
    PERSISTENCE: The registry maintains both:
    1. In-memory cache for fast lookups
    2. Audit log integration for persistence across restarts
    
    On startup, the registry can be reconstructed from the audit log
    by scanning for CONFIRMATION_CONSUMED entries.
    """
    
    def __init__(self, audit_logger: SubmissionAuditLogger):
        """
        Initialize the confirmation registry.
        
        Args:
            audit_logger: The submission audit logger for persistence
                         and replay attempt logging.
        """
        self._used: dict[str, UsedConfirmation] = {}
        self._audit_logger = audit_logger
    
    def is_used(self, confirmation_id: str) -> bool:
        """
        Check if a confirmation has been used.
        
        Checks both in-memory cache and audit log for persistence.
        
        Args:
            confirmation_id: The confirmation ID to check.
            
        Returns:
            True if the confirmation has been used, False otherwise.
        """
        # Check in-memory cache first (fast path)
        if confirmation_id in self._used:
            return True
        
        # Check audit log for persistence (slow path, but survives restart)
        audit_entry = self._audit_logger.find_confirmation_used(confirmation_id)
        if audit_entry is not None:
            # Reconstruct in-memory cache from audit log
            self._used[confirmation_id] = UsedConfirmation(
                confirmation_id=confirmation_id,
                request_id=audit_entry.request_id or "",
                used_at=audit_entry.timestamp,
                transmission_success=True,  # Assume success if in audit
            )
            return True
        
        return False
    
    def get_used_confirmation(self, confirmation_id: str) -> Optional[UsedConfirmation]:
        """
        Get the usage record for a confirmation.
        
        Args:
            confirmation_id: The confirmation ID to look up.
            
        Returns:
            The UsedConfirmation record if found, None otherwise.
        """
        # Check in-memory cache first
        if confirmation_id in self._used:
            return self._used[confirmation_id]
        
        # Check audit log for persistence
        audit_entry = self._audit_logger.find_confirmation_used(confirmation_id)
        if audit_entry is not None:
            used = UsedConfirmation(
                confirmation_id=confirmation_id,
                request_id=audit_entry.request_id or "",
                used_at=audit_entry.timestamp,
                transmission_success=True,
            )
            self._used[confirmation_id] = used
            return used
        
        return None
    
    def consume(
        self,
        confirmation: SubmissionConfirmation,
        submitter_id: str,
        transmission_success: bool = True,
        error_message: Optional[str] = None,
    ) -> UsedConfirmation:
        """
        Mark a confirmation as consumed (used).
        
        CRITICAL: This method MUST be called immediately after a
        transmission attempt, regardless of success or failure.
        The confirmation is invalidated either way.
        
        Args:
            confirmation: The confirmation being consumed.
            submitter_id: The submitter ID for audit logging.
            transmission_success: Whether the transmission succeeded.
            error_message: Optional error message if transmission failed.
            
        Returns:
            The UsedConfirmation record.
            
        Raises:
            TokenAlreadyUsedError: If the confirmation was already used.
            AuditLogFailure: If audit logging fails (HARD STOP).
        """
        confirmation_id = confirmation.confirmation_id
        
        # Check if already used (raises if replay attempt)
        self._check_and_block_replay(confirmation_id, submitter_id)
        
        # Create usage record
        used_at = datetime.now()
        used = UsedConfirmation(
            confirmation_id=confirmation_id,
            request_id=confirmation.request_id,
            used_at=used_at,
            transmission_success=transmission_success,
            error_message=error_message,
        )
        
        # Log to audit trail FIRST (for persistence)
        # This ensures the consumption is recorded even if process crashes
        audit_entry = create_audit_entry(
            submitter_id=submitter_id,
            action=SubmissionAction.CONFIRMATION_CONSUMED,
            request_id=confirmation.request_id,
            confirmation_id=confirmation_id,
            error_type="transmission_failed" if not transmission_success else None,
            error_message=error_message,
        )
        self._audit_logger.log(audit_entry)
        
        # Add to in-memory cache
        self._used[confirmation_id] = used
        
        return used
    
    def _check_and_block_replay(
        self,
        confirmation_id: str,
        submitter_id: str,
    ) -> None:
        """
        Check if confirmation is already used and block replay.
        
        If the confirmation has been used, logs the replay attempt
        to the audit trail and raises TokenAlreadyUsedError.
        
        Args:
            confirmation_id: The confirmation ID to check.
            submitter_id: The submitter ID for audit logging.
            
        Raises:
            TokenAlreadyUsedError: If the confirmation was already used.
        """
        used = self.get_used_confirmation(confirmation_id)
        if used is not None:
            # Log replay attempt to audit trail
            audit_entry = create_audit_entry(
                submitter_id=submitter_id,
                action=SubmissionAction.CONFIRMATION_REPLAY_BLOCKED,
                confirmation_id=confirmation_id,
                request_id=used.request_id,
                error_type="TokenAlreadyUsedError",
                error_message=f"Replay attempt blocked: confirmation {confirmation_id} "
                             f"was used at {used.used_at.isoformat()}",
            )
            self._audit_logger.log(audit_entry)
            
            # Raise error
            raise TokenAlreadyUsedError(confirmation_id, used.used_at)
    
    def validate_and_consume(
        self,
        confirmation: SubmissionConfirmation,
        submitter_id: str,
        now: Optional[datetime] = None,
    ) -> UsedConfirmation:
        """
        Validate a confirmation and mark it as consumed in one atomic operation.
        
        This is the primary entry point for consuming confirmations.
        It checks:
        1. Confirmation has not been used (replay protection)
        2. Confirmation has not expired
        
        Then marks the confirmation as consumed.
        
        Args:
            confirmation: The confirmation to validate and consume.
            submitter_id: The submitter ID for audit logging.
            now: Optional current time for expiry check (for testing).
            
        Returns:
            The UsedConfirmation record.
            
        Raises:
            TokenAlreadyUsedError: If the confirmation was already used.
            TokenExpiredError: If the confirmation has expired.
            AuditLogFailure: If audit logging fails (HARD STOP).
        """
        from submission_workflow.errors import TokenExpiredError
        
        # Check if already used (raises if replay attempt)
        self._check_and_block_replay(confirmation.confirmation_id, submitter_id)
        
        # Check expiry
        if confirmation.is_expired(now):
            raise TokenExpiredError(
                confirmation.confirmation_id,
                confirmation.expires_at,
            )
        
        # Consume the confirmation
        return self.consume(
            confirmation=confirmation,
            submitter_id=submitter_id,
            transmission_success=True,  # Assume success, caller updates if needed
        )
    
    def reconstruct_from_audit(self) -> int:
        """
        Reconstruct the in-memory cache from the audit log.
        
        This method should be called on startup to restore state
        from the persisted audit log.
        
        Returns:
            Number of confirmations reconstructed.
        """
        count = 0
        for entry in self._audit_logger.get_chain():
            if (
                entry.action == SubmissionAction.CONFIRMATION_CONSUMED
                and entry.confirmation_id is not None
                and entry.confirmation_id not in self._used
            ):
                self._used[entry.confirmation_id] = UsedConfirmation(
                    confirmation_id=entry.confirmation_id,
                    request_id=entry.request_id or "",
                    used_at=entry.timestamp,
                    transmission_success=entry.error_type is None,
                    error_message=entry.error_message,
                )
                count += 1
        return count
    
    def __len__(self) -> int:
        """Return the number of consumed confirmations."""
        return len(self._used)
    
    def __contains__(self, confirmation_id: str) -> bool:
        """Check if a confirmation_id is in the registry."""
        return self.is_used(confirmation_id)
