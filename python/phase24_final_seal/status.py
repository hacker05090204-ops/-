"""
Phase-24 Status: Governance status reporting.

Status is read-only after seal.
"""

from .types import GovernanceStatus


# All phases that are frozen when system is sealed
_ALL_PHASES: tuple[int, ...] = tuple(range(13, 25))  # Phases 13-24


def get_governance_status(
    sealed: bool,
    decommissioned: bool,
    sealed_at: str | None = None,
    decommissioned_at: str | None = None,
) -> GovernanceStatus:
    """
    Get current governance status.
    
    This function:
    - Reports current status
    - Does NOT modify status
    - Does NOT trigger actions
    
    Args:
        sealed: Whether system is sealed.
        decommissioned: Whether system is decommissioned.
        sealed_at: ISO-8601 timestamp of seal, or None.
        decommissioned_at: ISO-8601 timestamp of decommission, or None.
        
    Returns:
        Immutable GovernanceStatus.
    """
    if decommissioned:
        status = "decommissioned"
        phases_frozen = _ALL_PHASES
    elif sealed:
        status = "sealed"
        phases_frozen = _ALL_PHASES
    else:
        status = "active"
        phases_frozen = ()
    
    return GovernanceStatus(
        status=status,
        sealed_at=sealed_at,
        decommissioned_at=decommissioned_at,
        phases_frozen=phases_frozen,
    )

