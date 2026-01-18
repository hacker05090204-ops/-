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
Phase-12 Workflow State Management

Track 3 - TASK-3.1, TASK-3.2: Implement State Machine Transitions

This module implements:
- create_workflow(): Create new workflow in INITIALIZED state
- transition_state(): Transition workflow to new state
- is_valid_transition(): Check if transition is valid
- require_human_confirmation(): Check if human confirmation is required (always True)
- validate_human_confirmation(): Validate human confirmation token

CONSTRAINTS:
- STATE MANAGEMENT ONLY
- NO decision logic (no "should", "if allowed", "recommend")
- NO execution logic
- NO retry logic
- NO automation
- NO reasoning based on audit contents
- Audit data may NOT influence transitions
- Hash verification may NOT gate transitions
- All transitions require explicit human confirmation
- Fail-closed is mandatory

VALID TRANSITIONS:
- INITIALIZED -> AWAITING_HUMAN
- AWAITING_HUMAN -> HUMAN_CONFIRMED
- AWAITING_HUMAN -> FAILED
- HUMAN_CONFIRMED -> COMPLETED
- HUMAN_CONFIRMED -> FAILED
- Any state -> FAILED (fail-closed)

NO EXECUTION LOGIC - NO DECISION LOGIC
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Set, Tuple

from .errors import AutomationAttemptError, InvalidTransitionError
from .types import WorkflowState, WorkflowStatus


# =============================================================================
# CONSTANTS: Valid State Transitions
# =============================================================================

# Explicit finite set of valid transitions
# Format: (from_status, to_status)
VALID_TRANSITIONS: Set[Tuple[WorkflowStatus, WorkflowStatus]] = {
    # Normal flow
    (WorkflowStatus.INITIALIZED, WorkflowStatus.AWAITING_HUMAN),
    (WorkflowStatus.AWAITING_HUMAN, WorkflowStatus.HUMAN_CONFIRMED),
    (WorkflowStatus.HUMAN_CONFIRMED, WorkflowStatus.COMPLETED),
    # Fail paths (fail-closed)
    (WorkflowStatus.AWAITING_HUMAN, WorkflowStatus.FAILED),
    (WorkflowStatus.HUMAN_CONFIRMED, WorkflowStatus.FAILED),
    # Any state can transition to FAILED (fail-closed)
    (WorkflowStatus.INITIALIZED, WorkflowStatus.FAILED),
    (WorkflowStatus.COMPLETED, WorkflowStatus.FAILED),
}


# =============================================================================
# TASK-3.1: State Machine Transitions
# =============================================================================

def create_workflow(workflow_id: str, current_phase: str = "phase-12") -> WorkflowState:
    """
    Create a new workflow in INITIALIZED state.
    
    Args:
        workflow_id: Unique identifier for the workflow
        current_phase: Current phase identifier (default: "phase-12")
    
    Returns:
        New immutable WorkflowState in INITIALIZED status
    
    NO EXECUTION LOGIC - NO DECISION LOGIC
    """
    now = datetime.now(timezone.utc)
    
    return WorkflowState(
        workflow_id=workflow_id,
        current_phase=current_phase,
        status=WorkflowStatus.INITIALIZED,
        created_at=now,
        updated_at=now,
        human_confirmation_required=True,  # ALWAYS True - INV-5.1
        no_auto_action=True  # ALWAYS True - INV-5.1
    )


def is_valid_transition(
    from_status: WorkflowStatus,
    to_status: WorkflowStatus
) -> bool:
    """
    Check if a state transition is valid.
    
    This function performs a simple lookup in the VALID_TRANSITIONS set.
    It does NOT make decisions - it only reports validity.
    
    Args:
        from_status: Current workflow status
        to_status: Target workflow status
    
    Returns:
        True if transition is valid, False otherwise
    
    NO EXECUTION LOGIC - NO DECISION LOGIC
    """
    return (from_status, to_status) in VALID_TRANSITIONS


def transition_state(
    current_state: WorkflowState,
    new_status: WorkflowStatus,
    human_confirmation_token: str
) -> WorkflowState:
    """
    Transition workflow to a new state.
    
    This function:
    1. Validates the human confirmation token (required, non-empty)
    2. Validates the transition is allowed
    3. Returns a NEW immutable state (original unchanged)
    
    Args:
        current_state: Current workflow state
        new_status: Target workflow status
        human_confirmation_token: Human-provided confirmation token (required)
    
    Returns:
        New immutable WorkflowState with updated status
    
    Raises:
        AutomationAttemptError: If human_confirmation_token is empty or None
        InvalidTransitionError: If transition is not valid
    
    NO EXECUTION LOGIC - NO DECISION LOGIC
    """
    # Validate human confirmation token - REQUIRED, NON-EMPTY
    if not validate_human_confirmation(human_confirmation_token):
        raise AutomationAttemptError(
            "Human confirmation token is required and must be non-empty. "
            "Automation without human confirmation is forbidden."
        )
    
    # Validate transition
    if not is_valid_transition(current_state.status, new_status):
        raise InvalidTransitionError(
            f"Invalid transition: {current_state.status.value} -> {new_status.value}. "
            f"Workflow ID: {current_state.workflow_id}"
        )
    
    # Create new immutable state (original unchanged)
    return WorkflowState(
        workflow_id=current_state.workflow_id,
        current_phase=current_state.current_phase,
        status=new_status,
        created_at=current_state.created_at,
        updated_at=datetime.now(timezone.utc),
        human_confirmation_required=True,  # ALWAYS True - INV-5.1
        no_auto_action=True  # ALWAYS True - INV-5.1
    )


def transition_to_failed(
    current_state: WorkflowState,
    human_confirmation_token: str
) -> WorkflowState:
    """
    Transition workflow to FAILED state (fail-closed).
    
    Any state can transition to FAILED. This is the fail-closed mechanism.
    
    Args:
        current_state: Current workflow state
        human_confirmation_token: Human-provided confirmation token (required)
    
    Returns:
        New immutable WorkflowState with FAILED status
    
    Raises:
        AutomationAttemptError: If human_confirmation_token is empty or None
    
    NO EXECUTION LOGIC - NO DECISION LOGIC
    """
    return transition_state(current_state, WorkflowStatus.FAILED, human_confirmation_token)


# =============================================================================
# TASK-3.2: Human Confirmation Requirement
# =============================================================================

def require_human_confirmation(state: WorkflowState) -> bool:
    """
    Check if human confirmation is required for this state.
    
    This function ALWAYS returns True. Human confirmation is ALWAYS required.
    This is not a decision - it is a constant invariant.
    
    Args:
        state: Current workflow state
    
    Returns:
        True (always)
    
    NO EXECUTION LOGIC - NO DECISION LOGIC
    """
    # Human confirmation is ALWAYS required - INV-5.1
    # This is not a decision, it is a constant
    return True


def validate_human_confirmation(confirmation_token: str) -> bool:
    """
    Validate a human confirmation token.
    
    Validation rules:
    - Token must not be None
    - Token must not be empty string
    - Token must not be whitespace-only
    
    This function does NOT auto-generate tokens.
    This function does NOT make decisions about token validity beyond format.
    
    Args:
        confirmation_token: Human-provided confirmation token
    
    Returns:
        True if token is valid (non-empty), False otherwise
    
    NO EXECUTION LOGIC - NO DECISION LOGIC
    """
    if confirmation_token is None:
        return False
    
    if not isinstance(confirmation_token, str):
        return False
    
    # Token must be non-empty and not whitespace-only
    return len(confirmation_token.strip()) > 0
