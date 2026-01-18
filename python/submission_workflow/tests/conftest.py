"""
Phase-7 Test Fixtures and Configuration

Provides common fixtures for testing the Human-Authorized Submission Workflow.
"""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import Generator
import uuid

import pytest
from hypothesis import settings, Verbosity

from submission_workflow.types import (
    Platform,
    SubmissionStatus,
    SubmissionAction,
    SubmissionRequest,
    SubmissionConfirmation,
    SubmissionAuditEntry,
    DraftReport,
)
from submission_workflow.audit import SubmissionAuditLogger
from submission_workflow.registry import ConfirmationRegistry
from submission_workflow.network import NetworkTransmitManager


# Configure hypothesis for Phase-7 tests
settings.register_profile(
    "phase7",
    max_examples=100,
    deadline=5000,
    verbosity=Verbosity.normal,
)
settings.load_profile("phase7")


@pytest.fixture
def audit_logger() -> SubmissionAuditLogger:
    """Create a fresh audit logger for testing."""
    return SubmissionAuditLogger()


@pytest.fixture
def registry(audit_logger: SubmissionAuditLogger) -> ConfirmationRegistry:
    """Create a fresh confirmation registry for testing."""
    return ConfirmationRegistry(audit_logger)


@pytest.fixture
def network_manager(
    audit_logger: SubmissionAuditLogger,
    registry: ConfirmationRegistry,
) -> NetworkTransmitManager:
    """Create a fresh network transmit manager for testing."""
    return NetworkTransmitManager(audit_logger, registry)


@pytest.fixture
def sample_draft() -> DraftReport:
    """Create a sample draft report for testing."""
    return DraftReport(
        draft_id=str(uuid.uuid4()),
        request_id=str(uuid.uuid4()),
        title="Test Vulnerability Report",
        description="This is a test vulnerability description.",
        severity="HIGH",
        classification="XSS",
        evidence_references=["https://example.com/evidence1"],
        custom_fields={"platform": "hackerone"},
    )


@pytest.fixture
def sample_confirmation(sample_draft: DraftReport) -> SubmissionConfirmation:
    """Create a sample valid confirmation for testing."""
    now = datetime.now()
    return SubmissionConfirmation(
        confirmation_id=str(uuid.uuid4()),
        request_id=sample_draft.request_id,
        submitter_id="test-submitter",
        report_hash=sample_draft.compute_hash(),  # Hash matches draft
        confirmed_at=now,
        expires_at=now + timedelta(minutes=15),
        submitter_signature="test-signature",
    )


@pytest.fixture
def expired_confirmation() -> SubmissionConfirmation:
    """Create an expired confirmation for testing."""
    past = datetime.now() - timedelta(hours=1)
    return SubmissionConfirmation(
        confirmation_id=str(uuid.uuid4()),
        request_id=str(uuid.uuid4()),
        submitter_id="test-submitter",
        report_hash="abc123hash",
        confirmed_at=past,
        expires_at=past + timedelta(minutes=15),  # Expired 45 minutes ago
        submitter_signature="test-signature",
    )


@pytest.fixture
def sample_request() -> SubmissionRequest:
    """Create a sample submission request for testing."""
    return SubmissionRequest(
        request_id=str(uuid.uuid4()),
        decision_id=str(uuid.uuid4()),
        finding_id=str(uuid.uuid4()),
        severity="HIGH",
        platform=Platform.HACKERONE,
        submitter_id="test-submitter",
        created_at=datetime.now(),
        status=SubmissionStatus.PENDING,
    )


def make_confirmation(
    confirmation_id: str | None = None,
    request_id: str | None = None,
    submitter_id: str = "test-submitter",
    expires_in_minutes: int = 15,
    report_hash: str = "test-hash",
) -> SubmissionConfirmation:
    """Factory function to create confirmations for testing."""
    now = datetime.now()
    return SubmissionConfirmation(
        confirmation_id=confirmation_id or str(uuid.uuid4()),
        request_id=request_id or str(uuid.uuid4()),
        submitter_id=submitter_id,
        report_hash=report_hash,
        confirmed_at=now,
        expires_at=now + timedelta(minutes=expires_in_minutes),
        submitter_signature="test-signature",
    )


def make_draft(
    draft_id: str | None = None,
    request_id: str | None = None,
    title: str = "Test Report",
    description: str = "Test description",
    severity: str = "HIGH",
) -> DraftReport:
    """Factory function to create draft reports for testing."""
    return DraftReport(
        draft_id=draft_id or str(uuid.uuid4()),
        request_id=request_id or str(uuid.uuid4()),
        title=title,
        description=description,
        severity=severity,
        classification="XSS",
        evidence_references=["https://example.com/evidence"],
        custom_fields={"platform": "hackerone"},
    )
