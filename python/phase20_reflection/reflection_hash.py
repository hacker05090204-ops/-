"""
Phase-20 Reflection Hash: Cryptographic Hashing

Provides SHA-256 hashing for reflection text and binding creation.
NO content analysis. Hash is computed on raw bytes only.
"""

import hashlib
from datetime import datetime, timezone

from .types import ReflectionBinding


def hash_reflection(text: str) -> str:
    """
    Compute SHA-256 hash of reflection text.
    
    Args:
        text: Reflection text (any UTF-8 string, including empty).
        
    Returns:
        64-character lowercase hex string (SHA-256).
        
    Note:
        This function does NOT analyze content.
        It hashes raw UTF-8 bytes without preprocessing.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def create_binding(
    reflection_hash: str,
    phase15_digest: str,
    phase19_digest: str,
) -> ReflectionBinding:
    """
    Create cryptographic binding between reflection and phase artifacts.
    
    Args:
        reflection_hash: SHA-256 of reflection text.
        phase15_digest: SHA-256 digest of Phase-15 logs.
        phase19_digest: SHA-256 digest of Phase-19 export.
        
    Returns:
        Immutable ReflectionBinding with computed binding_hash.
        
    Note:
        Binding hash is SHA-256 of concatenated inputs + timestamp.
        This creates tamper-evident proof of the binding.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Concatenate all inputs for binding hash
    binding_input = f"{reflection_hash}:{phase15_digest}:{phase19_digest}:{timestamp}"
    binding_hash = hashlib.sha256(binding_input.encode("utf-8")).hexdigest()
    
    return ReflectionBinding(
        binding_hash=binding_hash,
        reflection_hash=reflection_hash,
        phase15_digest=phase15_digest,
        phase19_digest=phase19_digest,
        timestamp=timestamp,
        verifiable=True,
    )
