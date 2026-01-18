"""
Phase-24 Seal: System seal creation.

Seal is ALWAYS human-initiated — NO auto-seal.
"""

import hashlib
import uuid

from .types import SystemSeal


def compute_seal_hash(
    seal_id: str,
    timestamp: str,
    sealed_by: str,
    seal_reason: str,
    archive_hash: str,
) -> str:
    """
    Compute SHA-256 hash of seal record.
    
    Args:
        seal_id: UUID of the seal.
        timestamp: ISO-8601 timestamp.
        sealed_by: Identifier of sealer.
        seal_reason: Reason for seal.
        archive_hash: Hash of archive.
        
    Returns:
        64-character lowercase hex string (SHA-256).
    """
    combined = f"{seal_id}:{timestamp}:{sealed_by}:{seal_reason}:{archive_hash}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def create_seal(
    sealed_by: str,
    seal_reason: str,
    archive_hash: str,
    timestamp: str,
) -> SystemSeal:
    """
    Create a system seal with human confirmation.
    
    This function:
    - Creates seal record
    - Does NOT auto-seal
    - Does NOT schedule seal
    - Always sets human_initiated=True
    - Always sets actor="HUMAN"
    
    Args:
        sealed_by: Free-text identifier of sealer (NOT verified).
        seal_reason: Free-text reason for seal (NOT analyzed).
        archive_hash: SHA-256 of complete archive.
        timestamp: ISO-8601 timestamp.
        
    Returns:
        Immutable SystemSeal.
    """
    seal_id = str(uuid.uuid4())
    
    seal_hash = compute_seal_hash(
        seal_id=seal_id,
        timestamp=timestamp,
        sealed_by=sealed_by,
        seal_reason=seal_reason,
        archive_hash=archive_hash,
    )
    
    return SystemSeal(
        seal_id=seal_id,
        timestamp=timestamp,
        sealed_by=sealed_by,
        seal_reason=seal_reason,  # Stored as-is, NOT analyzed
        archive_hash=archive_hash,
        seal_hash=seal_hash,
        sealed=True,  # Always True for seal records
        human_initiated=True,  # ALWAYS True
        actor="HUMAN",  # ALWAYS "HUMAN"
    )

