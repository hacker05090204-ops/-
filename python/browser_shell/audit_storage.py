# PHASE-13 GOVERNANCE COMPLIANCE
# This module is part of Phase-13 (Controlled Bug Bounty Browser Shell)
#
# FORBIDDEN CAPABILITIES:
# - NO automation logic
# - NO execution authority
# - NO decision authority
# - NO learning or personalization
# - NO audit modification (delete, update, truncate)
# - NO scope expansion
# - NO session extension
# - NO batch approvals
# - NO scheduled actions
# - NO disable mechanism
#
# MANDATORY DECLARATION:
# Phase-13 must not alter execution authority, human control,
# governance friction, audit invariants, or legal accountability.

"""
Append-Only Audit Storage for Phase-13 Browser Shell.

Requirement: 6.1 (Audit Trail Properties)

This module provides APPEND-ONLY storage for audit entries.
NO delete. NO update. NO truncate. NO disable.
All writes are SYNCHRONOUS - action blocked until write confirmed.
"""

import json
import os
from dataclasses import dataclass
from typing import List

from browser_shell.audit_types import AuditEntry


@dataclass(frozen=True)
class AppendResult:
    """
    Result of an append operation.
    
    Immutable to prevent tampering with result status.
    """
    success: bool
    entry_id: str
    error_message: str = ""


class AuditStorage:
    """
    Append-only audit storage.
    
    Per Requirement 6.1 (Audit Trail Properties):
    - NO delete capability
    - NO update capability
    - NO truncate capability
    - Writes are SYNCHRONOUS (action blocked until write confirmed)
    - Storage is SEPARATE from application storage
    - NO mechanism to disable audit logging
    
    FORBIDDEN METHODS (not implemented):
    - delete, remove, erase, clear, purge, wipe
    - update, modify, change, edit, alter, mutate
    - truncate, trim, cut, shorten, limit
    - disable, stop, pause, suspend, skip, bypass
    """
    
    AUDIT_FILENAME = "audit_trail.jsonl"
    
    def __init__(self, storage_path: str) -> None:
        """
        Initialize audit storage with dedicated path.
        
        Args:
            storage_path: Dedicated directory for audit storage.
                          Must be separate from application storage.
        """
        self._storage_path = storage_path
        self._audit_file = os.path.join(storage_path, self.AUDIT_FILENAME)
        
        # Create dedicated audit directory if it doesn't exist
        os.makedirs(storage_path, exist_ok=True)
        
        # Create audit file if it doesn't exist
        if not os.path.exists(self._audit_file):
            with open(self._audit_file, 'w') as f:
                pass  # Create empty file
    
    def append(self, entry: AuditEntry) -> AppendResult:
        """
        Append an audit entry to storage.
        
        This operation is SYNCHRONOUS:
        - Blocks until write is confirmed on disk
        - Uses fsync to ensure durability
        - Returns only after entry is persisted
        
        Args:
            entry: The audit entry to append.
        
        Returns:
            AppendResult indicating success or failure.
        
        STOP Condition: If write fails, caller must HALT operations.
        """
        try:
            # Serialize entry to JSON
            entry_dict = {
                'entry_id': entry.entry_id,
                'timestamp': entry.timestamp,
                'previous_hash': entry.previous_hash,
                'action_type': entry.action_type,
                'initiator': entry.initiator,
                'session_id': entry.session_id,
                'scope_hash': entry.scope_hash,
                'action_details': entry.action_details,
                'outcome': entry.outcome,
                'entry_hash': entry.entry_hash,
            }
            
            json_line = json.dumps(entry_dict) + "\n"
            
            # SYNCHRONOUS write with fsync
            with open(self._audit_file, 'a') as f:
                f.write(json_line)
                f.flush()
                os.fsync(f.fileno())  # Ensure write to disk
            
            return AppendResult(
                success=True,
                entry_id=entry.entry_id,
            )
            
        except Exception as e:
            # Write failure - caller must HALT
            return AppendResult(
                success=False,
                entry_id=entry.entry_id,
                error_message=str(e),
            )
    
    def read_all(self) -> List[AuditEntry]:
        """
        Read all audit entries from storage.
        
        This is a READ-ONLY operation for verification and analysis.
        
        Returns:
            List of all audit entries in chronological order.
        """
        entries = []
        
        if not os.path.exists(self._audit_file):
            return entries
        
        with open(self._audit_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                entry_dict = json.loads(line)
                entry = AuditEntry(
                    entry_id=entry_dict['entry_id'],
                    timestamp=entry_dict['timestamp'],
                    previous_hash=entry_dict['previous_hash'],
                    action_type=entry_dict['action_type'],
                    initiator=entry_dict['initiator'],
                    session_id=entry_dict['session_id'],
                    scope_hash=entry_dict['scope_hash'],
                    action_details=entry_dict['action_details'],
                    outcome=entry_dict['outcome'],
                    entry_hash=entry_dict['entry_hash'],
                )
                entries.append(entry)
        
        return entries
    
    def get_last_entry(self) -> AuditEntry | None:
        """
        Get the last audit entry for hash chain linking.
        
        Returns:
            The last entry, or None if storage is empty.
        """
        entries = self.read_all()
        if entries:
            return entries[-1]
        return None
    
    def count(self) -> int:
        """
        Count total audit entries.
        
        Returns:
            Number of entries in storage.
        """
        return len(self.read_all())
