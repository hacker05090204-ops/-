"""
Phase-29 API Module

GOVERNANCE:
- CONNECTIVITY ONLY
- All endpoints require human_initiated=True
- NO automation, inference, or scoring
- NO background execution
- NO modification of frozen phases
"""

from phase29_api.types import (
    GovernanceViolationError,
    BrowserStartResponse,
    BrowserActionResponse,
    BrowserStopResponse,
    BrowserStatusResponse,
    EvidenceResponse,
    EvidenceItem,
    DISCLAIMER_START,
    DISCLAIMER_ACTION,
    DISCLAIMER_EVIDENCE,
    DISCLAIMER_STOP,
    DISCLAIMER_STATUS,
)
from phase29_api.validation import (
    validate_human_initiated,
    validate_session_id,
    validate_action,
)
from phase29_api.server import app

__all__ = [
    # Types
    "GovernanceViolationError",
    "BrowserStartResponse",
    "BrowserActionResponse",
    "BrowserStopResponse",
    "BrowserStatusResponse",
    "EvidenceResponse",
    "EvidenceItem",
    # Disclaimers
    "DISCLAIMER_START",
    "DISCLAIMER_ACTION",
    "DISCLAIMER_EVIDENCE",
    "DISCLAIMER_STOP",
    "DISCLAIMER_STATUS",
    # Validation
    "validate_human_initiated",
    "validate_session_id",
    "validate_action",
    # Server
    "app",
]
