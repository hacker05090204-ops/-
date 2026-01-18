"""
Phase-28 Selector: Human-Initiated Proof Selection

NO AUTHORITY / PRESENTATION ONLY

Records human proof selections.
Does NOT filter, rank, or recommend.
Does NOT modify selection order.

All selection is human-initiated.
"""

from datetime import datetime, timezone
from typing import Union
import uuid

from .types import (
    DISCLAIMER,
    ProofSelection,
    PresentationError,
)


def select_proofs(
    attestation_ids: list[str],
    bundle_ids: list[str],
    *,
    human_initiated: bool,
) -> Union[ProofSelection, PresentationError]:
    """
    Record human proof selection.
    
    NO AUTHORITY / PRESENTATION ONLY
    
    Does NOT filter, rank, or recommend.
    Records selection exactly as provided.
    
    Args:
        attestation_ids: List of attestation IDs selected by human
        bundle_ids: List of bundle IDs selected by human
        human_initiated: MUST be True
        
    Returns:
        ProofSelection or PresentationError
    """
    if not human_initiated:
        return PresentationError(
            error_type="HUMAN_INITIATION_REQUIRED",
            message="Selection requires human_initiated=True",
            timestamp=datetime.now(timezone.utc).isoformat(),
            disclaimer=DISCLAIMER,
        )
    
    # Record selection exactly as provided (no filtering, ranking, or modification)
    return ProofSelection(
        selection_id=str(uuid.uuid4()),
        selected_by="HUMAN",
        selected_at=datetime.now(timezone.utc).isoformat(),
        attestation_ids=tuple(attestation_ids),  # Preserve order
        bundle_ids=tuple(bundle_ids),  # Preserve order
        human_initiated=True,
        disclaimer=DISCLAIMER,
    )


def list_available_proofs(
    *,
    human_initiated: bool,
) -> Union[dict, PresentationError]:
    """
    List available proofs for human selection.
    
    NO AUTHORITY / PRESENTATION ONLY
    
    Does NOT filter, rank, or recommend.
    Returns all available proofs equally.
    
    Args:
        human_initiated: MUST be True
        
    Returns:
        Dict with available proofs or PresentationError
    """
    if not human_initiated:
        return PresentationError(
            error_type="HUMAN_INITIATION_REQUIRED",
            message="Listing requires human_initiated=True",
            timestamp=datetime.now(timezone.utc).isoformat(),
            disclaimer=DISCLAIMER,
        )
    
    # Return structure for available proofs
    # Actual proof discovery would be done by reading Phase-27 outputs
    return {
        "disclaimer": DISCLAIMER,
        "note": "Human must select proofs. System does NOT recommend.",
        "attestations": [],  # Would be populated from Phase-27
        "bundles": [],  # Would be populated from Phase-27
        "listed_at": datetime.now(timezone.utc).isoformat(),
        "listed_by": "HUMAN",
    }
