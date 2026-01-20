"""
PHASE 03 — TRUST BOUNDARIES PACKAGE
2026 RE-IMPLEMENTATION

This package provides trust boundary definitions for the kali-mcp-toolkit system.

Usage:
    from phase03_trust import TrustZone, validate_crossing, INTERNAL_TO_PRIVILEGED
"""

from phase03_trust.trust import (
    # Enum
    TrustZone,
    # Dataclass
    TrustBoundary,
    # Predefined boundaries
    UNTRUSTED_TO_BOUNDARY,
    BOUNDARY_TO_INTERNAL,
    INTERNAL_TO_PRIVILEGED,
    # Functions
    validate_crossing,
    can_cross_to_privileged,
)

__all__ = [
    "TrustZone",
    "TrustBoundary",
    "UNTRUSTED_TO_BOUNDARY",
    "BOUNDARY_TO_INTERNAL",
    "INTERNAL_TO_PRIVILEGED",
    "validate_crossing",
    "can_cross_to_privileged",
]
