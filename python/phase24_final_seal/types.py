"""
Phase-24 Types: Final System Seal & Decommission Mode

All types are IMMUTABLE (frozen dataclasses).
NO automation or auto-trigger fields.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SystemSeal:
    """
    Immutable system seal record.
    
    Seal is ALWAYS human-initiated.
    System does NOT auto-seal.
    """
    
    seal_id: str
    """UUID of this seal."""
    
    timestamp: str
    """ISO-8601 timestamp when seal was created."""
    
    sealed_by: str
    """Free-text identifier of sealer (NOT verified)."""
    
    seal_reason: str
    """Free-text reason for seal (NOT analyzed)."""
    
    archive_hash: str
    """SHA-256 of complete archive at seal time."""
    
    seal_hash: str
    """SHA-256 of seal record."""
    
    sealed: bool
    """Always True for seal records."""
    
    human_initiated: bool
    """Always True. Seal is ALWAYS human-initiated."""
    
    actor: str
    """Always 'HUMAN'. Seal is ALWAYS attributed to human."""


@dataclass(frozen=True)
class DecommissionRecord:
    """
    Immutable decommission record.
    
    Decommission is ALWAYS human-initiated.
    System does NOT auto-decommission.
    """
    
    decommission_id: str
    """UUID of this decommission."""
    
    timestamp: str
    """ISO-8601 timestamp when decommission was recorded."""
    
    decommissioned_by: str
    """Free-text identifier of decommissioner (NOT verified)."""
    
    reason: str
    """Free-text reason for decommission (NOT analyzed)."""
    
    archive_hash: str
    """SHA-256 of archive at decommission time."""
    
    decommissioned: bool
    """Always True for decommission records."""
    
    human_initiated: bool
    """Always True. Decommission is ALWAYS human-initiated."""
    
    actor: str
    """Always 'HUMAN'. Decommission is ALWAYS attributed to human."""


@dataclass(frozen=True)
class GovernanceStatus:
    """
    Immutable governance status record.
    
    Status is read-only after seal.
    """
    
    status: str
    """Current status: 'active', 'sealed', 'decommissioned'."""
    
    sealed_at: str | None
    """ISO-8601 timestamp of seal, or None if not sealed."""
    
    decommissioned_at: str | None
    """ISO-8601 timestamp of decommission, or None if not decommissioned."""
    
    phases_frozen: tuple[int, ...]
    """Tuple of frozen phase numbers."""

