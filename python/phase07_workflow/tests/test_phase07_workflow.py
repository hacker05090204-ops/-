"""PHASE 07 TESTS — 2026 RE-IMPLEMENTATION"""

import pytest


class TestWorkflowStateEnum:
    def test_exists(self):
        from phase07_workflow import WorkflowState
        assert WorkflowState is not None

    def test_has_states(self):
        from phase07_workflow import WorkflowState
        assert hasattr(WorkflowState, 'CREATED')
        assert hasattr(WorkflowState, 'PENDING_APPROVAL')
        assert hasattr(WorkflowState, 'APPROVED')
        assert hasattr(WorkflowState, 'EXECUTING')
        assert hasattr(WorkflowState, 'COMPLETED')


class TestWorkflowInstance:
    def test_exists(self):
        from phase07_workflow import WorkflowInstance
        assert WorkflowInstance is not None


class TestCreateWorkflow:
    def test_create_workflow(self):
        from phase07_workflow import create_workflow, WorkflowState
        wf = create_workflow("Test Workflow", "actor-001")
        assert wf.name == "Test Workflow"
        assert wf.current_state == WorkflowState.CREATED

    def test_validates_name(self):
        from phase07_workflow import create_workflow
        with pytest.raises(ValueError):
            create_workflow("", "actor-001")

    def test_validates_actor_id(self):
        from phase07_workflow import create_workflow
        with pytest.raises(ValueError):
            create_workflow("Test", "")


class TestTransitionValidation:
    def test_valid_transition(self):
        from phase07_workflow import is_transition_valid, WorkflowState
        assert is_transition_valid(WorkflowState.CREATED, WorkflowState.PENDING_APPROVAL) is True

    def test_invalid_transition(self):
        from phase07_workflow import is_transition_valid, WorkflowState
        assert is_transition_valid(WorkflowState.CREATED, WorkflowState.COMPLETED) is False


class TestTransitionRequiresApproval:
    def test_most_transitions_require_approval(self):
        from phase07_workflow import transition_requires_approval, WorkflowState
        assert transition_requires_approval(WorkflowState.PENDING_APPROVAL, WorkflowState.APPROVED) is True
        assert transition_requires_approval(WorkflowState.APPROVED, WorkflowState.EXECUTING) is True


class TestTransitionWorkflow:
    def test_transition_without_approval_fails(self):
        from phase07_workflow import create_workflow, transition_workflow, WorkflowState
        wf = create_workflow("Test", "actor-001")
        # Transition to PENDING_APPROVAL requires approval
        result = transition_workflow(wf, WorkflowState.PENDING_APPROVAL, approved=False)
        assert result is False  # Should fail without approval

    def test_transition_with_approval_succeeds(self):
        from phase07_workflow import create_workflow, transition_workflow, WorkflowState
        wf = create_workflow("Test", "actor-001")
        result = transition_workflow(wf, WorkflowState.PENDING_APPROVAL, approved=True)
        assert result is True
        assert wf.current_state == WorkflowState.PENDING_APPROVAL


class TestIsWorkflowTerminal:
    def test_completed_is_terminal(self):
        from phase07_workflow import is_workflow_terminal, WorkflowState
        assert is_workflow_terminal(WorkflowState.COMPLETED) is True
        assert is_workflow_terminal(WorkflowState.FAILED) is True
        assert is_workflow_terminal(WorkflowState.CANCELLED) is True

    def test_executing_is_not_terminal(self):
        from phase07_workflow import is_workflow_terminal, WorkflowState
        assert is_workflow_terminal(WorkflowState.EXECUTING) is False


class TestPackageExports:
    def test_all_exports(self):
        from phase07_workflow import (
            WorkflowState, WorkflowInstance, StateTransition,
            VALID_TRANSITIONS, create_workflow, is_transition_valid
        )
        assert all([WorkflowState, WorkflowInstance, StateTransition])
