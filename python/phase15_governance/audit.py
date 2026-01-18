"""
Phase-15 Audit Module

Append-only audit logging with hash chain.
This module ONLY logs events - no decisions, no scoring.

MANDATORY DECLARATION:
"Phase-15 may ONLY implement enforcement, validation, logging, and blocking."
"""

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from phase15_governance.errors import IntegrityError


# In-memory storage (append-only)
_audit_entries: list[dict[str, Any]] = []
_genesis_hash = "GENESIS_PHASE15_AUDIT_CHAIN"


def _reset_for_testing() -> None:
    """Reset audit state for testing only."""
    global _audit_entries
    _audit_entries = []


def _compute_hash(entry: dict[str, Any]) -> str:
    """Compute hash for an entry."""
    content = f"{entry['entry_id']}:{entry['event_type']}:{entry['timestamp']}:{entry['attribution']}"
    return hashlib.sha256(content.encode()).hexdigest()


def log_event(
    event_type: Optional[str],
    data: dict[str, Any],
    attribution: Optional[str] = None,
) -> str:
    """
    Log an event to the audit trail.
    
    Args:
        event_type: Type of event (required)
        data: Event data
        attribution: HUMAN or SYSTEM (required)
    
    Returns:
        Entry ID
    
    Raises:
        ValueError: If event_type or attribution is invalid
    """
    if event_type is None:
        raise ValueError("event_type is required")
    
    if attribution is None:
        raise ValueError("attribution is required")
    
    if attribution not in ("HUMAN", "SYSTEM"):
        raise ValueError("attribution must be HUMAN or SYSTEM")

    entry_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Get previous hash
    if len(_audit_entries) == 0:
        previous_hash = _genesis_hash
    else:
        previous_hash = _audit_entries[-1]["hash"]
    
    entry = {
        "entry_id": entry_id,
        "event_type": event_type,
        "data": data,
        "attribution": attribution,
        "timestamp": timestamp,
        "previous_hash": previous_hash,
    }
    
    entry["hash"] = _compute_hash(entry)
    _audit_entries.append(entry)
    
    return entry_id


def get_entry(entry_id: str) -> Optional[dict[str, Any]]:
    """Get an entry by ID."""
    for entry in _audit_entries:
        if entry["entry_id"] == entry_id:
            return entry.copy()
    return None


def get_last_entry() -> Optional[dict[str, Any]]:
    """Get the most recent entry."""
    if len(_audit_entries) == 0:
        return None
    return _audit_entries[-1].copy()


def validate_chain() -> bool:
    """
    Validate the hash chain integrity.
    
    Returns:
        True if chain is valid
    
    Raises:
        IntegrityError: If chain is broken
    """
    if len(_audit_entries) == 0:
        return True
    
    # Check first entry links to genesis
    if _audit_entries[0]["previous_hash"] != _genesis_hash:
        raise IntegrityError("First entry does not link to genesis")
    
    # Check each entry links to previous
    for i in range(1, len(_audit_entries)):
        if _audit_entries[i]["previous_hash"] != _audit_entries[i - 1]["hash"]:
            raise IntegrityError(f"Chain broken at entry {i}")
    
    return True
