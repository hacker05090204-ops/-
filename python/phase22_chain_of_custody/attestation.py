"""
Phase-22 Attestation: Human attestation recording.

This module records attestations — NO auto-generation, NO analysis.
"""

import hashlib
import uuid

from .types import Attestation


def compute_attestation_hash(
    attestation_id: str,
    timestamp: str,
    attestor_id: str,
    attestation_text: str,
    evidence_hash: str,
) -> str:
    """
    Compute SHA-256 hash of attestation content.
    
    Args:
        attestation_id: UUID of the attestation.
        timestamp: ISO-8601 timestamp.
        attestor_id: Identifier of attestor.
        attestation_text: Attestation text.
        evidence_hash: Hash of evidence.
        
    Returns:
        64-character lowercase hex string (SHA-256).
    """
    combined = f"{attestation_id}:{timestamp}:{attestor_id}:{attestation_text}:{evidence_hash}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def create_attestation(
    evidence_hash: str,
    attestor_id: str,
    attestation_text: str,
    timestamp: str,
) -> Attestation:
    """
    Create a human attestation record.
    
    This function:
    - Records human attestation
    - Does NOT analyze attestation text
    - Does NOT verify attestor identity
    - Does NOT judge validity
    - Always sets human_initiated=True
    - Always sets actor="HUMAN"
    
    Args:
        evidence_hash: SHA-256 of evidence being attested.
        attestor_id: Free-text identifier of attestor (NOT verified).
        attestation_text: Free-text attestation (NOT analyzed).
        timestamp: ISO-8601 timestamp.
        
    Returns:
        Immutable Attestation.
    """
    attestation_id = str(uuid.uuid4())
    
    attestation_hash = compute_attestation_hash(
        attestation_id=attestation_id,
        timestamp=timestamp,
        attestor_id=attestor_id,
        attestation_text=attestation_text,
        evidence_hash=evidence_hash,
    )
    
    return Attestation(
        attestation_id=attestation_id,
        timestamp=timestamp,
        attestor_id=attestor_id,
        attestation_text=attestation_text,  # Stored as-is, NOT analyzed
        evidence_hash=evidence_hash,
        attestation_hash=attestation_hash,
        human_initiated=True,  # ALWAYS True
        actor="HUMAN",  # ALWAYS "HUMAN"
    )

