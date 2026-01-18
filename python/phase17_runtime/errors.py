"""
Phase-17 Runtime Errors

GOVERNANCE CONSTRAINT:
- Error types for runtime governance violations
- No intelligence, automation, or authority
"""


class RuntimeGovernanceViolation(Exception):
    """Base exception for runtime governance violations."""
    pass


class HeadlessModeViolation(RuntimeGovernanceViolation):
    """Raised when headless mode is attempted (prohibited)."""
    pass


class AutomationViolation(RuntimeGovernanceViolation):
    """Raised when automation is attempted (prohibited)."""
    pass


class BackgroundExecutionViolation(RuntimeGovernanceViolation):
    """Raised when background execution is attempted (prohibited)."""
    pass


class SilentStartupViolation(RuntimeGovernanceViolation):
    """Raised when silent startup is attempted (prohibited)."""
    pass


class SilentShutdownViolation(RuntimeGovernanceViolation):
    """Raised when silent shutdown is attempted (prohibited)."""
    pass


class UIModificationViolation(RuntimeGovernanceViolation):
    """Raised when UI modification is attempted (prohibited)."""
    pass


class Phase15ModificationViolation(RuntimeGovernanceViolation):
    """Raised when Phase-15 modification is attempted (prohibited)."""
    pass


class PackageManifestViolation(RuntimeGovernanceViolation):
    """Raised when package doesn't match manifest."""
    pass
