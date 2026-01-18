"""
Phase-20 Types: Human Reflection & Intent Capture

All types are IMMUTABLE (frozen dataclasses).
NO scoring, ranking, or analysis fields.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReflectionRecord:
    """
    Immutable record of human reflection.
    
    This record captures human intent WITHOUT analysis.
    All fields are primitive types (str, bool).
    NO scoring or quality fields exist.
    """
    
    session_id: str
    """UUID of the session this reflection belongs to."""
    
    timestamp: str
    """ISO-8601 timestamp when reflection was recorded."""
    
    reflection_text: str
    """Free-form reflection text. NOT ANALYZED. NOT VALIDATED."""
    
    reflection_hash: str
    """SHA-256 hash of reflection_text."""
    
    phase15_log_digest: str
    """SHA-256 digest of Phase-15 logs at time of reflection."""
    
    phase19_export_digest: str
    """SHA-256 digest of Phase-19 export (empty string if no export)."""
    
    declined: bool
    """True if human declined to provide reflection."""
    
    decline_reason: str
    """Free-form reason for decline. NOT ANALYZED. Empty if not declined."""
    
    human_initiated: bool
    """Always True. Reflection is ALWAYS human-initiated."""
    
    actor: str
    """Always 'HUMAN'. Reflection is ALWAYS attributed to human."""


@dataclass(frozen=True)
class ReflectionBinding:
    """
    Immutable cryptographic binding between reflection and phase artifacts.
    
    This binding creates tamper-evident proof that:
    - A specific reflection was made
    - At a specific time
    - Against specific Phase-15 and Phase-19 artifacts
    """
    
    binding_hash: str
    """SHA-256 of concatenated hashes (reflection + phase15 + phase19 + timestamp)."""
    
    reflection_hash: str
    """SHA-256 of the reflection text."""
    
    phase15_digest: str
    """SHA-256 digest of Phase-15 logs."""
    
    phase19_digest: str
    """SHA-256 digest of Phase-19 export."""
    
    timestamp: str
    """ISO-8601 timestamp when binding was created."""
    
    verifiable: bool
    """Always True. Binding is always verifiable."""
