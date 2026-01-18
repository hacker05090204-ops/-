"""
Phase-19: Human-Guided Submission Preparation

MANDATORY DECLARATION:
Phase-19 is HUMAN-GUIDED SUBMISSION PREPARATION ONLY.
No automation, no scoring, no platform selection, no verification.

This module provides:
- Report export (read-only from Phase-15)
- URL opener (human click required)
- Static checklist (no scoring)
- Submission logger (human attribution)

PROHIBITED:
- Automatic submission
- Platform selection
- Scoring or ranking
- Verification language
- Background execution
- Phase-15 modification
"""

from .types import (
    ExportFormat,
    SubmissionAction,
    ChecklistItem,
    SubmissionLog,
)
from .exporter import ReportExporter
from .url_opener import URLOpener
from .checklist import SubmissionChecklist
from .submission_logger import SubmissionLogger

__all__ = [
    "ExportFormat",
    "SubmissionAction",
    "ChecklistItem",
    "SubmissionLog",
    "ReportExporter",
    "URLOpener",
    "SubmissionChecklist",
    "SubmissionLogger",
]
