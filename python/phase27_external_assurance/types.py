"""
Phase-27 Types: External Assurance & Proof

NO AUTHORITY / PROOF ONLY

All types are IMMUTABLE (frozen dataclasses).
All types include disclaimer field.
All types require human_initiated field where applicable.

This module has NO execution authority, NO enforcement authority.
"""

from dataclasses import dataclass


# Standard disclaimer for all outputs
DISCLAIMER = """NO AUTHORITY / PROOF ONLY

This output is provided for external assurance purposes only.
This system has NO authority to make compliance decisions.
This system has NO authority to execute or enforce.
Human authority is required for all decisions."""


@dataclass(frozen=True)
class ArtifactHash:
    """
    Immutable artifact hash record.
    
    Hash is ALWAYS human-initiated.
    System does NOT auto-compute hashes.
    
    NO AUTHORITY / PROOF ONLY
    """
    
    artifact_path: str
    """Path to the artifact that was hashed."""
    
    hash_algorithm: str
    """Hash algorithm used. Always 'SHA-256'."""
    
    hash_value: str
    """Hex-encoded hash value."""
    
    computed_at: str
    """ISO-8601 timestamp when hash was computed."""
    
    human_initiated: bool
    """Always True. Hash computation is ALWAYS human-initiated."""
    
    disclaimer: str
    """Always contains NO AUTHORITY / PROOF ONLY disclaimer."""


@dataclass(frozen=True)
class ComplianceAttestation:
    """
    Immutable compliance attestation record.
    
    Attestation is ALWAYS human-initiated.
    System does NOT auto-generate attestations.
    System does NOT make compliance decisions.
    
    NO AUTHORITY / PROOF ONLY
    """
    
    attestation_id: str
    """UUID of this attestation."""
    
    timestamp: str
    """ISO-8601 timestamp when attestation was generated."""
    
    artifact_hashes: tuple[ArtifactHash, ...]
    """Tuple of artifact hashes included in attestation."""
    
    phases_covered: tuple[int, ...]
    """Tuple of phase numbers covered by this attestation."""
    
    human_initiated: bool
    """Always True. Attestation is ALWAYS human-initiated."""
    
    disclaimer: str
    """Always contains NO AUTHORITY / PROOF ONLY disclaimer."""
    
    actor: str
    """Always 'HUMAN'. Attestation is ALWAYS attributed to human."""


@dataclass(frozen=True)
class AuditBundle:
    """
    Immutable audit bundle record.
    
    Bundle is ALWAYS human-initiated.
    System does NOT auto-create bundles.
    
    NO AUTHORITY / PROOF ONLY
    """
    
    bundle_id: str
    """UUID of this bundle."""
    
    created_at: str
    """ISO-8601 timestamp when bundle was created."""
    
    attestations: tuple[ComplianceAttestation, ...]
    """Tuple of attestations included in bundle."""
    
    governance_docs: tuple[str, ...]
    """Tuple of governance document paths included in bundle."""
    
    bundle_hash: str
    """SHA-256 hash of bundle contents."""
    
    human_initiated: bool
    """Always True. Bundle creation is ALWAYS human-initiated."""
    
    disclaimer: str
    """Always contains NO AUTHORITY / PROOF ONLY disclaimer."""
    
    actor: str
    """Always 'HUMAN'. Bundle is ALWAYS attributed to human."""


@dataclass(frozen=True)
class ProofError:
    """
    Immutable error record.
    
    Errors are returned, NOT raised as exceptions.
    This ensures predictable, static output.
    
    NO AUTHORITY / PROOF ONLY
    """
    
    error_type: str
    """Error category (e.g., 'HUMAN_INITIATION_REQUIRED', 'FILE_NOT_FOUND')."""
    
    message: str
    """Human-readable error message."""
    
    timestamp: str
    """ISO-8601 timestamp when error occurred."""
    
    disclaimer: str
    """Always contains NO AUTHORITY / PROOF ONLY disclaimer."""
