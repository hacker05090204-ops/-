"""
Phase-21 Patch Hash: SHA-256 hashing for patches.

This module provides ONLY hashing — NO analysis.
"""

import hashlib


def compute_patch_hash(patch_content: str) -> str:
    """
    Compute SHA-256 hash of patch content.
    
    This function:
    - Computes deterministic hash
    - Does NOT analyze content
    - Does NOT score content
    - Does NOT validate content
    
    Args:
        patch_content: Raw patch content (any string).
        
    Returns:
        64-character lowercase hex string (SHA-256).
    """
    return hashlib.sha256(patch_content.encode("utf-8")).hexdigest()


def create_binding_hash(
    patch_hash: str,
    decision_hash: str,
    timestamp: str,
) -> str:
    """
    Create binding hash from component hashes.
    
    This function:
    - Combines hashes deterministically
    - Does NOT analyze content
    - Does NOT score content
    
    Args:
        patch_hash: SHA-256 of patch content.
        decision_hash: SHA-256 of decision record.
        timestamp: ISO-8601 timestamp.
        
    Returns:
        64-character lowercase hex string (SHA-256).
    """
    combined = f"{patch_hash}:{decision_hash}:{timestamp}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def compute_decision_hash(
    patch_id: str,
    confirmed: bool,
    rejected: bool,
    reason: str,
    timestamp: str,
) -> str:
    """
    Compute SHA-256 hash of decision record.
    
    Args:
        patch_id: UUID of the patch.
        confirmed: Whether patch was confirmed.
        rejected: Whether patch was rejected.
        reason: Human-provided reason (not analyzed).
        timestamp: ISO-8601 timestamp.
        
    Returns:
        64-character lowercase hex string (SHA-256).
    """
    combined = f"{patch_id}:{confirmed}:{rejected}:{reason}:{timestamp}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()

