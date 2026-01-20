"""
PHASE 09 — BROWSER INTERACTION ABSTRACTION
2026 RE-IMPLEMENTATION

Browser interaction abstractions for web security testing.
NO AUTOMATION. All browser interactions require human initiation.

Document ID: GOV-PHASE09-2026-REIMPL-CODE
Date: 2026-01-20
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class BrowserActionType(Enum):
    """Types of browser actions."""
    NAVIGATE = "navigate"
    CLICK = "click"
    INPUT = "input"
    SCREENSHOT = "screenshot"
    INSPECT = "inspect"


@dataclass(frozen=True)
class BrowserAction:
    """
    Definition of a browser action.
    
    NO AUTOMATION: All actions require human initiation.
    """
    action_id: str
    action_type: BrowserActionType
    target_selector: Optional[str] = None
    value: Optional[str] = None
    requires_human_initiation: bool = True  # ALWAYS True


@dataclass(frozen=True)
class BrowserState:
    """Current state of a browser session."""
    session_id: str
    current_url: str
    page_title: str = ""
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


def create_browser_action(
    action_type: BrowserActionType,
    target_selector: Optional[str] = None,
    value: Optional[str] = None
) -> BrowserAction:
    """Create a new browser action. Always requires human initiation."""
    return BrowserAction(
        action_id=str(uuid.uuid4()),
        action_type=action_type,
        target_selector=target_selector,
        value=value,
        requires_human_initiation=True  # ENFORCED
    )


def requires_human_initiation(action: BrowserAction) -> bool:
    """Check if action requires human initiation. ALWAYS returns True."""
    return True  # ALL browser actions require human initiation
