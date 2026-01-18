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
Phase-12 Type Definitions

Track 1 - TASK-1.2 through TASK-1.7: Define Types

This module defines all enums and frozen dataclasses for Phase-12.
All dataclasses are frozen (immutable).
All dataclasses have human_confirmation_required=True by default.
All dataclasses have no_auto_action=True by default.

NO EXECUTION LOGIC - NO DECISION LOGIC
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List


# =============================================================================
# TASK-1.2: WorkflowStatus Enum
# =============================================================================

class WorkflowStatus(Enum):
    """
    Workflow status values for Phase-12 orchestration.
    
    Requirement: REQ-3.1.3
    """
    INITIALIZED = "initialized"
    AWAITING_HUMAN = "awaiting_human"
    HUMAN_CONFIRMED = "human_confirmed"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# TASK-1.3: OrchestrationEventType Enum
# =============================================================================

class OrchestrationEventType(Enum):
    """
    Event types for Phase-12 orchestration audit logging.
    
    Requirement: REQ-3.4.3
    """
    WORKFLOW_CREATED = "workflow_created"
    STATE_TRANSITION = "state_transition"
    CORRELATION_CREATED = "correlation_created"
    REPORT_GENERATED = "report_generated"
    HUMAN_CONFIRMATION_RECEIVED = "human_confirmation_received"
    ERROR_OCCURRED = "error_occurred"


# =============================================================================
# TASK-1.4: WorkflowState Frozen Dataclass
# =============================================================================

@dataclass(frozen=True)
class WorkflowState:
    """
    Immutable workflow state for Phase-12 orchestration.
    
    Requirements: REQ-3.1.1, REQ-3.1.2, REQ-3.1.4
    Invariant: INV-5.1 (human_confirmation_required always True)
    """
    workflow_id: str
    current_phase: str
    status: WorkflowStatus
    created_at: datetime
    updated_at: datetime
    human_confirmation_required: bool = True  # ALWAYS True - INV-5.1
    no_auto_action: bool = True  # ALWAYS True - INV-5.1


# =============================================================================
# TASK-1.5: CrossPhaseCorrelation Frozen Dataclass
# =============================================================================

@dataclass(frozen=True)
class CrossPhaseCorrelation:
    """
    Immutable cross-phase correlation for Phase-12 orchestration.
    
    Requirements: REQ-3.2.1, REQ-3.2.2
    Invariant: INV-5.1 (human_confirmation_required always True)
    """
    correlation_id: str
    phase_entries: Dict[str, str]  # phase_name -> audit_entry_id
    created_at: datetime
    human_confirmation_required: bool = True  # ALWAYS True - INV-5.1
    no_auto_action: bool = True  # ALWAYS True - INV-5.1


# =============================================================================
# TASK-1.6: OrchestrationAuditEntry Frozen Dataclass
# =============================================================================

@dataclass(frozen=True)
class OrchestrationAuditEntry:
    """
    Immutable audit entry for Phase-12 orchestration.
    
    Requirements: REQ-3.4.1, REQ-3.4.2
    Invariant: INV-5.1 (human_confirmation_required always True)
    Invariant: INV-5.2 (hash chain integrity)
    """
    entry_id: str
    timestamp: datetime
    event_type: OrchestrationEventType
    workflow_id: str
    details: Dict[str, Any]
    previous_hash: str
    entry_hash: str
    human_confirmation_required: bool = True  # ALWAYS True - INV-5.1
    no_auto_action: bool = True  # ALWAYS True - INV-5.1


# =============================================================================
# TASK-1.7: IntegrationReport Frozen Dataclass
# =============================================================================

@dataclass(frozen=True)
class IntegrationReport:
    """
    Immutable integration report for Phase-12 orchestration.
    
    Requirements: REQ-3.5.1, REQ-3.5.2
    Invariant: INV-5.1 (human_confirmation_required always True)
    Constraint: auto_submit_allowed is ALWAYS False
    """
    report_id: str
    workflow_id: str
    generated_at: datetime
    summary: str
    phase_summaries: Dict[str, str]
    correlation_ids: List[str]
    human_confirmation_required: bool = True  # ALWAYS True - INV-5.1
    no_auto_action: bool = True  # ALWAYS True - INV-5.1
    auto_submit_allowed: bool = False  # ALWAYS False - REQ-3.5.3
