"""
PHASE 03 — TRUST BOUNDARIES
2026 RE-IMPLEMENTATION

This module defines trust zones and boundaries for the kali-mcp-toolkit system.

⚠️ CRITICAL NOTICE:
    This is a 2026 RE-IMPLEMENTATION.
    This is NOT a recovery of lost code.

Document ID: GOV-PHASE03-2026-REIMPL-CODE
Date: 2026-01-20
Status: IMPLEMENTED
"""

from dataclasses import dataclass
from enum import Enum
from typing import Final

from phase02_actors import Actor, Role


# =============================================================================
# TRUST ZONE ENUM
# =============================================================================

class TrustZone(Enum):
    """
    Defines zones of trust within the system.
    
    Zones are ordered from least trusted to most trusted:
    UNTRUSTED → BOUNDARY → INTERNAL → PRIVILEGED
    """
    UNTRUSTED = "untrusted"
    BOUNDARY = "boundary"
    INTERNAL = "internal"
    PRIVILEGED = "privileged"


# =============================================================================
# TRUST BOUNDARY DATACLASS
# =============================================================================

@dataclass(frozen=True)
class TrustBoundary:
    """
    Immutable definition of a trust boundary.
    
    Attributes:
        name: Human-readable name for this boundary
        from_zone: The zone being exited
        to_zone: The zone being entered
        requires_human_approval: Whether crossing requires human approval
    """
    name: str
    from_zone: TrustZone
    to_zone: TrustZone
    requires_human_approval: bool


# =============================================================================
# PREDEFINED BOUNDARIES
# =============================================================================

UNTRUSTED_TO_BOUNDARY: Final[TrustBoundary] = TrustBoundary(
    name="untrusted_to_boundary",
    from_zone=TrustZone.UNTRUSTED,
    to_zone=TrustZone.BOUNDARY,
    requires_human_approval=False
)
"""Boundary from untrusted sources into system boundary."""

BOUNDARY_TO_INTERNAL: Final[TrustBoundary] = TrustBoundary(
    name="boundary_to_internal",
    from_zone=TrustZone.BOUNDARY,
    to_zone=TrustZone.INTERNAL,
    requires_human_approval=False
)
"""Boundary from boundary into internal system."""

INTERNAL_TO_PRIVILEGED: Final[TrustBoundary] = TrustBoundary(
    name="internal_to_privileged",
    from_zone=TrustZone.INTERNAL,
    to_zone=TrustZone.PRIVILEGED,
    requires_human_approval=True  # Always requires human approval
)
"""Boundary into privileged operations. ALWAYS requires human approval."""


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_crossing(actor: Actor, boundary: TrustBoundary) -> bool:
    """
    Validate if an actor can cross a trust boundary.
    
    Rules:
    - Crossing to PRIVILEGED requires ADMINISTRATOR role
    - Crossing to INTERNAL requires OPERATOR or ADMINISTRATOR role
    - Crossing to BOUNDARY is allowed for all roles
    
    Args:
        actor: The actor attempting to cross
        boundary: The boundary to cross
    
    Returns:
        bool: True if crossing is allowed, False otherwise
    """
    target_zone = boundary.to_zone
    
    if target_zone == TrustZone.PRIVILEGED:
        return actor.role == Role.ADMINISTRATOR
    
    if target_zone == TrustZone.INTERNAL:
        return actor.role in (Role.OPERATOR, Role.ADMINISTRATOR)
    
    if target_zone == TrustZone.BOUNDARY:
        return True  # All roles can enter boundary zone
    
    return False


def can_cross_to_privileged(actor: Actor) -> bool:
    """
    Check if an actor can cross into privileged zone.
    
    Only ADMINISTRATOR role can access privileged operations.
    This still requires human approval at execution time.
    
    Args:
        actor: The actor to check
    
    Returns:
        bool: True if actor can cross to privileged, False otherwise
    """
    return actor.role == Role.ADMINISTRATOR


# =============================================================================
# END OF PHASE-03 TRUST
# =============================================================================
