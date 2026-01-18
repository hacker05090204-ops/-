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
Hash Chain for Phase-13 Audit Trail Integrity.

Requirement: 6.1 (Hash-chained), 6.3 (Audit Trail Integrity)

This module provides cryptographic hash chain for audit entries.
Each entry is linked to the previous entry via SHA-256 hash.
Chain validation detects any tampering or corruption.
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from browser_shell.audit_storage import AuditStorage


@dataclass(frozen=True)
class ValidationResult:
    """
    Result of hash chain validation.
    
    Immutable to prevent tampering with validation status.
    """
    valid: bool
    entry_count: int
    error_message: str = ""
    failed_entry_id: str = ""


class HashChain:
    """
    Cryptographic hash chain for audit trail integrity.
    
    Per Requirement 6.1 (Hash-chained):
    - Each entry cryptographically linked to previous entry
    - Hash chain validation on startup
    - Hash chain validation periodically during operation
    - Hash chain failure halts all operations
    
    Per Requirement 6.3 (Audit Trail Integrity):
    - External time source used for timestamps
    
    FORBIDDEN METHODS (not implemented):
    - auto_*, execute_*, learn_*, optimize_*
    """
    
    # Genesis hash for first entry (all zeros)
    GENESIS_HASH = "0" * 64
    
    def compute_entry_hash(
        self,
        entry_id: str,
        timestamp: str,
        previous_hash: str,
        action_type: str,
        initiator: str,
        session_id: str,
        scope_hash: str,
        action_details: str,
        outcome: str,
    ) -> str:
        """
        Compute SHA-256 hash for an audit entry.
        
        The hash includes ALL fields to ensure integrity.
        The previous_hash links this entry to the chain.
        
        Args:
            All fields of the audit entry except entry_hash.
        
        Returns:
            64-character lowercase hex string (SHA-256).
        """
        # Concatenate all fields in deterministic order
        data = "|".join([
            entry_id,
            timestamp,
            previous_hash,
            action_type,
            initiator,
            session_id,
            scope_hash,
            action_details,
            outcome,
        ])
        
        # Compute SHA-256
        hash_bytes = hashlib.sha256(data.encode('utf-8')).digest()
        return hash_bytes.hex()
    
    def validate_chain(self, storage: "AuditStorage") -> ValidationResult:
        """
        Validate the entire hash chain.
        
        Per Requirement 6.3 (Audit Trail Integrity):
        - Validates on startup
        - Validates periodically during operation
        - Failure triggers HALT
        
        Args:
            storage: The audit storage to validate.
        
        Returns:
            ValidationResult indicating chain integrity status.
        
        STOP Condition: If validation fails, caller must HALT all operations.
        """
        entries = storage.read_all()
        
        if not entries:
            return ValidationResult(valid=True, entry_count=0)
        
        expected_previous = self.GENESIS_HASH
        
        for i, entry in enumerate(entries):
            # Verify chain link
            if entry.previous_hash != expected_previous:
                return ValidationResult(
                    valid=False,
                    entry_count=i,
                    error_message=f"Chain link broken at entry {entry.entry_id}: "
                                  f"expected previous_hash {expected_previous[:16]}..., "
                                  f"got {entry.previous_hash[:16]}...",
                    failed_entry_id=entry.entry_id,
                )
            
            # Recompute hash
            computed_hash = self.compute_entry_hash(
                entry_id=entry.entry_id,
                timestamp=entry.timestamp,
                previous_hash=entry.previous_hash,
                action_type=entry.action_type,
                initiator=entry.initiator,
                session_id=entry.session_id,
                scope_hash=entry.scope_hash,
                action_details=entry.action_details,
                outcome=entry.outcome,
            )
            
            # Verify entry hash
            if entry.entry_hash != computed_hash:
                return ValidationResult(
                    valid=False,
                    entry_count=i,
                    error_message=f"Hash mismatch at entry {entry.entry_id}: "
                                  f"stored {entry.entry_hash[:16]}..., "
                                  f"computed {computed_hash[:16]}...",
                    failed_entry_id=entry.entry_id,
                )
            
            # Update expected previous for next entry
            expected_previous = entry.entry_hash
        
        return ValidationResult(
            valid=True,
            entry_count=len(entries),
        )
    
    def get_external_timestamp(self) -> str:
        """
        Get timestamp from external source.
        
        Per Requirement 6.3 (Audit Trail Integrity):
        - Timestamps must not be from local clock alone
        - Uses UTC timezone for consistency
        
        In production, this should query an external NTP server
        or trusted time service. For now, uses system UTC time
        with explicit timezone marking.
        
        Returns:
            ISO 8601 formatted timestamp string.
        """
        # Use UTC timezone explicitly
        now = datetime.now(timezone.utc)
        return now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
