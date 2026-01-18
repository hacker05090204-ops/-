"""
Phase-9: Browser-Integrated Assisted Hunting Layer

An ASSISTIVE layer that reduces human workload to near-negligible effort
WITHOUT creating automation, autonomy, or submission authority.

This module provides:
- Browser observation (URLs, DOM context, navigation)
- Contextual hints and pattern reminders
- Duplicate warnings (non-blocking)
- Scope validation (read-only)
- Draft report generation (human must copy/edit/approve)

SAFETY CONSTRAINTS (NON-NEGOTIABLE):
- NO payload execution
- NO traffic injection
- NO request modification
- NO report submission
- NO severity assignment
- NO bug classification ("this is a bug")
- NO auto-confirmation
- NO auto-PoC generation
- NO auto-video recording
- NO auto-chaining of findings
- NO modification of human decisions

Human always clicks YES / NO.

PHASE BOUNDARIES:
- Phase-4 to Phase-7: READ-ONLY access
- Phase-8: ADVISORY-ONLY access
- NO network execution
- NO stealth/evasion/bypass logic

FORBIDDEN IMPORTS:
- execution_layer (Phase-4) - except types for read-only
- artifact_scanner (Phase-5) - except types for read-only
- httpx, requests, aiohttp, socket (Network execution)
"""

from .types import (
    # Enums
    HintType,
    HintSeverity,
    ObservationType,
    ConfirmationStatus,
    # Data models
    BrowserObservation,
    ContextHint,
    DuplicateHint,
    ScopeWarning,
    DraftReportContent,
    HumanConfirmation,
    AssistantOutput,
)

from .errors import (
    BrowserAssistantError,
    ArchitecturalViolationError,
    AutomationAttemptError,
    NetworkExecutionAttemptError,
    HumanConfirmationRequired,
    InvalidObservationError,
    ReadOnlyViolationError,
)

from .boundaries import Phase9BoundaryGuard

from .observer import BrowserObserver

from .context import ContextAnalyzer

from .duplicate_hint import DuplicateHintEngine

from .scope_check import ScopeChecker

from .draft_generator import DraftReportGenerator

from .confirmation import HumanConfirmationGate

from .assistant import BrowserAssistant


__all__ = [
    # Enums
    "HintType",
    "HintSeverity",
    "ObservationType",
    "ConfirmationStatus",
    # Data models
    "BrowserObservation",
    "ContextHint",
    "DuplicateHint",
    "ScopeWarning",
    "DraftReportContent",
    "HumanConfirmation",
    "AssistantOutput",
    # Errors
    "BrowserAssistantError",
    "ArchitecturalViolationError",
    "AutomationAttemptError",
    "NetworkExecutionAttemptError",
    "HumanConfirmationRequired",
    "InvalidObservationError",
    "ReadOnlyViolationError",
    # Components
    "Phase9BoundaryGuard",
    "BrowserObserver",
    "ContextAnalyzer",
    "DuplicateHintEngine",
    "ScopeChecker",
    "DraftReportGenerator",
    "HumanConfirmationGate",
    "BrowserAssistant",
]
