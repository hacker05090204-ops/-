"""
Phase-21 Patch Applicator: Human-confirmed patch application.

This module applies patches ONLY with human confirmation — NO automation.
"""

from datetime import datetime, timezone

from .types import PatchRecord, ApplyResult
from .patch_hash import compute_patch_hash


def apply_patch(
    patch_content: str,
    confirmation: PatchRecord | None,
) -> ApplyResult:
    """
    Apply a patch with human confirmation.
    
    This function:
    - REQUIRES human confirmation
    - Does NOT auto-apply
    - Does NOT analyze patch
    - Does NOT score patch
    - Does NOT recommend actions
    
    Args:
        patch_content: Patch content to apply.
        confirmation: Human confirmation record (REQUIRED).
        
    Returns:
        ApplyResult with application status.
        
    Raises:
        ValueError: If confirmation is missing or is a rejection.
    """
    # Confirmation is REQUIRED
    if confirmation is None:
        raise ValueError("Human confirmation required to apply patch")
    
    # Cannot apply rejected patches
    if confirmation.human_rejected:
        raise ValueError("Cannot apply patch: patch was rejected by human")
    
    # Must be confirmed
    if not confirmation.human_confirmed:
        raise ValueError("Human confirmation required to apply patch")
    
    # Compute patch hash
    patch_hash = compute_patch_hash(patch_content)
    
    # Create confirmation hash
    confirmation_hash = compute_patch_hash(
        f"{confirmation.patch_id}:{confirmation.timestamp}:{confirmation.human_reason}"
    )
    
    timestamp = datetime.now(timezone.utc).isoformat()
    
    return ApplyResult(
        applied=True,
        patch_hash=patch_hash,
        confirmation_hash=confirmation_hash,
        timestamp=timestamp,
        human_initiated=True,  # ALWAYS True
        actor="HUMAN",  # ALWAYS "HUMAN"
    )

