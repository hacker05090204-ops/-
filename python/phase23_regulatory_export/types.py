"""
Phase-23 Types: Regulatory Export & Jurisdiction Mode

All types are IMMUTABLE (frozen dataclasses).
NO legal interpretation or compliance scoring fields.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class JurisdictionSelection:
    """
    Immutable record of human jurisdiction selection.
    
    Jurisdiction is ALWAYS selected by human.
    System does NOT auto-select or recommend.
    """
    
    jurisdiction_code: str
    """Jurisdiction code (e.g., 'US', 'EU', 'UK')."""
    
    jurisdiction_name: str
    """Human-readable jurisdiction name."""
    
    selected_by: str
    """Free-text identifier of selector (NOT verified)."""
    
    timestamp: str
    """ISO-8601 timestamp when selection was made."""
    
    human_initiated: bool
    """Always True. Selection is ALWAYS human-initiated."""
    
    actor: str
    """Always 'HUMAN'. Selection is ALWAYS attributed to human."""


@dataclass(frozen=True)
class RegulatoryExport:
    """
    Immutable regulatory export record.
    
    Content is NOT modified — only formatted with disclaimers.
    """
    
    export_id: str
    """UUID of this export."""
    
    jurisdiction: JurisdictionSelection
    """Human-selected jurisdiction."""
    
    disclaimers: tuple[str, ...]
    """Static disclaimers for jurisdiction."""
    
    content_hash: str
    """SHA-256 of original content (preserved)."""
    
    export_hash: str
    """SHA-256 of export with disclaimers."""
    
    timestamp: str
    """ISO-8601 timestamp when export was created."""
    
    human_initiated: bool
    """Always True. Export is ALWAYS human-initiated."""
    
    actor: str
    """Always 'HUMAN'. Export is ALWAYS attributed to human."""


@dataclass(frozen=True)
class ExportDecline:
    """
    Immutable record of decline to export.
    
    Decline is ALWAYS allowed.
    Reason is NOT analyzed.
    """
    
    decline_id: str
    """UUID of this decline."""
    
    timestamp: str
    """ISO-8601 timestamp when decline was recorded."""
    
    reason: str
    """Free-text reason for decline (NOT analyzed)."""
    
    declined: bool
    """Always True for decline records."""
    
    human_initiated: bool
    """Always True. Decline is ALWAYS human-initiated."""
    
    actor: str
    """Always 'HUMAN'. Decline is ALWAYS attributed to human."""

