"""
Phase-15 Governance Errors

Error types for Phase-15 governance enforcement.
These are blocking errors only - no decision-making.

MANDATORY DECLARATION:
"Phase-15 may ONLY implement enforcement, validation, logging, and blocking."
"""


class GovernanceError(Exception):
    """Base error for governance violations."""
    pass


class GovernanceBlockedError(GovernanceError):
    """Raised when an action is blocked by governance rules."""
    pass


class ValidationError(GovernanceError):
    """Raised when input validation fails against static constraints."""
    pass


class IntegrityError(GovernanceError):
    """Raised when audit integrity check fails."""
    pass


class Phase13WriteError(GovernanceBlockedError):
    """Raised when write to Phase-13 is attempted."""
    pass
