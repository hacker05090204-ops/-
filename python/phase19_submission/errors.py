"""
Phase-19 Errors

All errors relate to governance violations.
"""


class Phase19Error(Exception):
    """Base error for Phase-19."""
    pass


class HumanInitiationRequired(Phase19Error):
    """Raised when action attempted without human initiation."""
    pass


class HumanConfirmationRequired(Phase19Error):
    """Raised when action attempted without human confirmation."""
    pass


class ForbiddenExportFormat(Phase19Error):
    """Raised when attempting to export in forbidden format."""
    pass


class ForbiddenLanguageDetected(Phase19Error):
    """Raised when verification language detected in export."""
    pass


class Phase15ModificationAttempt(Phase19Error):
    """Raised when attempting to modify Phase-15 data."""
    pass


class ScoringAttempt(Phase19Error):
    """Raised when scoring or ranking is attempted."""
    pass


class AutomationAttempt(Phase19Error):
    """Raised when automation is detected."""
    pass


class BackgroundExecutionAttempt(Phase19Error):
    """Raised when background execution is detected."""
    pass
