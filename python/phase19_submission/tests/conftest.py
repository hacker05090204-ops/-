"""
Phase-19 Test Fixtures

GOVERNANCE: All fixtures enforce human-guided constraints.
"""

import pytest
from datetime import datetime
from typing import List

from ..types import (
    ExportFormat,
    Finding,
    ChecklistItem,
    SubmissionAction,
)


@pytest.fixture
def sample_findings() -> List[Finding]:
    """Sample findings for testing (alphabetically ordered)."""
    return [
        Finding(
            finding_id="FIND-001",
            title="Alpha Finding",
            description="Description for alpha finding",
        ),
        Finding(
            finding_id="FIND-002",
            title="Beta Finding",
            description="Description for beta finding",
        ),
        Finding(
            finding_id="FIND-003",
            title="Gamma Finding",
            description="Description for gamma finding",
        ),
    ]


@pytest.fixture
def sample_checklist_items() -> List[ChecklistItem]:
    """Sample checklist items (neutral language, no scoring)."""
    return [
        ChecklistItem(
            item_id="CHECK-001",
            description="Review finding details",
        ),
        ChecklistItem(
            item_id="CHECK-002",
            description="Prepare submission URL",
        ),
        ChecklistItem(
            item_id="CHECK-003",
            description="Export report",
        ),
    ]


@pytest.fixture
def forbidden_verification_words() -> List[str]:
    """Words that MUST NOT appear in exports."""
    return [
        "verified",
        "confirmed",
        "validated",
        "high confidence",
        "low confidence",
        "certain",
        "definitely",
        "proven",
        "authenticated",
        "approved",
    ]


@pytest.fixture
def forbidden_scoring_words() -> List[str]:
    """Words that indicate scoring/ranking (FORBIDDEN)."""
    return [
        "score",
        "rank",
        "priority",
        "severity",
        "critical",
        "high",
        "medium",
        "low",
        "important",
        "urgent",
        "recommended",
        "suggested",
    ]


@pytest.fixture
def allowed_export_formats() -> List[ExportFormat]:
    """Allowed export formats (static, non-executable)."""
    return [ExportFormat.PDF, ExportFormat.TXT, ExportFormat.MD]


@pytest.fixture
def forbidden_export_extensions() -> List[str]:
    """Forbidden export extensions."""
    return [
        ".html",
        ".htm",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".exe",
        ".sh",
        ".bat",
        ".py",
        ".rb",
    ]
