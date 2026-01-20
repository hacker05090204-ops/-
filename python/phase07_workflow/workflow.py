"""
PHASE 07 — WORKFLOW STATE MACHINE
2026 RE-IMPLEMENTATION

Defines workflow states and transitions with human control points.

⚠️ CRITICAL: This is a 2026 RE-IMPLEMENTATION.

Document ID: GOV-PHASE07-2026-REIMPL-CODE
Date: 2026-01-20
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Final
import uuid


# =============================================================================
# WORKFLOW STATE ENUM
# =============================================================================

class WorkflowState(Enum):
    """States in a security workflow."""
    CREATED = "created"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    EXECUTING = "executing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# =============================================================================
# WORKFLOW INSTANCE
# =============================================================================

@dataclass
class WorkflowInstance:
    """
    A workflow instance tracking state and history.
    
    All state transitions require human approval at control points.
    """
    workflow_id: str
    name: str
    current_state: WorkflowState
    actor_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    history: list[str] = field(default_factory=list)


# =============================================================================
# STATE TRANSITION
# =============================================================================

@dataclass(frozen=True)
class StateTransition:
    """Definition of a valid state transition."""
    from_state: WorkflowState
    to_state: WorkflowState
    requires_human_approval: bool = True


# =============================================================================
# VALID TRANSITIONS
# =============================================================================

# All transitions that require human approval
VALID_TRANSITIONS: Final[list[StateTransition]] = [
    StateTransition(WorkflowState.CREATED, WorkflowState.PENDING_APPROVAL, True),
    StateTransition(WorkflowState.PENDING_APPROVAL, WorkflowState.APPROVED, True),
    StateTransition(WorkflowState.PENDING_APPROVAL, WorkflowState.CANCELLED, True),
    StateTransition(WorkflowState.APPROVED, WorkflowState.EXECUTING, True),
    StateTransition(WorkflowState.EXECUTING, WorkflowState.PAUSED, True),
    StateTransition(WorkflowState.EXECUTING, WorkflowState.COMPLETED, False),  # Automatic on success
    StateTransition(WorkflowState.EXECUTING, WorkflowState.FAILED, False),     # Automatic on failure
    StateTransition(WorkflowState.PAUSED, WorkflowState.EXECUTING, True),
    StateTransition(WorkflowState.PAUSED, WorkflowState.CANCELLED, True),
]


# =============================================================================
# WORKFLOW FUNCTIONS
# =============================================================================

def create_workflow(name: str, actor_id: str) -> WorkflowInstance:
    """Create a new workflow instance."""
    if not name or not name.strip():
        raise ValueError("name cannot be empty")
    if not actor_id or not actor_id.strip():
        raise ValueError("actor_id cannot be empty")
    
    return WorkflowInstance(
        workflow_id=str(uuid.uuid4()),
        name=name.strip(),
        current_state=WorkflowState.CREATED,
        actor_id=actor_id.strip(),
        history=[f"Created at {datetime.utcnow().isoformat()}"]
    )


def is_transition_valid(from_state: WorkflowState, to_state: WorkflowState) -> bool:
    """Check if a state transition is valid."""
    for transition in VALID_TRANSITIONS:
        if transition.from_state == from_state and transition.to_state == to_state:
            return True
    return False


def transition_requires_approval(from_state: WorkflowState, to_state: WorkflowState) -> bool:
    """Check if a transition requires human approval."""
    for transition in VALID_TRANSITIONS:
        if transition.from_state == from_state and transition.to_state == to_state:
            return transition.requires_human_approval
    return True  # Default: require approval for unknown transitions


def transition_workflow(
    workflow: WorkflowInstance,
    to_state: WorkflowState,
    approved: bool = False
) -> bool:
    """
    Attempt to transition a workflow to a new state.
    
    Returns True if transition succeeded, False otherwise.
    """
    if not is_transition_valid(workflow.current_state, to_state):
        return False
    
    if transition_requires_approval(workflow.current_state, to_state) and not approved:
        return False
    
    old_state = workflow.current_state
    workflow.current_state = to_state
    workflow.updated_at = datetime.utcnow()
    workflow.history.append(f"Transitioned from {old_state.value} to {to_state.value}")
    return True


def is_workflow_terminal(state: WorkflowState) -> bool:
    """Check if a workflow state is terminal (cannot transition further)."""
    return state in (WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED)


# =============================================================================
# END OF PHASE-07 WORKFLOW
# =============================================================================
