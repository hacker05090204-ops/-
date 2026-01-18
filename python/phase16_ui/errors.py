"""
Phase-16 UI Error Types

All errors are display-only and do not imply verification or authority.
"""


class Phase16UIError(Exception):
    """Base error for Phase-16 UI layer."""
    pass


class UIGovernanceViolation(Phase16UIError):
    """
    Raised when UI code violates governance constraints.
    
    This error triggers HALT and requires human investigation.
    """
    pass


class UIRenderError(Phase16UIError):
    """Raised when UI rendering fails."""
    pass


class UIEventLogError(Phase16UIError):
    """Raised when UI event logging fails."""
    pass


class UIConfirmationError(Phase16UIError):
    """Raised when confirmation dialog fails."""
    pass
