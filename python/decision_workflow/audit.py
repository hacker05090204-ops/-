"""
Phase-6 Audit Logger

Maintains an immutable, hash-chained audit trail. Every decision, permission
denial, and significant action is logged with cryptographic integrity.

ARCHITECTURAL CONSTRAINTS:
- Append-only: No updates or deletes
- Hash chain: Each entry contains hash of previous entry
- HARD STOP on failure: AuditLogFailure halts all operations
"""

from __future__ import annotations
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Callable, Optional
import uuid

from decision_workflow.types import AuditEntry, Role, DecisionType, Severity
from decision_workflow.errors import AuditLogFailure


class AuditLogger:
    """
    Append-only audit logger with SHA-256 hash chain integrity.
    
    Each entry contains a hash of the previous entry, creating a
    tamper-evident chain. If any entry is modified, the chain breaks
    and integrity verification fails.
    
    HARD STOP: If a write fails, AuditLogFailure is raised and the
    system must halt. No decisions can be recorded without audit.
    """
    
    def __init__(
        self,
        write_callback: Optional[Callable[[AuditEntry], None]] = None,
        fail_on_write: bool = False,
    ):
        """
        Initialize the audit logger.
        
        Args:
            write_callback: Optional callback for persisting entries.
            fail_on_write: If True, simulate write failure (for testing).
        """
        self._entries: list[AuditEntry] = []
        self._write_callback = write_callback
        self._fail_on_write = fail_on_write
    
    def log(self, entry: AuditEntry) -> AuditEntry:
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
                message="Audit log write failed (simulated)",
            )
        
        # Get previous hash
        previous_hash = self._entries[-1].entry_hash if self._entries else None
        
        # Create entry with previous_hash
        entry_with_prev = AuditEntry(
            entry_id=entry.entry_id,
            timestamp=entry.timestamp,
            session_id=entry.session_id,
            reviewer_id=entry.reviewer_id,
            role=entry.role,
            action=entry.action,
            finding_id=entry.finding_id,
            decision_id=entry.decision_id,
            decision_type=entry.decision_type,
            severity=entry.severity,
            rationale=entry.rationale,
            error_type=entry.error_type,
            error_message=entry.error_message,
            previous_hash=previous_hash,
            entry_hash=None,  # Will be computed
        )
        
        # Compute hash
        entry_hash = entry_with_prev.compute_hash()
        
        # Create final entry with hash
        final_entry = AuditEntry(
            entry_id=entry_with_prev.entry_id,
            timestamp=entry_with_prev.timestamp,
            session_id=entry_with_prev.session_id,
            reviewer_id=entry_with_prev.reviewer_id,
            role=entry_with_prev.role,
            action=entry_with_prev.action,
            finding_id=entry_with_prev.finding_id,
            decision_id=entry_with_prev.decision_id,
            decision_type=entry_with_prev.decision_type,
            severity=entry_with_prev.severity,
            rationale=entry_with_prev.rationale,
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
                    message=f"Audit log write callback failed: {e}",
                )
        
        # Append to in-memory log
        self._entries.append(final_entry)
        
        return final_entry
    
    def get_chain(self) -> list[AuditEntry]:
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
    
    def get_entries_for_session(self, session_id: str) -> list[AuditEntry]:
        """
        Get all entries for a specific session.
        
        Args:
            session_id: The session ID to filter by.
            
        Returns:
            List of entries for the session.
        """
        return [e for e in self._entries if e.session_id == session_id]
    
    def get_entries_for_finding(self, finding_id: str) -> list[AuditEntry]:
        """
        Get all entries for a specific finding.
        
        Args:
            finding_id: The finding ID to filter by.
            
        Returns:
            List of entries for the finding.
        """
        return [e for e in self._entries if e.finding_id == finding_id]
    
    def count_decisions_for_session(self, session_id: str) -> int:
        """
        Count the number of decisions made in a session.
        
        Args:
            session_id: The session ID to count for.
            
        Returns:
            Number of decision entries.
        """
        return sum(
            1 for e in self._entries
            if e.session_id == session_id and e.action == "DECISION"
        )


def create_audit_entry(
    session_id: str,
    reviewer_id: str,
    role: Role,
    action: str,
    finding_id: Optional[str] = None,
    decision_id: Optional[str] = None,
    decision_type: Optional[DecisionType] = None,
    severity: Optional[Severity] = None,
    rationale: Optional[str] = None,
    error_type: Optional[str] = None,
    error_message: Optional[str] = None,
) -> AuditEntry:
    """
    Factory function to create an audit entry.
    
    Args:
        session_id: The session ID.
        reviewer_id: The reviewer ID.
        role: The reviewer's role.
        action: The action being logged.
        finding_id: Optional finding ID.
        decision_id: Optional decision ID.
        decision_type: Optional decision type.
        severity: Optional severity.
        rationale: Optional rationale.
        error_type: Optional error type.
        error_message: Optional error message.
        
    Returns:
        A new AuditEntry (without hash chain fields).
    """
    return AuditEntry(
        entry_id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        session_id=session_id,
        reviewer_id=reviewer_id,
        role=role,
        action=action,
        finding_id=finding_id,
        decision_id=decision_id,
        decision_type=decision_type,
        severity=severity,
        rationale=rationale,
        error_type=error_type,
        error_message=error_message,
    )
