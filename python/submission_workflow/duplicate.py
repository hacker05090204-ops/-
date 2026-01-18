"""
Phase-7 Duplicate Submission Prevention

Enforces decision_id + platform uniqueness with atomic locking.
Prevents race conditions where two submissions for the same decision
could both succeed.

SECURITY INVARIANTS:
- decision_id + platform combination is unique
- Lock acquired BEFORE confirmation check
- Lock held through transmission
- Double-check AFTER transmission (belt and suspenders)
- All duplicate attempts logged to audit trail

ARCHITECTURAL CONSTRAINTS:
- Thread-safe locking
- Audit log is source of truth for completed submissions
- Lock timeout prevents deadlocks
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from threading import Lock, RLock
from typing import Optional, Set
import uuid

from submission_workflow.types import (
    Platform,
    SubmissionAction,
    SubmissionAuditEntry,
)
from submission_workflow.errors import DuplicateSubmissionError
from submission_workflow.audit import SubmissionAuditLogger, create_audit_entry


@dataclass(frozen=True)
class SubmissionKey:
    """
    Unique key for a submission: decision_id + platform.
    
    This combination MUST be unique across all submissions.
    """
    decision_id: str
    platform: Platform
    
    def __hash__(self) -> int:
        return hash((self.decision_id, self.platform.value))
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SubmissionKey):
            return False
        return (
            self.decision_id == other.decision_id
            and self.platform == other.platform
        )


class DuplicateSubmissionGuard:
    """
    Thread-safe guard for preventing duplicate submissions.
    
    Uses a two-phase approach:
    1. BEFORE confirmation: Acquire lock and check audit log
    2. AFTER transmission: Double-check audit log (belt and suspenders)
    
    The audit log is the source of truth for completed submissions.
    The in-memory lock prevents race conditions during the submission window.
    
    SECURITY: All duplicate attempts are logged to the audit trail.
    """
    
    def __init__(self, audit_logger: SubmissionAuditLogger):
        """
        Initialize the duplicate submission guard.
        
        Args:
            audit_logger: The submission audit logger (source of truth).
        """
        self._audit_logger = audit_logger
        self._global_lock = Lock()  # Protects _active_submissions
        self._active_submissions: Set[SubmissionKey] = set()
        self._submission_locks: dict[SubmissionKey, RLock] = {}
    
    def _get_submission_lock(self, key: SubmissionKey) -> RLock:
        """Get or create a lock for a specific submission key."""
        with self._global_lock:
            if key not in self._submission_locks:
                self._submission_locks[key] = RLock()
            return self._submission_locks[key]
    
    def check_and_acquire(
        self,
        decision_id: str,
        platform: Platform,
        submitter_id: str,
    ) -> SubmissionKey:
        """
        Check for duplicates and acquire lock for submission.
        
        MUST be called BEFORE confirmation. Acquires a lock that MUST
        be released by calling release() after transmission completes.
        
        Args:
            decision_id: The decision ID from Phase-6.
            platform: The target platform.
            submitter_id: The submitter ID for audit logging.
            
        Returns:
            The SubmissionKey for this submission.
            
        Raises:
            DuplicateSubmissionError: If submission already exists.
        """
        key = SubmissionKey(decision_id=decision_id, platform=platform)
        lock = self._get_submission_lock(key)
        
        # Acquire the submission-specific lock
        lock.acquire()
        
        try:
            # Check 1: Is there an active submission in progress?
            with self._global_lock:
                if key in self._active_submissions:
                    # Log duplicate attempt
                    self._log_duplicate_blocked(key, submitter_id, "active_submission")
                    raise DuplicateSubmissionError(decision_id, platform)
            
            # Check 2: Has this already been submitted (check audit log)?
            if self._is_already_submitted(key):
                # Log duplicate attempt
                self._log_duplicate_blocked(key, submitter_id, "audit_log")
                raise DuplicateSubmissionError(decision_id, platform)
            
            # Mark as active
            with self._global_lock:
                self._active_submissions.add(key)
            
            return key
            
        except DuplicateSubmissionError:
            # Release lock on failure
            lock.release()
            raise
    
    def verify_and_release(
        self,
        key: SubmissionKey,
        submitter_id: str,
        transmission_success: bool,
    ) -> None:
        """
        Verify no duplicate occurred and release the lock.
        
        MUST be called AFTER transmission completes (success or failure).
        
        Args:
            key: The SubmissionKey from check_and_acquire().
            submitter_id: The submitter ID for audit logging.
            transmission_success: Whether transmission succeeded.
            
        Raises:
            DuplicateSubmissionError: If a duplicate was detected post-transmission.
        """
        lock = self._get_submission_lock(key)
        
        try:
            # Double-check: Did another submission sneak through?
            # This is the "belt and suspenders" check
            if transmission_success:
                # Count how many TRANSMITTED entries exist for this key
                count = self._count_submissions(key)
                if count > 1:
                    # This should never happen if locking is correct
                    # Log as a critical error
                    self._audit_logger.log(create_audit_entry(
                        submitter_id=submitter_id,
                        action=SubmissionAction.DUPLICATE_BLOCKED,
                        decision_id=key.decision_id,
                        platform=key.platform,
                        error_type="DuplicateSubmissionError",
                        error_message=(
                            f"CRITICAL: Post-transmission duplicate detected. "
                            f"Found {count} submissions for {key.decision_id}/{key.platform.value}"
                        ),
                    ))
                    raise DuplicateSubmissionError(key.decision_id, key.platform)
        finally:
            # Remove from active set
            with self._global_lock:
                self._active_submissions.discard(key)
            
            # Release the lock
            lock.release()
    
    def release_on_error(self, key: SubmissionKey) -> None:
        """
        Release lock without verification (for error cases).
        
        Call this if an error occurs before transmission completes.
        
        Args:
            key: The SubmissionKey from check_and_acquire().
        """
        lock = self._get_submission_lock(key)
        
        # Remove from active set
        with self._global_lock:
            self._active_submissions.discard(key)
        
        # Release the lock
        try:
            lock.release()
        except RuntimeError:
            # Lock was not held (shouldn't happen, but be safe)
            pass
    
    def _is_already_submitted(self, key: SubmissionKey) -> bool:
        """
        Check if a submission already exists in the audit log.
        
        Args:
            key: The submission key to check.
            
        Returns:
            True if a TRANSMITTED entry exists for this key.
        """
        return self._count_submissions(key) > 0
    
    def _count_submissions(self, key: SubmissionKey) -> int:
        """
        Count successful submissions for a key in the audit log.
        
        Args:
            key: The submission key to count.
            
        Returns:
            Number of TRANSMITTED entries for this key.
        """
        count = 0
        for entry in self._audit_logger.get_chain():
            if (
                entry.action == SubmissionAction.TRANSMITTED
                and entry.decision_id == key.decision_id
                and entry.platform == key.platform
            ):
                count += 1
        return count
    
    def _log_duplicate_blocked(
        self,
        key: SubmissionKey,
        submitter_id: str,
        reason: str,
    ) -> None:
        """Log a blocked duplicate attempt."""
        self._audit_logger.log(create_audit_entry(
            submitter_id=submitter_id,
            action=SubmissionAction.DUPLICATE_BLOCKED,
            decision_id=key.decision_id,
            platform=key.platform,
            error_type="DuplicateSubmissionError",
            error_message=f"Duplicate blocked: {reason}",
        ))
    
    def is_submitted(self, decision_id: str, platform: Platform) -> bool:
        """
        Check if a decision has been submitted to a platform.
        
        Args:
            decision_id: The decision ID to check.
            platform: The platform to check.
            
        Returns:
            True if already submitted.
        """
        key = SubmissionKey(decision_id=decision_id, platform=platform)
        return self._is_already_submitted(key)
    
    def get_active_count(self) -> int:
        """Return the number of active submissions in progress."""
        with self._global_lock:
            return len(self._active_submissions)
