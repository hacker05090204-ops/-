"""
Phase-7 Submission Audit Logger

Maintains an immutable, hash-chained audit trail SEPARATE from Phase-6.
Every submission action is logged with cryptographic integrity.

ARCHITECTURAL CONSTRAINTS:
- Append-only: No updates or deletes
- Hash chain: Each entry contains hash of previous entry
- HARD STOP on failure: AuditLogFailure halts all operations
- SEPARATE from Phase-6: No cross-writes to Phase-6 audit log
"""

from __future__ import annotations
from datetime import datetime
from typing import Callable, Optional
import uuid

from submission_workflow.types import (
    SubmissionAuditEntry,
    SubmissionAction,
    Platform,
)
from submission_workflow.errors import AuditLogFailure


class SubmissionAuditLogger:
    """
    Append-only audit logger with SHA-256 hash chain integrity.
    
    SEPARATE from Phase-6 audit log. Phase-7 maintains its own
    hash-chained audit trail for submission activities.
    
    Each entry contains a hash of the previous entry, creating a
    tamper-evident chain. If any entry is modified, the chain breaks
    and integrity verification fails.
    
    HARD STOP: If a write fails, AuditLogFailure is raised and the
    system must halt. No submissions can be made without audit.
    """
    
    def __init__(
        self,
        write_callback: Optional[Callable[[SubmissionAuditEntry], None]] = None,
        fail_on_write: bool = False,
    ):
        """
        Initialize the submission audit logger.
        
        Args:
            write_callback: Optional callback for persisting entries.
            fail_on_write: If True, simulate write failure (for testing).
        """
        self._entries: list[SubmissionAuditEntry] = []
        self._write_callback = write_callback
        self._fail_on_write = fail_on_write
    
    def log(self, entry: SubmissionAuditEntry) -> SubmissionAuditEntry:
        """
        Append an entry to the audit log with hash chain.
        
        Args:
            entry: The audit entry to log.
            
        Returns:
            The entry with hash chain fields populated.
            
        Raises:
            AuditLogFailure: If the write fails (HARD STOP).
        """
        # Simulate write failure for testing
        if self._fail_on_write:
            raise AuditLogFailure(
                original_error=RuntimeError("Simulated write failure"),
                message="Submission audit log write failed (simulated)",
            )
        
        # Get previous hash
        previous_hash = self._entries[-1].entry_hash if self._entries else None
        
        # Create entry with previous_hash
        entry_with_prev = SubmissionAuditEntry(
            entry_id=entry.entry_id,
            timestamp=entry.timestamp,
            action=entry.action,
            submitter_id=entry.submitter_id,
            request_id=entry.request_id,
            confirmation_id=entry.confirmation_id,
            submission_id=entry.submission_id,
            platform=entry.platform,
            decision_id=entry.decision_id,
            error_type=entry.error_type,
            error_message=entry.error_message,
            previous_hash=previous_hash,
            entry_hash=None,  # Will be computed
        )
        
        # Compute hash
        entry_hash = entry_with_prev.compute_hash()
        
        # Create final entry with hash
        final_entry = SubmissionAuditEntry(
            entry_id=entry_with_prev.entry_id,
            timestamp=entry_with_prev.timestamp,
            action=entry_with_prev.action,
            submitter_id=entry_with_prev.submitter_id,
            request_id=entry_with_prev.request_id,
            confirmation_id=entry_with_prev.confirmation_id,
            submission_id=entry_with_prev.submission_id,
            platform=entry_with_prev.platform,
            decision_id=entry_with_prev.decision_id,
            error_type=entry_with_prev.error_type,
            error_message=entry_with_prev.error_message,
            previous_hash=entry_with_prev.previous_hash,
            entry_hash=entry_hash,
        )
        
        # Persist via callback if provided
        if self._write_callback is not None:
            try:
                self._write_callback(final_entry)
            except Exception as e:
                raise AuditLogFailure(
                    original_error=e,
                    message=f"Submission audit log write callback failed: {e}",
                )
        
        # Append to in-memory log
        self._entries.append(final_entry)
        
        return final_entry
    
    def get_chain(self) -> list[SubmissionAuditEntry]:
        """
        Return the complete audit chain.
        
        Returns:
            List of all audit entries in order.
        """
        return list(self._entries)
    
    def verify_integrity(self) -> bool:
        """
        Verify the hash chain integrity.
        
        Returns:
            True if the chain is valid, False if tampered.
        """
        if not self._entries:
            return True
        
        # First entry should have no previous hash
        if self._entries[0].previous_hash is not None:
            return False
        
        # Verify each entry's hash
        for i, entry in enumerate(self._entries):
            # Verify entry hash matches computed hash
            expected_hash = entry.compute_hash()
            if entry.entry_hash != expected_hash:
                return False
            
            # Verify previous_hash matches previous entry's hash
            if i > 0:
                if entry.previous_hash != self._entries[i - 1].entry_hash:
                    return False
        
        return True
    
    def __len__(self) -> int:
        """Return the number of entries in the log."""
        return len(self._entries)
    
    def find_confirmation_used(self, confirmation_id: str) -> Optional[SubmissionAuditEntry]:
        """
        Find audit entry where a confirmation was consumed.
        
        Used for persistence recovery - if a confirmation_id appears
        in the audit log with CONFIRMATION_CONSUMED action, it has
        been used and cannot be reused.
        
        Args:
            confirmation_id: The confirmation ID to search for.
            
        Returns:
            The audit entry if found, None otherwise.
        """
        for entry in self._entries:
            if (
                entry.confirmation_id == confirmation_id
                and entry.action == SubmissionAction.CONFIRMATION_CONSUMED
            ):
                return entry
        return None
    
    def find_replay_attempts(self, confirmation_id: str) -> list[SubmissionAuditEntry]:
        """
        Find all replay attempts for a confirmation.
        
        Args:
            confirmation_id: The confirmation ID to search for.
            
        Returns:
            List of replay attempt audit entries.
        """
        return [
            entry for entry in self._entries
            if (
                entry.confirmation_id == confirmation_id
                and entry.action == SubmissionAction.CONFIRMATION_REPLAY_BLOCKED
            )
        ]


def create_audit_entry(
    submitter_id: str,
    action: SubmissionAction,
    request_id: Optional[str] = None,
    confirmation_id: Optional[str] = None,
    submission_id: Optional[str] = None,
    platform: Optional[Platform] = None,
    decision_id: Optional[str] = None,
    error_type: Optional[str] = None,
    error_message: Optional[str] = None,
) -> SubmissionAuditEntry:
    """
    Factory function to create a submission audit entry.
    
    Args:
        submitter_id: The submitter ID.
        action: The action being logged.
        request_id: Optional request ID.
        confirmation_id: Optional confirmation ID.
        submission_id: Optional submission ID.
        platform: Optional platform.
        decision_id: Optional decision ID.
        error_type: Optional error type.
        error_message: Optional error message.
        
    Returns:
        A new SubmissionAuditEntry (without hash chain fields).
    """
    return SubmissionAuditEntry(
        entry_id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        action=action,
        submitter_id=submitter_id,
        request_id=request_id,
        confirmation_id=confirmation_id,
        submission_id=submission_id,
        platform=platform,
        decision_id=decision_id,
        error_type=error_type,
        error_message=error_message,
    )
