"""
Phase-27 Audit Bundle: External Assurance & Proof

NO AUTHORITY / PROOF ONLY

Creates audit bundles for external verification.
All operations require human_initiated=True.
Returns static output only.

This module has NO execution authority, NO enforcement authority.
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone

from .types import AuditBundle, ComplianceAttestation, ProofError, DISCLAIMER


def _compute_bundle_hash(
    bundle_id: str,
    created_at: str,
    attestations: tuple[ComplianceAttestation, ...],
    governance_docs: tuple[str, ...],
) -> str:
    """
    Compute SHA-256 hash of bundle contents.
    
    Internal function - not exported.
    """
    # Create deterministic representation
    content = {
        "bundle_id": bundle_id,
        "created_at": created_at,
        "attestation_ids": [a.attestation_id for a in attestations],
        "governance_docs": list(governance_docs),
    }
    content_str = json.dumps(content, sort_keys=True)
    return hashlib.sha256(content_str.encode()).hexdigest()


def create_audit_bundle(
    attestations: tuple[ComplianceAttestation, ...],
    governance_docs: tuple[str, ...],
    *,
    human_initiated: bool,
) -> AuditBundle | ProofError:
    """
    Create an audit bundle.
    
    NO AUTHORITY / PROOF ONLY
    
    Args:
        attestations: Tuple of attestations to include.
        governance_docs: Tuple of governance document paths.
        human_initiated: MUST be True. Keyword-only argument.
    
    Returns:
        AuditBundle if successful, ProofError if failed.
        Never raises exceptions.
    
    Constraints:
        - human_initiated=True is REQUIRED
        - Returns ProofError if human_initiated=False
        - Actor is ALWAYS 'HUMAN'
        - NO execution authority
        - NO enforcement authority
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Check human initiation FIRST
    if not human_initiated:
        return ProofError(
            error_type="HUMAN_INITIATION_REQUIRED",
            message="Action requires human_initiated=True",
            timestamp=timestamp,
            disclaimer=DISCLAIMER,
        )
    
    bundle_id = str(uuid.uuid4())
    
    # Compute bundle hash
    bundle_hash = _compute_bundle_hash(
        bundle_id=bundle_id,
        created_at=timestamp,
        attestations=attestations,
        governance_docs=governance_docs,
    )
    
    return AuditBundle(
        bundle_id=bundle_id,
        created_at=timestamp,
        attestations=attestations,
        governance_docs=governance_docs,
        bundle_hash=bundle_hash,
        human_initiated=True,
        disclaimer=DISCLAIMER,
        actor="HUMAN",
    )
