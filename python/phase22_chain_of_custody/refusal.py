"""
Phase-22 Refusal: Refusal to attest handling.

Refusal is ALWAYS allowed. Reason is NOT analyzed.
"""

import hashlib
import uuid

from .types import Refusal


def compute_refusal_hash(
    refusal_id: str,
    timestamp: str,
    attestor_id: str,
    evidence_hash: str,
    reason: str,
) -> str:
    """
    Compute SHA-256 hash of refusal content.
    
    Args:
        refusal_id: UUID of the refusal.
        timestamp: ISO-8601 timestamp.
        attestor_id: Identifier of person refusing.
        evidence_hash: Hash of evidence.
        reason: Reason for refusal.
        
    Returns:
        64-character lowercase hex string (SHA-256).
    """
    combined = f"{refusal_id}:{timestamp}:{attestor_id}:{evidence_hash}:{reason}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def record_refusal(
    evidence_hash: str,
    attestor_id: str,
    reason: str,
    timestamp: str,
) -> Refusal:
    """
    Record a refusal to attest.
    
    Refusal is ALWAYS allowed.
    Reason is NOT analyzed.
    
    This function:
    - Records human refusal
    - Does NOT analyze reason
    - Does NOT block operation
    - Always sets human_initiated=True
    - Always sets actor="HUMAN"
    
    Args:
        evidence_hash: SHA-256 of evidence being refused.
        attestor_id: Free-text identifier of person refusing (NOT verified).
        reason: Free-text reason for refusal (NOT analyzed).
        timestamp: ISO-8601 timestamp.
        
    Returns:
        Immutable Refusal.
    """
    refusal_id = str(uuid.uuid4())
    
    refusal_hash = compute_refusal_hash(
        refusal_id=refusal_id,
        timestamp=timestamp,
        attestor_id=attestor_id,
        evidence_hash=evidence_hash,
        reason=reason,
    )
    
    return Refusal(
        refusal_id=refusal_id,
        timestamp=timestamp,
        attestor_id=attestor_id,
        evidence_hash=evidence_hash,
        reason=reason,  # Stored as-is, NOT analyzed
        refused=True,  # Always True for refusal records
        refusal_hash=refusal_hash,
        human_initiated=True,  # ALWAYS True
        actor="HUMAN",  # ALWAYS "HUMAN"
    )

