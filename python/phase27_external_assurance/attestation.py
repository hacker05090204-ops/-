"""
Phase-27 Attestation: External Assurance & Proof

NO AUTHORITY / PROOF ONLY

Generates compliance attestations.
All operations require human_initiated=True.
Returns static output only.

This module has NO execution authority, NO enforcement authority.
This module does NOT make compliance decisions.
"""

import uuid
from datetime import datetime, timezone

from .types import ArtifactHash, ComplianceAttestation, ProofError, DISCLAIMER


def generate_attestation(
    artifact_hashes: tuple[ArtifactHash, ...],
    phases_covered: tuple[int, ...],
    *,
    human_initiated: bool,
) -> ComplianceAttestation | ProofError:
    """
    Generate a compliance attestation.
    
    NO AUTHORITY / PROOF ONLY
    
    Args:
        artifact_hashes: Tuple of artifact hashes to include.
        phases_covered: Tuple of phase numbers covered.
        human_initiated: MUST be True. Keyword-only argument.
    
    Returns:
        ComplianceAttestation if successful, ProofError if failed.
        Never raises exceptions.
    
    Constraints:
        - human_initiated=True is REQUIRED
        - Returns ProofError if human_initiated=False
        - Actor is ALWAYS 'HUMAN'
        - NO compliance decisions are made
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
    
    return ComplianceAttestation(
        attestation_id=str(uuid.uuid4()),
        timestamp=timestamp,
        artifact_hashes=artifact_hashes,
        phases_covered=phases_covered,
        human_initiated=True,
        disclaimer=DISCLAIMER,
        actor="HUMAN",
    )
