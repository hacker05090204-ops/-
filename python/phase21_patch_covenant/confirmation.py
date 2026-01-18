"""
Phase-21 Confirmation: Human confirmation recording.

This module records human decisions — NO automation, NO analysis.
"""

from .types import PatchRecord
from .patch_hash import compute_patch_hash, compute_decision_hash


def record_confirmation(
    patch_id: str,
    timestamp: str,
    confirmed: bool,
    reason: str,
    patch_hash: str = "",
    patch_diff: str = "",
    symbols_modified: tuple[str, ...] = (),
) -> PatchRecord:
    """
    Record human confirmation of a patch.
    
    This function:
    - Records human decision
    - Does NOT analyze reason
    - Does NOT score decision
    - Does NOT recommend actions
    - Always sets human_initiated=True
    - Always sets actor="HUMAN"
    
    Args:
        patch_id: UUID of the patch.
        timestamp: ISO-8601 timestamp.
        confirmed: True if human confirmed.
        reason: Human-provided reason (not analyzed).
        patch_hash: SHA-256 of patch content.
        patch_diff: Human-readable diff.
        symbols_modified: Symbols touched by patch.
        
    Returns:
        Immutable PatchRecord.
    """
    return PatchRecord(
        patch_id=patch_id,
        timestamp=timestamp,
        patch_hash=patch_hash,
        patch_diff=patch_diff,
        symbols_modified=symbols_modified,
        human_confirmed=confirmed,
        human_rejected=False,
        human_reason=reason,
        human_initiated=True,  # ALWAYS True
        actor="HUMAN",  # ALWAYS "HUMAN"
    )


def record_rejection(
    patch_id: str,
    timestamp: str,
    reason: str,
    patch_hash: str = "",
    patch_diff: str = "",
    symbols_modified: tuple[str, ...] = (),
) -> PatchRecord:
    """
    Record human rejection of a patch.
    
    Rejection is ALWAYS allowed.
    Reason is NOT analyzed.
    
    This function:
    - Records human rejection
    - Does NOT analyze reason
    - Does NOT score decision
    - Does NOT recommend actions
    - Always sets human_initiated=True
    - Always sets actor="HUMAN"
    
    Args:
        patch_id: UUID of the patch.
        timestamp: ISO-8601 timestamp.
        reason: Human-provided reason (not analyzed).
        patch_hash: SHA-256 of patch content.
        patch_diff: Human-readable diff.
        symbols_modified: Symbols touched by patch.
        
    Returns:
        Immutable PatchRecord.
    """
    return PatchRecord(
        patch_id=patch_id,
        timestamp=timestamp,
        patch_hash=patch_hash,
        patch_diff=patch_diff,
        symbols_modified=symbols_modified,
        human_confirmed=False,
        human_rejected=True,  # Rejection recorded
        human_reason=reason,  # Stored as-is, NOT analyzed
        human_initiated=True,  # ALWAYS True
        actor="HUMAN",  # ALWAYS "HUMAN"
    )

