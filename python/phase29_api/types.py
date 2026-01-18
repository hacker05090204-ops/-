"""
Phase-29 API Types

GOVERNANCE:
- All types enforce human_initiated=True
- All response types include disclaimer
- Types are immutable (frozen dataclasses)
- NO scoring, ranking, or inference fields
"""

from dataclasses import dataclass, field
from typing import Optional, Any, Literal


# =============================================================================
# GOVERNANCE ERRORS
# =============================================================================


class GovernanceViolationError(Exception):
    """Raised when a governance rule is violated.
    
    GOVERNANCE: This error indicates automation or missing human_initiated.
    """
    pass


# =============================================================================
# REQUEST TYPES
# =============================================================================


@dataclass(frozen=True)
class InitiationMetadata:
    """Metadata about human initiation.
    
    GOVERNANCE: Tracks the human action that triggered the request.
    """
    timestamp: str
    element_id: str
    user_action: Literal["click", "submit", "keypress"]


@dataclass(frozen=True)
class SessionConfig:
    """Browser session configuration.
    
    GOVERNANCE: No automation flags allowed.
    """
    enable_video: bool = False
    viewport_width: int = 1280
    viewport_height: int = 720


@dataclass(frozen=True)
class BrowserAction:
    """Browser action to execute.
    
    GOVERNANCE: Actions are explicit, not automated.
    """
    action_type: Literal["navigate", "click", "scroll", "input_text", "screenshot", "wait", "hover"]
    target: str
    parameters: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# RESPONSE TYPES
# =============================================================================


@dataclass(frozen=True)
class BrowserStartResponse:
    """Response for POST /api/browser/start.
    
    GOVERNANCE: Includes human_initiated and disclaimer.
    """
    success: bool
    session_id: str
    execution_id: str
    started_at: str
    human_initiated: bool
    disclaimer: str


@dataclass(frozen=True)
class BrowserActionResponse:
    """Response for POST /api/browser/action.
    
    GOVERNANCE: Includes human_initiated and disclaimer.
    NO scoring, ranking, or interpretation fields.
    """
    success: bool
    action_id: str
    action_type: str
    executed_at: str
    result: dict[str, Any]
    human_initiated: bool
    disclaimer: str
    error: Optional[str] = None


@dataclass(frozen=True)
class EvidenceItem:
    """Single evidence item.
    
    GOVERNANCE: Read-only, no interpretation fields.
    """
    path: str
    captured_at: str
    label: str


@dataclass(frozen=True)
class EvidenceResponse:
    """Response for GET /api/browser/evidence.
    
    GOVERNANCE: Read-only evidence, includes disclaimer.
    NO interpretation, scoring, or recommendations.
    """
    success: bool
    session_id: str
    evidence: dict[str, Any]
    human_initiated: bool
    disclaimer: str


@dataclass(frozen=True)
class BrowserStopResponse:
    """Response for POST /api/browser/stop.
    
    GOVERNANCE: Includes human_initiated and disclaimer.
    """
    success: bool
    session_id: str
    stopped_at: str
    evidence_summary: dict[str, Any]
    human_initiated: bool
    disclaimer: str


@dataclass(frozen=True)
class BrowserStatusResponse:
    """Response for GET /api/browser/status.
    
    GOVERNANCE: Read-only status, includes disclaimer.
    """
    success: bool
    session_id: str
    status: Literal["active", "stopped", "error"]
    started_at: Optional[str]
    action_count: int
    human_initiated: bool
    disclaimer: str


@dataclass(frozen=True)
class ErrorResponse:
    """Error response.
    
    GOVERNANCE: Includes error code for governance violations.
    """
    success: Literal[False]
    error: str
    code: str


# =============================================================================
# DISCLAIMER CONSTANTS
# =============================================================================


DISCLAIMER_START = "NOT VERIFIED — Evidence capture only"
DISCLAIMER_ACTION = "NOT VERIFIED — Action executed, evidence captured"
DISCLAIMER_EVIDENCE = "NOT VERIFIED — Evidence is read-only, no interpretation provided"
DISCLAIMER_STOP = "NOT VERIFIED — Session stopped, evidence finalized"
DISCLAIMER_STATUS = "NOT VERIFIED — Status is read-only"
