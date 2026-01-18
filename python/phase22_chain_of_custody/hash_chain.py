"""
Phase-22 Hash Chain: Hash-chained custody ledger.

This module provides ONLY hash chaining — NO analysis.
"""

import hashlib
import uuid
from typing import Sequence

from .types import CustodyEntry


def compute_entry_hash(
    entry_id: str,
    timestamp: str,
    previous_hash: str,
    evidence_hash: str,
    event_type: str,
) -> str:
    """
    Compute SHA-256 hash of entry content.
    
    Args:
        entry_id: UUID of the entry.
        timestamp: ISO-8601 timestamp.
        previous_hash: Hash of previous entry.
        evidence_hash: Hash of evidence.
        event_type: Type of event.
        
    Returns:
        64-character lowercase hex string (SHA-256).
    """
    combined = f"{entry_id}:{timestamp}:{previous_hash}:{evidence_hash}:{event_type}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def create_chain_entry(
    evidence_hash: str,
    event_type: str,
    previous_hash: str,
    timestamp: str,
) -> CustodyEntry:
    """
    Create a new entry in the custody chain.
    
    This function:
    - Creates hash-linked entry
    - Does NOT analyze content
    - Does NOT judge validity
    - Always sets human_initiated=True
    - Always sets actor="HUMAN"
    
    Args:
        evidence_hash: SHA-256 of evidence being tracked.
        event_type: Type of event ('attestation', 'transfer', 'refusal').
        previous_hash: Hash of previous entry (empty for first).
        timestamp: ISO-8601 timestamp.
        
    Returns:
        Immutable CustodyEntry.
    """
    entry_id = str(uuid.uuid4())
    
    entry_hash = compute_entry_hash(
        entry_id=entry_id,
        timestamp=timestamp,
        previous_hash=previous_hash,
        evidence_hash=evidence_hash,
        event_type=event_type,
    )
    
    return CustodyEntry(
        entry_id=entry_id,
        timestamp=timestamp,
        previous_hash=previous_hash,
        entry_hash=entry_hash,
        evidence_hash=evidence_hash,
        event_type=event_type,
        human_initiated=True,  # ALWAYS True
        actor="HUMAN",  # ALWAYS "HUMAN"
    )


def verify_chain(entries: Sequence[CustodyEntry]) -> bool:
    """
    Verify integrity of custody chain.
    
    This function:
    - Checks hash linkage
    - Returns True/False only (no scoring)
    - Does NOT analyze content
    - Does NOT judge validity
    
    Args:
        entries: Sequence of CustodyEntry in order.
        
    Returns:
        True if chain is valid, False otherwise.
    """
    if not entries:
        return True
    
    # First entry must have empty previous_hash
    if entries[0].previous_hash != "":
        return False
    
    # Verify each entry links to previous
    for i in range(1, len(entries)):
        if entries[i].previous_hash != entries[i - 1].entry_hash:
            return False
    
    # Verify each entry's hash is correct
    for entry in entries:
        expected_hash = compute_entry_hash(
            entry_id=entry.entry_id,
            timestamp=entry.timestamp,
            previous_hash=entry.previous_hash,
            evidence_hash=entry.evidence_hash,
            event_type=entry.event_type,
        )
        if entry.entry_hash != expected_hash:
            return False
    
    return True

