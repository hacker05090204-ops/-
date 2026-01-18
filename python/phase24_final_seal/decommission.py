"""
Phase-24 Decommission: Human-confirmed decommission.

Decommission is ALWAYS human-initiated — NO auto-decommission.
"""

import uuid

from .types import DecommissionRecord


def create_decommission(
    decommissioned_by: str,
    reason: str,
    archive_hash: str,
    timestamp: str,
) -> DecommissionRecord:
    """
    Create a decommission record with human confirmation.
    
    This function:
    - Creates decommission record
    - Does NOT auto-decommission
    - Does NOT schedule decommission
    - Always sets human_initiated=True
    - Always sets actor="HUMAN"
    
    Args:
        decommissioned_by: Free-text identifier (NOT verified).
        reason: Free-text reason (NOT analyzed).
        archive_hash: SHA-256 of archive at decommission.
        timestamp: ISO-8601 timestamp.
        
    Returns:
        Immutable DecommissionRecord.
    """
    decommission_id = str(uuid.uuid4())
    
    return DecommissionRecord(
        decommission_id=decommission_id,
        timestamp=timestamp,
        decommissioned_by=decommissioned_by,
        reason=reason,  # Stored as-is, NOT analyzed
        archive_hash=archive_hash,
        decommissioned=True,  # Always True for decommission records
        human_initiated=True,  # ALWAYS True
        actor="HUMAN",  # ALWAYS "HUMAN"
    )

