# PHASE-12 GOVERNANCE COMPLIANCE
# This module is part of Phase-12 (Runtime Orchestration Implementation)
#
# FORBIDDEN CAPABILITIES:
# - NO execution logic
# - NO decision logic
# - NO submission logic
# - NO network access
# - NO browser automation
# - NO friction wiring or execution
# - NO auto-approval
# - NO frozen phase modification
#
# MANDATORY DECLARATION:
# Phase-12 implements orchestration without altering execution,
# human authority, governance friction, or audit invariants.

"""
Phase-12 Audit Layer

Track 2 - TASK-2.1, TASK-2.2: Implement Audit Log (Append-Only)

This module implements:
- create_audit_entry(): Create new audit entries
- compute_entry_hash(): Compute deterministic hash for entries
- verify_hash_chain(): Verify hash chain integrity
- get_chain_integrity_status(): Get detailed chain status

CONSTRAINTS:
- Append-only (no delete, no update)
- Hash chain must be strictly linear
- No cross-phase writes
- No recovery logic
- Deterministic behavior only

NO EXECUTION LOGIC - NO DECISION LOGIC
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from .errors import AuditIntegrityError
from .types import OrchestrationAuditEntry, OrchestrationEventType


# =============================================================================
# CONSTANTS
# =============================================================================

# Genesis hash for the first entry in a chain
GENESIS_HASH = "0" * 64


# =============================================================================
# TASK-2.1: Audit Entry Creation
# =============================================================================

def compute_entry_hash(
    entry_id: str,
    timestamp: datetime,
    event_type: OrchestrationEventType,
    workflow_id: str,
    details: Dict[str, Any],
    previous_hash: str
) -> str:
    """
    Compute deterministic hash for an audit entry.
    
    The hash is computed from all entry fields except entry_hash itself.
    This ensures hash chain integrity can be verified.
    
    Args:
        entry_id: Unique identifier for the entry
        timestamp: Entry timestamp
        event_type: Type of orchestration event
        workflow_id: Associated workflow ID
        details: Event details dictionary
        previous_hash: Hash of the previous entry in the chain
    
    Returns:
        SHA-256 hash as hexadecimal string
    
    NO EXECUTION LOGIC - NO DECISION LOGIC
    """
    # Create deterministic representation
    # Sort keys for consistent ordering
    hash_input = {
        "entry_id": entry_id,
        "timestamp": timestamp.isoformat(),
        "event_type": event_type.value,
        "workflow_id": workflow_id,
        "details": json.dumps(details, sort_keys=True),
        "previous_hash": previous_hash
    }
    
    # Serialize deterministically
    serialized = json.dumps(hash_input, sort_keys=True)
    
    # Compute SHA-256 hash
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def create_audit_entry(
    event_type: OrchestrationEventType,
    workflow_id: str,
    details: Dict[str, Any],
    previous_hash: str
) -> OrchestrationAuditEntry:
    """
    Create a new audit entry with computed hash.
    
    This function creates an immutable audit entry with:
    - Unique entry_id (UUID)
    - Current timestamp
    - Computed entry_hash based on all fields
    - Link to previous entry via previous_hash
    
    Args:
        event_type: Type of orchestration event
        workflow_id: Associated workflow ID
        details: Event details dictionary
        previous_hash: Hash of the previous entry (use GENESIS_HASH for first entry)
    
    Returns:
        Immutable OrchestrationAuditEntry
    
    NO EXECUTION LOGIC - NO DECISION LOGIC
    """
    entry_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc)
    
    # Compute hash for this entry
    entry_hash = compute_entry_hash(
        entry_id=entry_id,
        timestamp=timestamp,
        event_type=event_type,
        workflow_id=workflow_id,
        details=details,
        previous_hash=previous_hash
    )
    
    # Create immutable entry
    return OrchestrationAuditEntry(
        entry_id=entry_id,
        timestamp=timestamp,
        event_type=event_type,
        workflow_id=workflow_id,
        details=details,
        previous_hash=previous_hash,
        entry_hash=entry_hash,
        human_confirmation_required=True,  # ALWAYS True - INV-5.1
        no_auto_action=True  # ALWAYS True - INV-5.1
    )


# =============================================================================
# TASK-2.2: Hash Chain Verification
# =============================================================================

def verify_hash_chain(entries: List[OrchestrationAuditEntry]) -> bool:
    """
    Verify hash chain integrity for a sequence of audit entries.
    
    Verification checks:
    1. Each entry's entry_hash matches recomputed hash
    2. Each entry's previous_hash matches prior entry's entry_hash
    3. First entry's previous_hash is GENESIS_HASH (if chain starts from genesis)
    
    Args:
        entries: List of audit entries in chronological order
    
    Returns:
        True if chain is valid, False otherwise
    
    Raises:
        AuditIntegrityError: If chain integrity is compromised
    
    NO EXECUTION LOGIC - NO DECISION LOGIC
    """
    if not entries:
        return True  # Empty chain is valid
    
    for i, entry in enumerate(entries):
        # Recompute hash for this entry
        expected_hash = compute_entry_hash(
            entry_id=entry.entry_id,
            timestamp=entry.timestamp,
            event_type=entry.event_type,
            workflow_id=entry.workflow_id,
            details=entry.details,
            previous_hash=entry.previous_hash
        )
        
        # Verify entry_hash matches
        if entry.entry_hash != expected_hash:
            raise AuditIntegrityError(
                f"Entry {entry.entry_id} hash mismatch: "
                f"stored={entry.entry_hash}, computed={expected_hash}"
            )
        
        # Verify chain linkage (skip first entry)
        if i > 0:
            previous_entry = entries[i - 1]
            if entry.previous_hash != previous_entry.entry_hash:
                raise AuditIntegrityError(
                    f"Chain broken at entry {entry.entry_id}: "
                    f"previous_hash={entry.previous_hash}, "
                    f"expected={previous_entry.entry_hash}"
                )
    
    return True


def get_chain_integrity_status(
    entries: List[OrchestrationAuditEntry]
) -> Dict[str, Any]:
    """
    Get detailed hash chain integrity status.
    
    Returns comprehensive status including:
    - is_valid: Overall chain validity
    - entry_count: Number of entries in chain
    - first_entry_id: ID of first entry (if any)
    - last_entry_id: ID of last entry (if any)
    - error: Error message if chain is invalid
    
    Args:
        entries: List of audit entries in chronological order
    
    Returns:
        Dictionary with chain integrity status
    
    NO EXECUTION LOGIC - NO DECISION LOGIC
    """
    status: Dict[str, Any] = {
        "is_valid": False,
        "entry_count": len(entries),
        "first_entry_id": None,
        "last_entry_id": None,
        "error": None
    }
    
    if not entries:
        status["is_valid"] = True
        return status
    
    status["first_entry_id"] = entries[0].entry_id
    status["last_entry_id"] = entries[-1].entry_id
    
    try:
        verify_hash_chain(entries)
        status["is_valid"] = True
    except AuditIntegrityError as e:
        status["error"] = str(e)
    
    return status
