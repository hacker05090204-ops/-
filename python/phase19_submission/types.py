"""
Phase-19 Types

GOVERNANCE CONSTRAINTS:
- No scoring types
- No ranking types
- No platform selection types
- No verification types
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class ExportFormat(Enum):
    """
    Allowed export formats.
    
    ALLOWED: PDF, TXT, MD (static, non-executable)
    FORBIDDEN: HTML with scripts, interactive formats, embeds
    """
    PDF = "pdf"
    TXT = "txt"
    MD = "md"


class SubmissionAction(Enum):
    """Actions that can be logged (all require human initiation)."""
    EXPORT_REPORT = "export_report"
    OPEN_URL = "open_url"
    CONFIRM_ACTION = "confirm_action"
    CHECK_ITEM = "check_item"


@dataclass(frozen=True)
class ChecklistItem:
    """
    A single checklist item.
    
    CONSTRAINTS:
    - No priority field
    - No score field
    - No severity field
    - No importance field
    - Neutral language only
    """
    item_id: str
    description: str
    # NO priority, score, severity, importance, or ranking fields


@dataclass(frozen=True)
class SubmissionLog:
    """
    Log entry for submission actions.
    
    CONSTRAINTS:
    - attribution MUST be "HUMAN"
    - No system attribution
    - No AI attribution
    """
    timestamp: datetime
    action: SubmissionAction
    attribution: str = "HUMAN"  # ALWAYS "HUMAN"
    details: str = ""
    
    def __post_init__(self):
        if self.attribution != "HUMAN":
            raise ValueError("Attribution MUST be 'HUMAN'")


@dataclass(frozen=True)
class Finding:
    """
    A finding for export.
    
    CONSTRAINTS:
    - No score field
    - No rank field
    - No priority field
    - No severity field
    - Alphabetical ordering only
    """
    finding_id: str
    title: str
    description: str
    # NO score, rank, priority, severity fields


@dataclass
class ExportRequest:
    """Request to export a report (requires human initiation)."""
    findings: List[Finding]
    export_format: ExportFormat
    human_initiated: bool = False  # MUST be True to proceed
    
    def __post_init__(self):
        if not self.human_initiated:
            raise ValueError("Export MUST be human-initiated")


@dataclass
class URLOpenRequest:
    """Request to open a URL (requires human confirmation)."""
    url: str  # Human-provided, no validation
    human_confirmed: bool = False  # MUST be True to proceed
    
    def __post_init__(self):
        if not self.human_confirmed:
            raise ValueError("URL open MUST be human-confirmed")


# FORBIDDEN TYPES (explicitly not defined):
# - Score
# - Rank
# - Priority
# - Severity
# - Platform
# - Suggestion
# - Validation
