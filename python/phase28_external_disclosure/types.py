"""
Phase-28 Types: External Disclosure & Verifiable Presentation Layer

NO AUTHORITY / PRESENTATION ONLY

All types are IMMUTABLE (frozen dataclasses).
All types include disclaimer field.
All types require human_initiated field where applicable.

This module has NO execution authority, NO enforcement authority.
This module does NOT interpret, analyze, or recommend.
"""

from dataclasses import dataclass


# Primary disclaimer for all outputs
DISCLAIMER = """NO AUTHORITY / PRESENTATION ONLY

This output presents Phase-27 proofs without interpretation.
This system does NOT analyze, judge, or recommend.
Human review is required before any disclosure."""


# Not verified notice for all outputs
NOT_VERIFIED_NOTICE = """NOT VERIFIED — PROOF OF PROCESS, NOT CERTIFICATION

This presentation is provided for disclosure purposes only.
This system has NO authority to verify, certify, or validate.
This system has NO authority to make compliance decisions.
Human authority is required for all decisions."""


@dataclass(frozen=True)
class DisclosureContext:
    """
    Immutable disclosure context record.
    
    Context is ALWAYS human-provided.
    System does NOT modify or interpret context.
    
    NO AUTHORITY / PRESENTATION ONLY
    """
    
    context_id: str
    """UUID of this context."""
    
    provided_by: str
    """Always 'HUMAN'. Context is ALWAYS human-provided."""
    
    provided_at: str
    """ISO-8601 timestamp when context was provided."""
    
    context_text: str
    """Human-provided context text (unmodified)."""
    
    human_initiated: bool
    """Always True. Context provision is ALWAYS human-initiated."""
    
    disclaimer: str
    """Always contains NO AUTHORITY / PRESENTATION ONLY disclaimer."""


@dataclass(frozen=True)
class ProofSelection:
    """
    Immutable proof selection record.
    
    Selection is ALWAYS human-initiated.
    System does NOT filter, rank, or recommend.
    
    NO AUTHORITY / PRESENTATION ONLY
    """
    
    selection_id: str
    """UUID of this selection."""
    
    selected_by: str
    """Always 'HUMAN'. Selection is ALWAYS human-made."""
    
    selected_at: str
    """ISO-8601 timestamp when selection was made."""
    
    attestation_ids: tuple[str, ...]
    """Tuple of selected attestation IDs."""
    
    bundle_ids: tuple[str, ...]
    """Tuple of selected bundle IDs."""
    
    human_initiated: bool
    """Always True. Selection is ALWAYS human-initiated."""
    
    disclaimer: str
    """Always contains NO AUTHORITY / PRESENTATION ONLY disclaimer."""


@dataclass(frozen=True)
class DisclosurePackage:
    """
    Immutable disclosure package record.
    
    Package is ALWAYS human-initiated.
    System does NOT auto-share or auto-submit.
    
    NO AUTHORITY / PRESENTATION ONLY
    """
    
    package_id: str
    """UUID of this package."""
    
    created_at: str
    """ISO-8601 timestamp when package was created."""
    
    created_by: str
    """Always 'HUMAN'. Package is ALWAYS human-created."""
    
    context: DisclosureContext
    """Human-provided disclosure context."""
    
    selection: ProofSelection
    """Human-selected proofs."""
    
    rendered_content: str
    """Static rendered content."""
    
    package_hash: str
    """SHA-256 hash of package contents."""
    
    human_initiated: bool
    """Always True. Package creation is ALWAYS human-initiated."""
    
    disclaimer: str
    """Always contains NO AUTHORITY / PRESENTATION ONLY disclaimer."""
    
    not_verified_notice: str
    """Always contains NOT VERIFIED notice."""


@dataclass(frozen=True)
class PresentationError:
    """
    Immutable error record.
    
    Errors are returned, NOT raised as exceptions.
    This ensures predictable, static output.
    
    NO AUTHORITY / PRESENTATION ONLY
    """
    
    error_type: str
    """Error category (e.g., 'HUMAN_INITIATION_REQUIRED')."""
    
    message: str
    """Human-readable error message."""
    
    timestamp: str
    """ISO-8601 timestamp when error occurred."""
    
    disclaimer: str
    """Always contains NO AUTHORITY / PRESENTATION ONLY disclaimer."""
