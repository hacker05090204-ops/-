"""
Phase-5 Artifact Scanner

READ-ONLY artifact analysis module that consumes Phase-4 execution outputs
and produces signals and finding candidates for human review.

CRITICAL: This system assists humans. It does not autonomously hunt, judge, or earn.

NON-GOALS (FORBIDDEN):
- NO vulnerability classification (MCP's responsibility)
- NO severity assignment (human's responsibility)
- NO confidence scoring (MCP's responsibility)
- NO proof generation (MCP's responsibility)
- NO report submission (human's responsibility)
- NO execution triggering (Phase-4's responsibility)
- NO network requests (offline only)
- NO JavaScript execution (read-only analysis)
- NO action replay (read-only analysis)
- NO artifact modification (immutable input)
- NO artifact deletion (immutable input)
- NO MCP interaction (no direct communication)
- NO human approval bypass (all output requires human review)
"""

from artifact_scanner.types import (
    SignalType,
    Signal,
    FindingCandidate,
    ScanResult,
)
from artifact_scanner.errors import (
    ScannerError,
    ArtifactNotFoundError,
    ArtifactParseError,
    NoArtifactsError,
    ArchitecturalViolationError,
    ImmutabilityViolationError,
)
from artifact_scanner.scanner import Scanner
from artifact_scanner.loader import ArtifactLoader
from artifact_scanner.aggregator import SignalAggregator

__all__ = [
    # Main Scanner
    "Scanner",
    # Supporting classes
    "ArtifactLoader",
    "SignalAggregator",
    # Types
    "SignalType",
    "Signal",
    "FindingCandidate",
    "ScanResult",
    # Errors
    "ScannerError",
    "ArtifactNotFoundError",
    "ArtifactParseError",
    "NoArtifactsError",
    "ArchitecturalViolationError",
    "ImmutabilityViolationError",
]
