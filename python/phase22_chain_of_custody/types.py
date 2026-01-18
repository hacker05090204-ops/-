"""
Phase-22 Types: Chain-of-Custody & Legal Attestation

All types are IMMUTABLE (frozen dataclasses).
NO scoring, validity judgment, or analysis fields.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CustodyEntry:
    """
    Immutable entry in the custody chain.
    
    Each entry links to the previous entry via hash.
    NO scoring or validity fields.
    """
    
    entry_id: str
    """UUID of this entry."""
    
    timestamp: str
    """ISO-8601 timestamp when entry was created."""
    
    previous_hash: str
    """SHA-256 hash of previous entry (empty for first entry)."""
    
    entry_hash: str
    """SHA-256 hash of this entry."""
    
    evidence_hash: str
    """SHA-256 hash of evidence being tracked."""
    
    event_type: str
    """Type of event: 'attestation', 'transfer', 'refusal'."""
    
    human_initiated: bool
    """Always True. Custody events are ALWAYS human-initiated."""
    
    actor: str
    """Always 'HUMAN'. Custody events are ALWAYS attributed to human."""


@dataclass(frozen=True)
class Attestation:
    """
    Immutable human attestation record.
    
    Attestation text is NOT analyzed.
    Attestor ID is NOT verified.
    """
    
    attestation_id: str
    """UUID of this attestation."""
    
    timestamp: str
    """ISO-8601 timestamp when attestation was made."""
    
    attestor_id: str
    """Free-text identifier of attestor (NOT verified)."""
    
    attestation_text: str
    """Free-text attestation (NOT analyzed)."""
    
    evidence_hash: str
    """SHA-256 hash of evidence being attested."""
    
    attestation_hash: str
    """SHA-256 hash of attestation content."""
    
    human_initiated: bool
    """Always True. Attestations are ALWAYS human-initiated."""
    
    actor: str
    """Always 'HUMAN'. Attestations are ALWAYS attributed to human."""


@dataclass(frozen=True)
class CustodyTransfer:
    """
    Immutable custody transfer record.
    
    Records transfer of evidence custody between parties.
    Party identifiers are NOT verified.
    """
    
    transfer_id: str
    """UUID of this transfer."""
    
    timestamp: str
    """ISO-8601 timestamp when transfer occurred."""
    
    from_party: str
    """Free-text identifier of source party (NOT verified)."""
    
    to_party: str
    """Free-text identifier of destination party (NOT verified)."""
    
    evidence_hash: str
    """SHA-256 hash of evidence being transferred."""
    
    attestation: Attestation
    """Human attestation for this transfer."""
    
    transfer_hash: str
    """SHA-256 hash of transfer record."""
    
    human_initiated: bool
    """Always True. Transfers are ALWAYS human-initiated."""
    
    actor: str
    """Always 'HUMAN'. Transfers are ALWAYS attributed to human."""


@dataclass(frozen=True)
class Refusal:
    """
    Immutable refusal to attest record.
    
    Refusal is ALWAYS allowed.
    Reason is NOT analyzed.
    """
    
    refusal_id: str
    """UUID of this refusal."""
    
    timestamp: str
    """ISO-8601 timestamp when refusal was recorded."""
    
    attestor_id: str
    """Free-text identifier of person refusing (NOT verified)."""
    
    evidence_hash: str
    """SHA-256 hash of evidence being refused."""
    
    reason: str
    """Free-text reason for refusal (NOT analyzed)."""
    
    refused: bool
    """Always True for refusal records."""
    
    refusal_hash: str
    """SHA-256 hash of refusal record."""
    
    human_initiated: bool
    """Always True. Refusals are ALWAYS human-initiated."""
    
    actor: str
    """Always 'HUMAN'. Refusals are ALWAYS attributed to human."""

