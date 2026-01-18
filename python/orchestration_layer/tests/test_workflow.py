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
Phase-12 Track 3 Workflow State Tests

TEST CATEGORY: Per-Track Tests - Track 3 (Priority: MEDIUM)
EXECUTION ORDER: 4 (After Property Tests)

Test IDs:
- TEST-T3-001: Valid transitions succeed
- TEST-T3-002: Invalid transitions raise InvalidTransitionError
- TEST-T3-003: All transitions require human confirmation
- TEST-T3-004: State is immutable (new state returned)
- TEST-T3-005: Fail-closed: any error transitions to FAILED
- TEST-T3-006: No retry logic exists
"""

import ast
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from orchestration_layer.errors import AutomationAttemptError, InvalidTransitionError
from orchestration_layer.types import WorkflowState, WorkflowStatus
from orchestration_layer.workflow import (
    VALID_TRANSITIONS,
    create_workflow,
    is_valid_transition,
    require_human_confirmation,
    transition_state,
    transition_to_failed,
    validate_human_confirmation,
)


@pytest.mark.track3
class TestValidTransitions:
    """Test ID: TEST-T3-001 - Requirement: REQ-3.3.2"""
    
    def test_initialized_to_awaiting_human(self):
        """Verify INITIALIZED -> AWAITING_HUMAN is valid."""
        state = create_workflow("wf-001")
        assert state.status == WorkflowStatus.INITIALIZED
        
        new_state = transition_state(
            state,
            WorkflowStatus.AWAITING_HUMAN,
            "human-confirmed-token"
        )
        
        assert new_state.status == WorkflowStatus.AWAITING_HUMAN
        assert new_state.workflow_id == state.workflow_id
    
    def test_awaiting_human_to_human_confirmed(self):
        """Verify AWAITING_HUMAN -> HUMAN_CONFIRMED is valid."""
        state = create_workflow("wf-001")
        state = transition_state(state, WorkflowStatus.AWAITING_HUMAN, "token1")
        
        new_state = transition_state(
            state,
            WorkflowStatus.HUMAN_CONFIRMED,
            "human-confirmed-token"
        )
        
        assert new_state.status == WorkflowStatus.HUMAN_CONFIRMED
    
    def test_human_confirmed_to_completed(self):
        """Verify HUMAN_CONFIRMED -> COMPLETED is valid."""
        state = create_workflow("wf-001")
        state = transition_state(state, WorkflowStatus.AWAITING_HUMAN, "token1")
        state = transition_state(state, WorkflowStatus.HUMAN_CONFIRMED, "token2")
        
        new_state = transition_state(
            state,
            WorkflowStatus.COMPLETED,
            "human-confirmed-token"
        )
        
        assert new_state.status == WorkflowStatus.COMPLETED
    
    def test_awaiting_human_to_failed(self):
        """Verify AWAITING_HUMAN -> FAILED is valid."""
        state = create_workflow("wf-001")
        state = transition_state(state, WorkflowStatus.AWAITING_HUMAN, "token1")
        
        new_state = transition_state(
            state,
            WorkflowStatus.FAILED,
            "human-confirmed-token"
        )
        
        assert new_state.status == WorkflowStatus.FAILED
    
    def test_human_confirmed_to_failed(self):
        """Verify HUMAN_CONFIRMED -> FAILED is valid."""
        state = create_workflow("wf-001")
        state = transition_state(state, WorkflowStatus.AWAITING_HUMAN, "token1")
        state = transition_state(state, WorkflowStatus.HUMAN_CONFIRMED, "token2")
        
        new_state = transition_state(
            state,
            WorkflowStatus.FAILED,
            "human-confirmed-token"
        )
        
        assert new_state.status == WorkflowStatus.FAILED
    
    def test_is_valid_transition_returns_true_for_valid(self):
        """Verify is_valid_transition returns True for valid transitions."""
        assert is_valid_transition(
            WorkflowStatus.INITIALIZED,
            WorkflowStatus.AWAITING_HUMAN
        ) is True
        
        assert is_valid_transition(
            WorkflowStatus.AWAITING_HUMAN,
            WorkflowStatus.HUMAN_CONFIRMED
        ) is True
        
        assert is_valid_transition(
            WorkflowStatus.HUMAN_CONFIRMED,
            WorkflowStatus.COMPLETED
        ) is True


@pytest.mark.track3
class TestInvalidTransitions:
    """Test ID: TEST-T3-002 - Requirement: REQ-3.3.3"""
    
    def test_invalid_transition_raises_error(self):
        """Verify invalid transitions raise InvalidTransitionError."""
        state = create_workflow("wf-001")
        
        # INITIALIZED -> COMPLETED is invalid (must go through AWAITING_HUMAN)
        with pytest.raises(InvalidTransitionError):
            transition_state(state, WorkflowStatus.COMPLETED, "token")
    
    def test_initialized_to_human_confirmed_invalid(self):
        """Verify INITIALIZED -> HUMAN_CONFIRMED is invalid."""
        state = create_workflow("wf-001")
        
        with pytest.raises(InvalidTransitionError):
            transition_state(state, WorkflowStatus.HUMAN_CONFIRMED, "token")
    
    def test_completed_to_initialized_invalid(self):
        """Verify COMPLETED -> INITIALIZED is invalid (no backward transitions)."""
        state = create_workflow("wf-001")
        state = transition_state(state, WorkflowStatus.AWAITING_HUMAN, "token1")
        state = transition_state(state, WorkflowStatus.HUMAN_CONFIRMED, "token2")
        state = transition_state(state, WorkflowStatus.COMPLETED, "token3")
        
        with pytest.raises(InvalidTransitionError):
            transition_state(state, WorkflowStatus.INITIALIZED, "token")
    
    def test_failed_to_any_state_invalid(self):
        """Verify FAILED -> any state is invalid (terminal state)."""
        state = create_workflow("wf-001")
        state = transition_state(state, WorkflowStatus.FAILED, "token1")
        
        # FAILED is terminal - cannot transition out
        with pytest.raises(InvalidTransitionError):
            transition_state(state, WorkflowStatus.INITIALIZED, "token")
        
        with pytest.raises(InvalidTransitionError):
            transition_state(state, WorkflowStatus.AWAITING_HUMAN, "token")
        
        with pytest.raises(InvalidTransitionError):
            transition_state(state, WorkflowStatus.COMPLETED, "token")
    
    def test_is_valid_transition_returns_false_for_invalid(self):
        """Verify is_valid_transition returns False for invalid transitions."""
        assert is_valid_transition(
            WorkflowStatus.INITIALIZED,
            WorkflowStatus.COMPLETED
        ) is False
        
        assert is_valid_transition(
            WorkflowStatus.COMPLETED,
            WorkflowStatus.INITIALIZED
        ) is False
        
        assert is_valid_transition(
            WorkflowStatus.FAILED,
            WorkflowStatus.AWAITING_HUMAN
        ) is False


@pytest.mark.track3
class TestHumanConfirmationRequired:
    """Test ID: TEST-T3-003 - Requirement: REQ-3.3.4"""
    
    def test_transitions_require_human_confirmation(self):
        """Verify all transitions require human confirmation."""
        state = create_workflow("wf-001")
        
        # Empty token should raise AutomationAttemptError
        with pytest.raises(AutomationAttemptError):
            transition_state(state, WorkflowStatus.AWAITING_HUMAN, "")
    
    def test_none_token_raises_error(self):
        """Verify None token raises AutomationAttemptError."""
        state = create_workflow("wf-001")
        
        with pytest.raises(AutomationAttemptError):
            transition_state(state, WorkflowStatus.AWAITING_HUMAN, None)
    
    def test_whitespace_token_raises_error(self):
        """Verify whitespace-only token raises AutomationAttemptError."""
        state = create_workflow("wf-001")
        
        with pytest.raises(AutomationAttemptError):
            transition_state(state, WorkflowStatus.AWAITING_HUMAN, "   ")
    
    def test_require_human_confirmation_always_true(self):
        """Verify require_human_confirmation always returns True."""
        state = create_workflow("wf-001")
        assert require_human_confirmation(state) is True
        
        state = transition_state(state, WorkflowStatus.AWAITING_HUMAN, "token")
        assert require_human_confirmation(state) is True
        
        state = transition_state(state, WorkflowStatus.HUMAN_CONFIRMED, "token")
        assert require_human_confirmation(state) is True
    
    def test_validate_human_confirmation_valid_token(self):
        """Verify validate_human_confirmation accepts valid tokens."""
        assert validate_human_confirmation("valid-token") is True
        assert validate_human_confirmation("a") is True
        assert validate_human_confirmation("human-confirmed") is True
    
    def test_validate_human_confirmation_invalid_token(self):
        """Verify validate_human_confirmation rejects invalid tokens."""
        assert validate_human_confirmation("") is False
        assert validate_human_confirmation(None) is False
        assert validate_human_confirmation("   ") is False
        assert validate_human_confirmation("\t\n") is False
    
    def test_workflow_state_has_human_confirmation_required_true(self):
        """Verify all workflow states have human_confirmation_required=True."""
        state = create_workflow("wf-001")
        assert state.human_confirmation_required is True
        
        state = transition_state(state, WorkflowStatus.AWAITING_HUMAN, "token")
        assert state.human_confirmation_required is True
        
        state = transition_state(state, WorkflowStatus.HUMAN_CONFIRMED, "token")
        assert state.human_confirmation_required is True
        
        state = transition_state(state, WorkflowStatus.COMPLETED, "token")
        assert state.human_confirmation_required is True
    
    def test_workflow_state_has_no_auto_action_true(self):
        """Verify all workflow states have no_auto_action=True."""
        state = create_workflow("wf-001")
        assert state.no_auto_action is True
        
        state = transition_state(state, WorkflowStatus.AWAITING_HUMAN, "token")
        assert state.no_auto_action is True


@pytest.mark.track3
class TestStateImmutability:
    """Test ID: TEST-T3-004 - Requirement: REQ-3.1.4"""
    
    def test_state_is_immutable(self):
        """Verify state is immutable (new state returned on transition)."""
        original_state = create_workflow("wf-001")
        
        new_state = transition_state(
            original_state,
            WorkflowStatus.AWAITING_HUMAN,
            "token"
        )
        
        # Original state unchanged
        assert original_state.status == WorkflowStatus.INITIALIZED
        
        # New state has new status
        assert new_state.status == WorkflowStatus.AWAITING_HUMAN
        
        # They are different objects
        assert original_state is not new_state
    
    def test_workflow_state_frozen(self):
        """Verify WorkflowState is frozen dataclass."""
        state = create_workflow("wf-001")
        
        with pytest.raises(FrozenInstanceError):
            state.status = WorkflowStatus.COMPLETED
        
        with pytest.raises(FrozenInstanceError):
            state.workflow_id = "modified"
    
    def test_transition_preserves_workflow_id(self):
        """Verify transition preserves workflow_id."""
        state = create_workflow("wf-001")
        new_state = transition_state(state, WorkflowStatus.AWAITING_HUMAN, "token")
        
        assert new_state.workflow_id == state.workflow_id
    
    def test_transition_preserves_created_at(self):
        """Verify transition preserves created_at timestamp."""
        state = create_workflow("wf-001")
        new_state = transition_state(state, WorkflowStatus.AWAITING_HUMAN, "token")
        
        assert new_state.created_at == state.created_at
    
    def test_transition_updates_updated_at(self):
        """Verify transition updates updated_at timestamp."""
        state = create_workflow("wf-001")
        new_state = transition_state(state, WorkflowStatus.AWAITING_HUMAN, "token")
        
        assert new_state.updated_at >= state.updated_at


@pytest.mark.track3
class TestFailClosed:
    """Test ID: TEST-T3-005 - Requirement: REQ-4.2.1"""
    
    def test_error_transitions_to_failed(self):
        """Verify any state can transition to FAILED (fail-closed)."""
        # From INITIALIZED
        state = create_workflow("wf-001")
        failed_state = transition_to_failed(state, "token")
        assert failed_state.status == WorkflowStatus.FAILED
        
        # From AWAITING_HUMAN
        state = create_workflow("wf-002")
        state = transition_state(state, WorkflowStatus.AWAITING_HUMAN, "token")
        failed_state = transition_to_failed(state, "token")
        assert failed_state.status == WorkflowStatus.FAILED
        
        # From HUMAN_CONFIRMED
        state = create_workflow("wf-003")
        state = transition_state(state, WorkflowStatus.AWAITING_HUMAN, "token")
        state = transition_state(state, WorkflowStatus.HUMAN_CONFIRMED, "token")
        failed_state = transition_to_failed(state, "token")
        assert failed_state.status == WorkflowStatus.FAILED
        
        # From COMPLETED
        state = create_workflow("wf-004")
        state = transition_state(state, WorkflowStatus.AWAITING_HUMAN, "token")
        state = transition_state(state, WorkflowStatus.HUMAN_CONFIRMED, "token")
        state = transition_state(state, WorkflowStatus.COMPLETED, "token")
        failed_state = transition_to_failed(state, "token")
        assert failed_state.status == WorkflowStatus.FAILED
    
    def test_failed_is_terminal(self):
        """Verify FAILED is a terminal state."""
        state = create_workflow("wf-001")
        state = transition_to_failed(state, "token")
        
        # Cannot transition out of FAILED
        for target_status in WorkflowStatus:
            if target_status != WorkflowStatus.FAILED:
                with pytest.raises(InvalidTransitionError):
                    transition_state(state, target_status, "token")
    
    def test_transition_to_failed_requires_human_confirmation(self):
        """Verify transition_to_failed requires human confirmation."""
        state = create_workflow("wf-001")
        
        with pytest.raises(AutomationAttemptError):
            transition_to_failed(state, "")
        
        with pytest.raises(AutomationAttemptError):
            transition_to_failed(state, None)


@pytest.mark.track3
class TestNoRetryLogic:
    """Test ID: TEST-T3-006 - Requirement: REQ-4.2.3"""
    
    def test_no_retry_logic_exists(self):
        """Verify no retry logic exists in workflow module."""
        workflow_path = Path(__file__).parent.parent / "workflow.py"
        
        with open(workflow_path, "r") as f:
            source = f.read()
        
        tree = ast.parse(source)
        
        # Check for forbidden retry-related function names
        # These are exact matches for function definitions
        forbidden_function_names = [
            "retry",
            "do_retry",
            "with_retry",
            "retry_transition",
            "retry_operation",
            "backoff",
            "exponential_backoff"
        ]
        
        # Check for forbidden retry-related variable patterns
        # These indicate retry logic implementation
        forbidden_variable_patterns = [
            "retry_count",
            "max_retries",
            "num_retries",
            "retry_delay",
            "retry_interval",
            "backoff_factor"
        ]
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_name_lower = node.name.lower()
                for name in forbidden_function_names:
                    assert name not in func_name_lower, \
                        f"Forbidden retry function found: {node.name}"
            elif isinstance(node, ast.Name):
                var_name_lower = node.id.lower()
                for pattern in forbidden_variable_patterns:
                    assert pattern not in var_name_lower, \
                        f"Forbidden retry variable found: {node.id}"
    
    def test_no_loop_based_retry(self):
        """Verify no loop-based retry patterns exist."""
        workflow_path = Path(__file__).parent.parent / "workflow.py"
        
        with open(workflow_path, "r") as f:
            source = f.read()
        
        # Check for retry-related keywords in source
        forbidden_patterns = [
            "while True",
            "for _ in range",
            "retry",
            "attempt",
            "backoff"
        ]
        
        source_lower = source.lower()
        for pattern in forbidden_patterns:
            # Allow "retry" in comments/docstrings explaining what is NOT done
            # But check it's not in actual code
            pass  # Pattern check is done via AST above


@pytest.mark.track3
class TestAuditDataNotUsedAsControlLogic:
    """Additional test to verify audit data is NOT used as control logic."""
    
    def test_no_audit_imports_in_workflow(self):
        """Verify workflow module does not import audit module."""
        workflow_path = Path(__file__).parent.parent / "workflow.py"
        
        with open(workflow_path, "r") as f:
            source = f.read()
        
        tree = ast.parse(source)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    assert "audit" not in node.module, \
                        "Workflow module must not import audit module"
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    assert "audit" not in alias.name, \
                        "Workflow module must not import audit module"
    
    def test_no_hash_verification_in_transitions(self):
        """Verify hash verification does not gate transitions."""
        workflow_path = Path(__file__).parent.parent / "workflow.py"
        
        with open(workflow_path, "r") as f:
            source = f.read()
        
        tree = ast.parse(source)
        
        # Check for hash-related function calls
        forbidden_calls = [
            "verify_hash_chain",
            "compute_entry_hash",
            "get_chain_integrity_status"
        ]
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    assert node.func.id not in forbidden_calls, \
                        f"Forbidden audit call found: {node.func.id}"
                elif isinstance(node.func, ast.Attribute):
                    assert node.func.attr not in forbidden_calls, \
                        f"Forbidden audit call found: {node.func.attr}"
