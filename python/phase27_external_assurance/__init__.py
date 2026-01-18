"""
Phase-27: External Assurance & Proof

NO AUTHORITY / PROOF ONLY

This module provides external assurance and proof capabilities.

CONSTRAINTS:
- Human MUST initiate all actions (human_initiated=True)
- NO execution authority
- NO enforcement authority
- NO automation
- NO scoring or ranking
- NO compliance decisions
- NO network access
- Static output only (MD, TXT, JSON)
- All outputs include "NO AUTHORITY / PROOF ONLY" disclaimer
- SHA-256 or stronger for all hashes

ALLOWED ACTIONS:
- Read governance documents
- Read test results
- Compute hashes of frozen artifacts
- Generate compliance attestations
- Export audit bundles (human-triggered)

FORBIDDEN ACTIONS:
- Import runtime or execution layers
- Modify any prior phase
- Add background services, automation, scoring, ranking, recommendations
- Perform compliance decisions
- Make network requests

All operations are human-initiated and human-attributed.
"""

from .types import (
    DISCLAIMER,
    ArtifactHash,
    ComplianceAttestation,
    AuditBundle,
    ProofError,
)

from .hash_computer import (
    compute_artifact_hash,
)

from .attestation import (
    generate_attestation,
)

from .audit_bundle import (
    create_audit_bundle,
)


__all__ = [
    # Constants
    "DISCLAIMER",
    # Types
    "ArtifactHash",
    "ComplianceAttestation",
    "AuditBundle",
    "ProofError",
    # Hash computation
    "compute_artifact_hash",
    # Attestation
    "generate_attestation",
    # Audit bundle
    "create_audit_bundle",
]
