"""
Phase-22: Chain-of-Custody & Legal Attestation

This module provides legally defensible chain-of-custody tracking.

CONSTRAINTS:
- Human attestation REQUIRED for custody events
- NO auto-generation of attestations
- NO evidence modification
- NO validity judgment
- NO content analysis
- NO prior phase imports (Phase-13 through Phase-21)

All operations are human-initiated and human-attributed.
"""

from .types import (
    CustodyEntry,
    Attestation,
    CustodyTransfer,
    Refusal,
)

from .hash_chain import (
    compute_entry_hash,
    create_chain_entry,
    verify_chain,
)

from .attestation import (
    compute_attestation_hash,
    create_attestation,
)

from .refusal import (
    compute_refusal_hash,
    record_refusal,
)


__all__ = [
    # Types
    "CustodyEntry",
    "Attestation",
    "CustodyTransfer",
    "Refusal",
    # Hash chain
    "compute_entry_hash",
    "create_chain_entry",
    "verify_chain",
    # Attestation
    "compute_attestation_hash",
    "create_attestation",
    # Refusal
    "compute_refusal_hash",
    "record_refusal",
]

