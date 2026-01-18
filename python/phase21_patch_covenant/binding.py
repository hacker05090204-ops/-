"""
Phase-21 Binding: Cryptographic binding creation.

This module creates tamper-evident bindings — NO analysis.
"""

from .types import PatchBinding
from .patch_hash import create_binding_hash


def create_patch_binding(
    patch_hash: str,
    decision_hash: str,
    timestamp: str,
    session_id: str,
) -> PatchBinding:
    """
    Create cryptographic binding between patch and decision.
    
    This function:
    - Creates immutable binding
    - Does NOT analyze content
    - Does NOT score content
    - Does NOT recommend actions
    
    Args:
        patch_hash: SHA-256 of patch content.
        decision_hash: SHA-256 of decision record.
        timestamp: ISO-8601 timestamp.
        session_id: UUID of the session.
        
    Returns:
        Immutable PatchBinding.
    """
    binding_hash = create_binding_hash(
        patch_hash=patch_hash,
        decision_hash=decision_hash,
        timestamp=timestamp,
    )
    
    return PatchBinding(
        binding_hash=binding_hash,
        patch_hash=patch_hash,
        decision_hash=decision_hash,
        timestamp=timestamp,
        session_id=session_id,
        verifiable=True,  # ALWAYS True
    )


def verify_binding(binding: PatchBinding) -> bool:
    """
    Verify a patch binding is valid.
    
    This function:
    - Recomputes binding hash
    - Compares with stored hash
    - Returns True/False only (no scoring)
    
    Args:
        binding: PatchBinding to verify.
        
    Returns:
        True if binding is valid, False otherwise.
    """
    expected_hash = create_binding_hash(
        patch_hash=binding.patch_hash,
        decision_hash=binding.decision_hash,
        timestamp=binding.timestamp,
    )
    
    return binding.binding_hash == expected_hash

