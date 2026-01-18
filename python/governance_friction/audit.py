"""
Phase-10: Governance & Friction Layer - Friction Audit Logger

Append-only, tamper-evident audit log for friction actions.
"""

import hashlib
import time
import uuid
from typing import Dict, List, Any, Optional

from governance_friction.types import FrictionAction, AuditEntry


class FrictionAuditLogger:
    """
    Append-only audit logger for friction actions.
    
    SECURITY: This logger ensures:
    - Entries are append-only (no modifications)
    - Hash chain provides tamper detection
    - All friction actions are recorded
    """
    
    def __init__(self):
        """Initialize the audit logger."""
        self._entries: List[AuditEntry] = []
        self._entries_by_decision: Dict[str, List[AuditEntry]] = {}
        self._last_hash: str = "genesis"
    
    def log_action(
        self,
        action: FrictionAction,
        decision_id: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEntry:
        """
        Log a friction action.
        
        Args:
            action: The friction action being logged
            decision_id: Unique identifier for the decision
            details: Additional details about the action
            
        Returns:
            The created AuditEntry
        """
        # Convert details dict to immutable tuple of tuples
        details_tuple = tuple(sorted((details or {}).items()))
        
        # Create entry
        entry_id = str(uuid.uuid4())
        timestamp = time.monotonic()
        
        # Compute hash
        entry_hash = self._compute_hash(
            entry_id=entry_id,
            decision_id=decision_id,
            action=action,
            timestamp=timestamp,
            details=details_tuple,
            previous_hash=self._last_hash,
        )
        
        entry = AuditEntry(
            entry_id=entry_id,
            decision_id=decision_id,
            action=action,
            timestamp_monotonic=timestamp,
            details=details_tuple,
            previous_hash=self._last_hash,
            entry_hash=entry_hash,
        )
        
        # Append to log (append-only)
        self._entries.append(entry)
        
        # Index by decision
        if decision_id not in self._entries_by_decision:
            self._entries_by_decision[decision_id] = []
        self._entries_by_decision[decision_id].append(entry)
        
        # Update last hash
        self._last_hash = entry_hash
        
        return entry
    
    def get_entries(self, decision_id: str) -> List[AuditEntry]:
        """
        Get all entries for a decision.
        
        Args:
            decision_id: Unique identifier for the decision
            
        Returns:
            List of AuditEntry for the decision
        """
        return list(self._entries_by_decision.get(decision_id, []))
    
    def get_all_entries(self) -> List[AuditEntry]:
        """
        Get all entries in the log.
        
        Returns:
            List of all AuditEntry
        """
        return list(self._entries)
    
    def verify_chain(self) -> bool:
        """
        Verify the integrity of the hash chain.
        
        Returns:
            True if chain is valid, False if tampered
        """
        if not self._entries:
            return True
        
        expected_previous = "genesis"
        
        for entry in self._entries:
            # Verify previous hash matches
            if entry.previous_hash != expected_previous:
                return False
            
            # Verify entry hash is correct
            computed_hash = self._compute_hash(
                entry_id=entry.entry_id,
                decision_id=entry.decision_id,
                action=entry.action,
                timestamp=entry.timestamp_monotonic,
                details=entry.details,
                previous_hash=entry.previous_hash,
            )
            
            if entry.entry_hash != computed_hash:
                return False
            
            expected_previous = entry.entry_hash
        
        return True
    
    def _compute_hash(
        self,
        entry_id: str,
        decision_id: str,
        action: FrictionAction,
        timestamp: float,
        details: tuple,
        previous_hash: str,
    ) -> str:
        """Compute SHA-256 hash for an entry."""
        content = f"{entry_id}|{decision_id}|{action.name}|{timestamp}|{details}|{previous_hash}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def get_entry_count(self) -> int:
        """Get total number of entries."""
        return len(self._entries)
    
    def get_decision_count(self) -> int:
        """Get number of unique decisions."""
        return len(self._entries_by_decision)
