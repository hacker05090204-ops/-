"""
Phase-16 UI & Human Interaction Layer

MANDATORY DECLARATION:
"Phase-16 must not introduce authority, verification, inference, autonomy, or automation.
Phase-16 is a HUMAN INTERFACE ONLY."

CRITICAL CONSTRAINT:
UI MUST NOT compute, infer, or emphasize any data based on content.

This module provides:
- UI rendering (display only)
- Human input capture (explicit clicks only)
- Mandatory disclaimers
- Phase-15 interface forwarding (human-initiated only)
- UI event logging (HUMAN attribution)

This module NEVER provides:
- Verification, confirmation, or validation
- Inference, scoring, ranking, or classification
- Automation, auto-navigation, or auto-submit
- Background operations, timers, or polling
- Recommendations, suggestions, or advice
"""

from phase16_ui.errors import Phase16UIError, UIGovernanceViolation
from phase16_ui.strings import UIStrings
from phase16_ui.state import UIState
from phase16_ui.renderer import UIRenderer
from phase16_ui.confirmation import ConfirmationDialog
from phase16_ui.cve_panel import CVEPanel
from phase16_ui.event_logger import UIEventLogger

__all__ = [
    "Phase16UIError",
    "UIGovernanceViolation",
    "UIStrings",
    "UIState",
    "UIRenderer",
    "ConfirmationDialog",
    "CVEPanel",
    "UIEventLogger",
]
