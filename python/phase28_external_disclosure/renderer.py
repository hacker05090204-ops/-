"""
Phase-28 Renderer: Static Proof Rendering

NO AUTHORITY / PRESENTATION ONLY

Renders Phase-27 proofs using static templates.
Does NOT interpret, analyze, or recommend.
Does NOT format based on content analysis.
Does NOT detect platforms.

All rendering is human-initiated.
"""

from datetime import datetime, timezone
from typing import Union

from .types import (
    DISCLAIMER,
    NOT_VERIFIED_NOTICE,
    PresentationError,
)


# Static template for proof rendering
PROOF_TEMPLATE = """
================================================================================
{not_verified_notice}
================================================================================

PROOF PRESENTATION
------------------

{proof_content}

================================================================================
{disclaimer}
================================================================================

Rendered: {timestamp}
Rendered By: HUMAN (human-initiated)
"""


# Static template for attestation rendering
ATTESTATION_TEMPLATE = """
================================================================================
{not_verified_notice}
================================================================================

ATTESTATION PRESENTATION
------------------------

Attestation ID: {attestation_id}
Timestamp: {attestation_timestamp}
Phases Covered: {phases_covered}
Actor: {actor}

Artifact Hashes:
{artifact_hashes}

================================================================================
{disclaimer}
================================================================================

Rendered: {timestamp}
Rendered By: HUMAN (human-initiated)
"""


# Static template for bundle rendering
BUNDLE_TEMPLATE = """
================================================================================
{not_verified_notice}
================================================================================

AUDIT BUNDLE PRESENTATION
-------------------------

Bundle ID: {bundle_id}
Created: {bundle_created}
Actor: {actor}
Bundle Hash: {bundle_hash}

Governance Documents:
{governance_docs}

Attestations:
{attestations}

================================================================================
{disclaimer}
================================================================================

Rendered: {timestamp}
Rendered By: HUMAN (human-initiated)
"""


def render_proofs(
    proofs: list,
    *,
    human_initiated: bool,
) -> Union[str, PresentationError]:
    """
    Render proofs using static template.
    
    NO AUTHORITY / PRESENTATION ONLY
    
    Args:
        proofs: List of Phase-27 proof objects
        human_initiated: MUST be True
        
    Returns:
        Rendered string or PresentationError
    """
    if not human_initiated:
        return PresentationError(
            error_type="HUMAN_INITIATION_REQUIRED",
            message="Rendering requires human_initiated=True",
            timestamp=datetime.now(timezone.utc).isoformat(),
            disclaimer=DISCLAIMER,
        )
    
    # Build proof content without interpretation
    proof_lines = []
    for i, proof in enumerate(proofs):
        proof_lines.append(f"Proof {i + 1}:")
        if hasattr(proof, 'attestation_id'):
            proof_lines.append(f"  Type: Attestation")
            proof_lines.append(f"  ID: {proof.attestation_id}")
        elif hasattr(proof, 'bundle_id'):
            proof_lines.append(f"  Type: Bundle")
            proof_lines.append(f"  ID: {proof.bundle_id}")
        elif hasattr(proof, 'hash_value'):
            proof_lines.append(f"  Type: Hash")
            proof_lines.append(f"  Value: {proof.hash_value}")
        proof_lines.append("")
    
    return PROOF_TEMPLATE.format(
        not_verified_notice=NOT_VERIFIED_NOTICE,
        proof_content="\n".join(proof_lines) if proof_lines else "(No proofs selected)",
        disclaimer=DISCLAIMER,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def render_attestation(
    attestation,
    *,
    human_initiated: bool,
) -> Union[str, PresentationError]:
    """
    Render attestation using static template.
    
    NO AUTHORITY / PRESENTATION ONLY
    
    Args:
        attestation: Phase-27 ComplianceAttestation
        human_initiated: MUST be True
        
    Returns:
        Rendered string or PresentationError
    """
    if not human_initiated:
        return PresentationError(
            error_type="HUMAN_INITIATION_REQUIRED",
            message="Rendering requires human_initiated=True",
            timestamp=datetime.now(timezone.utc).isoformat(),
            disclaimer=DISCLAIMER,
        )
    
    # Build hash list without interpretation
    hash_lines = []
    for h in attestation.artifact_hashes:
        hash_lines.append(f"  - {h.artifact_path}: {h.hash_value}")
    
    return ATTESTATION_TEMPLATE.format(
        not_verified_notice=NOT_VERIFIED_NOTICE,
        attestation_id=attestation.attestation_id,
        attestation_timestamp=attestation.timestamp,
        phases_covered=", ".join(str(p) for p in attestation.phases_covered),
        actor=attestation.actor,
        artifact_hashes="\n".join(hash_lines) if hash_lines else "  (none)",
        disclaimer=DISCLAIMER,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def render_bundle(
    bundle,
    *,
    human_initiated: bool,
) -> Union[str, PresentationError]:
    """
    Render bundle using static template.
    
    NO AUTHORITY / PRESENTATION ONLY
    
    Args:
        bundle: Phase-27 AuditBundle
        human_initiated: MUST be True
        
    Returns:
        Rendered string or PresentationError
    """
    if not human_initiated:
        return PresentationError(
            error_type="HUMAN_INITIATION_REQUIRED",
            message="Rendering requires human_initiated=True",
            timestamp=datetime.now(timezone.utc).isoformat(),
            disclaimer=DISCLAIMER,
        )
    
    # Build governance doc list without interpretation
    doc_lines = []
    for doc in bundle.governance_docs:
        doc_lines.append(f"  - {doc}")
    
    # Build attestation list without interpretation
    att_lines = []
    for att in bundle.attestations:
        att_lines.append(f"  - {att.attestation_id}")
    
    return BUNDLE_TEMPLATE.format(
        not_verified_notice=NOT_VERIFIED_NOTICE,
        bundle_id=bundle.bundle_id,
        bundle_created=bundle.created_at,
        actor=bundle.actor,
        bundle_hash=bundle.bundle_hash,
        governance_docs="\n".join(doc_lines) if doc_lines else "  (none)",
        attestations="\n".join(att_lines) if att_lines else "  (none)",
        disclaimer=DISCLAIMER,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
