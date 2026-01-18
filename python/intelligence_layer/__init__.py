"""
Phase-8: Read-Only Intelligence & Feedback Layer

A passive analytics module that provides insights from historical
decision and submission data. This module is strictly READ-ONLY
with NO network access, NO automation, and NO decision-making.

SAFETY CONSTRAINTS (NON-NEGOTIABLE):
- Network access PERMANENTLY DISABLED
- NO writes to Phase-6 or Phase-7 data
- NO automation of any kind
- NO validation of bugs
- NO recommendations
- NO predictions
- NO PoC generation
- NO CVE identification
- NO severity calculation
- NO prioritization
- NO ranking
- NO comparisons between reviewers
- Human remains FINAL AUTHORITY

All outputs include: "Human decision required"

FORBIDDEN IMPORTS (raise ArchitecturalViolationError):
- execution_layer (Phase-4)
- artifact_scanner (Phase-5)
- httpx, requests, aiohttp, socket, urllib.request (Network)
"""

from intelligence_layer.types import (
    # Enums
    InsightType,
    # Data models
    DuplicateWarning,
    SimilarFinding,
    AcceptancePattern,
    TargetProfile,
    PerformanceMetrics,
    PatternInsight,
    DataPoint,
    TimelineEntry,
)

from intelligence_layer.errors import (
    IntelligenceLayerError,
    ArchitecturalViolationError,
    NetworkAccessAttemptError,
    DataNotFoundError,
    InsufficientDataError,
    InvalidQueryError,
)

from intelligence_layer.boundaries import BoundaryGuard

from intelligence_layer.data_access import DataAccessLayer

from intelligence_layer.duplicate import DuplicateDetector

from intelligence_layer.acceptance import AcceptanceTracker

from intelligence_layer.target import TargetProfiler

from intelligence_layer.performance import PerformanceAnalyzer

from intelligence_layer.patterns import PatternEngine


__all__ = [
    # Enums
    "InsightType",
    # Data models
    "DuplicateWarning",
    "SimilarFinding",
    "AcceptancePattern",
    "TargetProfile",
    "PerformanceMetrics",
    "PatternInsight",
    "DataPoint",
    "TimelineEntry",
    # Errors
    "IntelligenceLayerError",
    "ArchitecturalViolationError",
    "NetworkAccessAttemptError",
    "DataNotFoundError",
    "InsufficientDataError",
    "InvalidQueryError",
    # Components
    "BoundaryGuard",
    "DataAccessLayer",
    "DuplicateDetector",
    "AcceptanceTracker",
    "TargetProfiler",
    "PerformanceAnalyzer",
    "PatternEngine",
]
