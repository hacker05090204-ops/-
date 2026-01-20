"""
PHASE 01 — CORE CONSTANTS
2026 RE-IMPLEMENTATION

This module defines the foundational constants, identities, and invariants
for the kali-mcp-toolkit system.

⚠️ CRITICAL NOTICE:
    This is a 2026 RE-IMPLEMENTATION.
    This is NOT a recovery of lost code.
    This is NOT a claim of historical behavior.

Document ID: GOV-PHASE01-2026-REIMPL-CODE
Date: 2026-01-20
Status: IMPLEMENTED
"""

from typing import Final
import uuid

# =============================================================================
# SYSTEM IDENTITY CONSTANTS
# =============================================================================

SYSTEM_ID: Final[str] = "550e8400-e29b-41d4-a716-446655440001"
"""Unique identifier for this kali-mcp-toolkit instance."""

SYSTEM_NAME: Final[str] = "kali-mcp-toolkit"
"""Official name of the system."""

REIMPLEMENTATION_DATE: Final[str] = "2026-01-20"
"""Date of this 2026 re-implementation."""


# =============================================================================
# VERSION INFORMATION
# =============================================================================

VERSION: Final[str] = "1.0.0"
"""Semantic version string for the 2026 re-implementation."""

VERSION_TUPLE: Final[tuple[int, int, int]] = (1, 0, 0)
"""Version as a tuple (major, minor, patch)."""


# =============================================================================
# CORE INVARIANTS
# These rules must NEVER be violated by any phase in the system.
# =============================================================================

INVARIANT_HUMAN_AUTHORITY: Final[bool] = True
"""
All security-impacting operations MUST be authorized by a human.
No automated decision-making is permitted for exploit execution.
"""

INVARIANT_NO_AUTO_EXPLOIT: Final[bool] = True
"""
The system MUST NOT automatically execute exploits.
All exploitation requires explicit human initiation.
"""

INVARIANT_AUDIT_REQUIRED: Final[bool] = True
"""
All operations MUST produce an audit trail.
No silent operations are permitted.
"""

INVARIANT_NO_SCORING: Final[bool] = True
"""
The system MUST NOT score, rank, or prioritize vulnerabilities automatically.
Risk assessment is a human responsibility.
"""


# =============================================================================
# SECURITY CONSTANTS
# =============================================================================

MAX_OPERATION_TIMEOUT_SECONDS: Final[int] = 300
"""Maximum timeout for any single operation (5 minutes)."""

REQUIRE_HUMAN_CONFIRMATION: Final[bool] = True
"""All destructive or security-impacting operations require human confirmation."""


# =============================================================================
# GOVERNANCE MARKERS
# =============================================================================

GOVERNANCE_VERSION: Final[str] = "2026.1"
"""Version of the governance framework."""

REIMPLEMENTATION_MARKER: Final[str] = "REIMPL-2026"
"""Marker identifying this as a 2026 re-implementation."""


# =============================================================================
# END OF PHASE-01 CONSTANTS
# =============================================================================
