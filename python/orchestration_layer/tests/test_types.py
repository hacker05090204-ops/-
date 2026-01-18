# PHASE-12 GOVERNANCE COMPLIANCE
# This module is part of Phase-12 (Runtime Orchestration Implementation)
#
# FORBIDDEN CAPABILITIES:
# - NO execution logic
# - NO decision logic
# - NO submission logic
# - NO network access
# - NO browser automation
# - NO friction wiring or execution
# - NO auto-approval
# - NO frozen phase modification
#
# MANDATORY DECLARATION:
# Phase-12 implements orchestration without altering execution,
# human authority, governance friction, or audit invariants.

"""
Phase-12 Track 1 Types Tests

TEST CATEGORY: Per-Track Tests - Track 1 (Priority: MEDIUM)
EXECUTION ORDER: 4 (After Property Tests)

Test IDs:
- TEST-T1-002: WorkflowStatus enum has all required values
- TEST-T1-003: OrchestrationEventType enum has all required values
- TEST-T1-004: WorkflowState is frozen dataclass
- TEST-T1-005: WorkflowState has human_confirmation_required=True
- TEST-T1-006: CrossPhaseCorrelation is frozen dataclass
- TEST-T1-007: OrchestrationAuditEntry is frozen dataclass
- TEST-T1-008: IntegrationReport is frozen dataclass
- TEST-T1-009: IntegrationReport has auto_submit_allowed=False
"""

import pytest
from dataclasses import FrozenInstanceError
from datetime import datetime

from orchestration_layer.types import (
    WorkflowStatus,
    OrchestrationEventType,
    WorkflowState,
    CrossPhaseCorrelation,
    OrchestrationAuditEntry,
    IntegrationReport,
)


# =============================================================================
# TEST-T1-002: WorkflowStatus Enum
# =============================================================================

@pytest.mark.track1
class TestWorkflowStatusEnum:
    """
    Test ID: TEST-T1-002
    Requirement: REQ-3.1.3
    """
    
    def test_has_initialized_status(self):
        """Verify INITIALIZED status exists."""
        assert WorkflowStatus.INITIALIZED.value == "initialized"
    
    def test_has_awaiting_human_status(self):
        """Verify AWAITING_HUMAN status exists."""
        assert WorkflowStatus.AWAITING_HUMAN.value == "awaiting_human"
    
    def test_has_human_confirmed_status(self):
        """Verify HUMAN_CONFIRMED status exists."""
        assert WorkflowStatus.HUMAN_CONFIRMED.value == "human_confirmed"
    
    def test_has_completed_status(self):
        """Verify COMPLETED status exists."""
        assert WorkflowStatus.COMPLETED.value == "completed"
    
    def test_has_failed_status(self):
        """Verify FAILED status exists."""
        assert WorkflowStatus.FAILED.value == "failed"


# =============================================================================
# TEST-T1-003: OrchestrationEventType Enum
# =============================================================================

@pytest.mark.track1
class TestOrchestrationEventTypeEnum:
    """
    Test ID: TEST-T1-003
    Requirement: REQ-3.4.3
    """
    
    def test_has_workflow_created_event(self):
        """Verify WORKFLOW_CREATED event type exists."""
        assert OrchestrationEventType.WORKFLOW_CREATED.value == "workflow_created"
    
    def test_has_state_transition_event(self):
        """Verify STATE_TRANSITION event type exists."""
        assert OrchestrationEventType.STATE_TRANSITION.value == "state_transition"
    
    def test_has_correlation_created_event(self):
        """Verify CORRELATION_CREATED event type exists."""
        assert OrchestrationEventType.CORRELATION_CREATED.value == "correlation_created"
    
    def test_has_report_generated_event(self):
        """Verify REPORT_GENERATED event type exists."""
        assert OrchestrationEventType.REPORT_GENERATED.value == "report_generated"
    
    def test_has_human_confirmation_received_event(self):
        """Verify HUMAN_CONFIRMATION_RECEIVED event type exists."""
        assert OrchestrationEventType.HUMAN_CONFIRMATION_RECEIVED.value == "human_confirmation_received"
    
    def test_has_error_occurred_event(self):
        """Verify ERROR_OCCURRED event type exists."""
        assert OrchestrationEventType.ERROR_OCCURRED.value == "error_occurred"


# =============================================================================
# TEST-T1-004, TEST-T1-005: WorkflowState Dataclass
# =============================================================================

@pytest.mark.track1
class TestWorkflowStateDataclass:
    """
    Test IDs: TEST-T1-004, TEST-T1-005
    Requirements: REQ-3.1.4, INV-5.1
    """
    
    def test_is_frozen_dataclass(self):
        """Verify WorkflowState is a frozen dataclass."""
        now = datetime.now()
        state = WorkflowState(
            workflow_id="test-123",
            current_phase="phase-12",
            status=WorkflowStatus.INITIALIZED,
            created_at=now,
            updated_at=now,
        )
        with pytest.raises(FrozenInstanceError):
            state.workflow_id = "modified"
    
    def test_human_confirmation_required_default_true(self):
        """Verify human_confirmation_required defaults to True."""
        now = datetime.now()
        state = WorkflowState(
            workflow_id="test-123",
            current_phase="phase-12",
            status=WorkflowStatus.INITIALIZED,
            created_at=now,
            updated_at=now,
        )
        assert state.human_confirmation_required is True
    
    def test_no_auto_action_default_true(self):
        """Verify no_auto_action defaults to True."""
        now = datetime.now()
        state = WorkflowState(
            workflow_id="test-123",
            current_phase="phase-12",
            status=WorkflowStatus.INITIALIZED,
            created_at=now,
            updated_at=now,
        )
        assert state.no_auto_action is True
    
    def test_has_required_fields(self):
        """Verify all required fields are present."""
        now = datetime.now()
        state = WorkflowState(
            workflow_id="test-123",
            current_phase="phase-12",
            status=WorkflowStatus.INITIALIZED,
            created_at=now,
            updated_at=now,
        )
        assert state.workflow_id == "test-123"
        assert state.current_phase == "phase-12"
        assert state.status == WorkflowStatus.INITIALIZED
        assert state.created_at == now
        assert state.updated_at == now


# =============================================================================
# TEST-T1-006: CrossPhaseCorrelation Dataclass
# =============================================================================

@pytest.mark.track1
class TestCrossPhaseCorrelationDataclass:
    """
    Test ID: TEST-T1-006
    Requirement: REQ-3.2.2
    """
    
    def test_is_frozen_dataclass(self):
        """Verify CrossPhaseCorrelation is a frozen dataclass."""
        now = datetime.now()
        correlation = CrossPhaseCorrelation(
            correlation_id="corr-123",
            phase_entries={"phase-4": "entry-1"},
            created_at=now,
        )
        with pytest.raises(FrozenInstanceError):
            correlation.correlation_id = "modified"
    
    def test_human_confirmation_required_default_true(self):
        """Verify human_confirmation_required defaults to True."""
        now = datetime.now()
        correlation = CrossPhaseCorrelation(
            correlation_id="corr-123",
            phase_entries={"phase-4": "entry-1"},
            created_at=now,
        )
        assert correlation.human_confirmation_required is True
    
    def test_no_auto_action_default_true(self):
        """Verify no_auto_action defaults to True."""
        now = datetime.now()
        correlation = CrossPhaseCorrelation(
            correlation_id="corr-123",
            phase_entries={"phase-4": "entry-1"},
            created_at=now,
        )
        assert correlation.no_auto_action is True
    
    def test_has_required_fields(self):
        """Verify all required fields are present."""
        now = datetime.now()
        entries = {"phase-4": "entry-1", "phase-5": "entry-2"}
        correlation = CrossPhaseCorrelation(
            correlation_id="corr-123",
            phase_entries=entries,
            created_at=now,
        )
        assert correlation.correlation_id == "corr-123"
        assert correlation.phase_entries == entries
        assert correlation.created_at == now


# =============================================================================
# TEST-T1-007: OrchestrationAuditEntry Dataclass
# =============================================================================

@pytest.mark.track1
class TestOrchestrationAuditEntryDataclass:
    """
    Test ID: TEST-T1-007
    Requirement: REQ-3.4.2
    """
    
    def test_is_frozen_dataclass(self):
        """Verify OrchestrationAuditEntry is a frozen dataclass."""
        now = datetime.now()
        entry = OrchestrationAuditEntry(
            entry_id="entry-123",
            timestamp=now,
            event_type=OrchestrationEventType.WORKFLOW_CREATED,
            workflow_id="wf-123",
            details={"key": "value"},
            previous_hash="abc123",
            entry_hash="def456",
        )
        with pytest.raises(FrozenInstanceError):
            entry.entry_id = "modified"
    
    def test_human_confirmation_required_default_true(self):
        """Verify human_confirmation_required defaults to True."""
        now = datetime.now()
        entry = OrchestrationAuditEntry(
            entry_id="entry-123",
            timestamp=now,
            event_type=OrchestrationEventType.WORKFLOW_CREATED,
            workflow_id="wf-123",
            details={},
            previous_hash="abc123",
            entry_hash="def456",
        )
        assert entry.human_confirmation_required is True
    
    def test_no_auto_action_default_true(self):
        """Verify no_auto_action defaults to True."""
        now = datetime.now()
        entry = OrchestrationAuditEntry(
            entry_id="entry-123",
            timestamp=now,
            event_type=OrchestrationEventType.WORKFLOW_CREATED,
            workflow_id="wf-123",
            details={},
            previous_hash="abc123",
            entry_hash="def456",
        )
        assert entry.no_auto_action is True
    
    def test_has_required_fields(self):
        """Verify all required fields are present."""
        now = datetime.now()
        entry = OrchestrationAuditEntry(
            entry_id="entry-123",
            timestamp=now,
            event_type=OrchestrationEventType.STATE_TRANSITION,
            workflow_id="wf-123",
            details={"from": "A", "to": "B"},
            previous_hash="abc123",
            entry_hash="def456",
        )
        assert entry.entry_id == "entry-123"
        assert entry.timestamp == now
        assert entry.event_type == OrchestrationEventType.STATE_TRANSITION
        assert entry.workflow_id == "wf-123"
        assert entry.details == {"from": "A", "to": "B"}
        assert entry.previous_hash == "abc123"
        assert entry.entry_hash == "def456"


# =============================================================================
# TEST-T1-008, TEST-T1-009: IntegrationReport Dataclass
# =============================================================================

@pytest.mark.track1
class TestIntegrationReportDataclass:
    """
    Test IDs: TEST-T1-008, TEST-T1-009
    Requirements: REQ-3.5.2, REQ-3.5.3
    """
    
    def test_is_frozen_dataclass(self):
        """Verify IntegrationReport is a frozen dataclass."""
        now = datetime.now()
        report = IntegrationReport(
            report_id="report-123",
            workflow_id="wf-123",
            generated_at=now,
            summary="Test summary",
            phase_summaries={"phase-4": "summary-4"},
            correlation_ids=["corr-1"],
        )
        with pytest.raises(FrozenInstanceError):
            report.report_id = "modified"
    
    def test_human_confirmation_required_default_true(self):
        """Verify human_confirmation_required defaults to True."""
        now = datetime.now()
        report = IntegrationReport(
            report_id="report-123",
            workflow_id="wf-123",
            generated_at=now,
            summary="Test summary",
            phase_summaries={},
            correlation_ids=[],
        )
        assert report.human_confirmation_required is True
    
    def test_no_auto_action_default_true(self):
        """Verify no_auto_action defaults to True."""
        now = datetime.now()
        report = IntegrationReport(
            report_id="report-123",
            workflow_id="wf-123",
            generated_at=now,
            summary="Test summary",
            phase_summaries={},
            correlation_ids=[],
        )
        assert report.no_auto_action is True
    
    def test_auto_submit_allowed_default_false(self):
        """Verify auto_submit_allowed defaults to False."""
        now = datetime.now()
        report = IntegrationReport(
            report_id="report-123",
            workflow_id="wf-123",
            generated_at=now,
            summary="Test summary",
            phase_summaries={},
            correlation_ids=[],
        )
        assert report.auto_submit_allowed is False
    
    def test_has_required_fields(self):
        """Verify all required fields are present."""
        now = datetime.now()
        report = IntegrationReport(
            report_id="report-123",
            workflow_id="wf-123",
            generated_at=now,
            summary="Test summary",
            phase_summaries={"phase-4": "summary-4", "phase-5": "summary-5"},
            correlation_ids=["corr-1", "corr-2"],
        )
        assert report.report_id == "report-123"
        assert report.workflow_id == "wf-123"
        assert report.generated_at == now
        assert report.summary == "Test summary"
        assert report.phase_summaries == {"phase-4": "summary-4", "phase-5": "summary-5"}
        assert report.correlation_ids == ["corr-1", "corr-2"]
