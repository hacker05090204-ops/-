"""
Phase-5 Scanner Error Hierarchy

All errors that cause HARD STOP are marked as such.
HARD STOP means: refuse to proceed, log the violation, alert human.

This system assists humans. It does not autonomously hunt, judge, or earn.
"""


class ScannerError(Exception):
    """Base error for Scanner."""
    pass


class ArtifactNotFoundError(ScannerError):
    """Artifact file not found — continue with available artifacts.
    
    This is NOT a HARD STOP — scanner continues with available artifacts.
    """
    pass


class ArtifactParseError(ScannerError):
    """Artifact failed to parse — continue with available artifacts.
    
    This is NOT a HARD STOP — scanner continues with available artifacts.
    """
    pass


class NoArtifactsError(ScannerError):
    """No artifacts available — cannot proceed.
    
    This is a HARD STOP — scanner cannot produce any results.
    """
    pass


class ArchitecturalViolationError(ScannerError):
    """Attempted forbidden action — HARD STOP.
    
    This error is raised when Scanner is asked to:
    - Classify vulnerabilities (MCP's responsibility)
    - Assign severity (human's responsibility)
    - Compute confidence scores (MCP's responsibility)
    - Generate proofs (MCP's responsibility)
    - Submit reports (human's responsibility)
    - Trigger executions (Phase-4's responsibility)
    - Make network requests (offline only)
    - Execute JavaScript (read-only analysis)
    - Replay actions (read-only analysis)
    - Modify artifacts (immutable input)
    - Delete artifacts (immutable input)
    """
    pass


class ImmutabilityViolationError(ScannerError):
    """Artifact was modified during scan — HARD STOP.
    
    This error is raised when:
    - File hash before scan != file hash after scan
    - Artifact content was altered during analysis
    """
    pass


# Error classification for handling
HARD_STOP_ERRORS = (
    NoArtifactsError,
    ArchitecturalViolationError,
    ImmutabilityViolationError,
)

RECOVERABLE_ERRORS = (
    ArtifactNotFoundError,
    ArtifactParseError,
)


def is_hard_stop(error: Exception) -> bool:
    """Check if error requires HARD STOP."""
    return isinstance(error, HARD_STOP_ERRORS)


def is_recoverable(error: Exception) -> bool:
    """Check if error can be recovered from (continue with partial results)."""
    return isinstance(error, RECOVERABLE_ERRORS)
