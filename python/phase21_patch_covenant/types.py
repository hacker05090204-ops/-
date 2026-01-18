"""
Phase-21 Types: Patch Covenant & Update Validation

All types are IMMUTABLE (frozen dataclasses).
NO scoring, ranking, or analysis fields.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PatchRecord:
    """
    Immutable record of a patch and its human decision.
    
    This record captures patch metadata WITHOUT analysis.
    All fields are primitive types.
    NO scoring or quality fields exist.
    """
    
    patch_id: str
    """UUID of the patch."""
    
    timestamp: str
    """ISO-8601 timestamp when record was created."""
    
    patch_hash: str
    """SHA-256 hash of patch content."""
    
    patch_diff: str
    """Human-readable diff. NOT ANALYZED."""
    
    symbols_modified: tuple[str, ...]
    """Symbols touched by this patch. Immutable tuple."""
    
    human_confirmed: bool
    """True if human confirmed the patch."""
    
    human_rejected: bool
    """True if human rejected the patch."""
    
    human_reason: str
    """Free-form reason for decision. NOT ANALYZED."""
    
    human_initiated: bool
    """Always True. Patch decisions are ALWAYS human-initiated."""
    
    actor: str
    """Always 'HUMAN'. Patch decisions are ALWAYS attributed to human."""


@dataclass(frozen=True)
class PatchBinding:
    """
    Immutable cryptographic binding between patch and human decision.
    
    This binding creates tamper-evident proof that:
    - A specific patch was reviewed
    - A specific decision was made
    - At a specific time
    """
    
    binding_hash: str
    """SHA-256 of concatenated hashes (patch + decision + timestamp)."""
    
    patch_hash: str
    """SHA-256 of the patch content."""
    
    decision_hash: str
    """SHA-256 of the decision record."""
    
    timestamp: str
    """ISO-8601 timestamp when binding was created."""
    
    session_id: str
    """UUID of the session."""
    
    verifiable: bool
    """Always True. Binding is always verifiable."""


@dataclass(frozen=True)
class SymbolConstraints:
    """
    Immutable symbol constraints for patch validation.
    
    Allowlist: symbols that MAY be modified.
    Denylist: symbols that MUST NOT appear.
    
    Both lists are STATIC (frozenset) — no runtime modification.
    """
    
    allowlist: frozenset[str]
    """Symbols that MAY be modified by patches."""
    
    denylist: frozenset[str]
    """Symbols that MUST NOT appear in patches."""
    
    version: str
    """Constraint version. Immutable."""


@dataclass(frozen=True)
class ValidationResult:
    """
    Immutable result of symbol validation.
    
    Contains ONLY pass/fail — NO scoring.
    """
    
    passed: bool
    """True if validation passed, False otherwise."""
    
    blocked_symbols: tuple[str, ...]
    """Symbols that caused validation to fail. Empty if passed."""
    
    constraint_version: str
    """Version of constraints used for validation."""


@dataclass(frozen=True)
class ApplyResult:
    """
    Immutable result of patch application.
    
    Contains application status and human attribution.
    NO scoring or quality fields.
    """
    
    applied: bool
    """True if patch was applied."""
    
    patch_hash: str
    """SHA-256 of applied patch."""
    
    confirmation_hash: str
    """SHA-256 of confirmation record."""
    
    timestamp: str
    """ISO-8601 timestamp of application."""
    
    human_initiated: bool
    """Always True. Application is ALWAYS human-initiated."""
    
    actor: str
    """Always 'HUMAN'. Application is ALWAYS attributed to human."""

