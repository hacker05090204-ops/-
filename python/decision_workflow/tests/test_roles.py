"""
Tests for Phase-6 Role Enforcement.

Feature: human-decision-workflow
Property 7: Operator Forbidden Actions
Property 8: Reviewer Permitted Actions
Validates: Requirements 9.2, 9.3, 9.4, 9.5, 9.6, 9.7
"""

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st
from datetime import datetime

from decision_workflow.types import Role, Action, ROLE_PERMISSIONS, ReviewSession
from decision_workflow.roles import RoleEnforcer
from decision_workflow.errors import InsufficientPermissionError


# ============================================================================
# Unit Tests
# ============================================================================

class TestRoleEnforcerBasic:
    """Basic unit tests for RoleEnforcer."""
    
    def test_get_allowed_actions_operator(self):
        """Operator should have limited permissions."""
        enforcer = RoleEnforcer()
        allowed = enforcer.get_allowed_actions(Role.OPERATOR)
        
        assert Action.VIEW_FINDINGS in allowed
        assert Action.MARK_REVIEWED in allowed
        assert Action.ADD_NOTE in allowed
        assert Action.DEFER in allowed
        assert Action.ESCALATE in allowed
        
        assert Action.APPROVE not in allowed
        assert Action.REJECT not in allowed
        assert Action.ASSIGN_SEVERITY not in allowed
    
    def test_get_allowed_actions_reviewer(self):
        """Reviewer should have all permissions."""
        enforcer = RoleEnforcer()
        allowed = enforcer.get_allowed_actions(Role.REVIEWER)
        
        # All actions should be allowed
        for action in Action:
            assert action in allowed
    
    def test_check_permission_operator_allowed(self, operator_session):
        """Operator should be allowed to perform operator actions."""
        enforcer = RoleEnforcer()
        
        # These should not raise
        enforcer.check_permission(operator_session, Action.VIEW_FINDINGS)
        enforcer.check_permission(operator_session, Action.MARK_REVIEWED)
        enforcer.check_permission(operator_session, Action.ADD_NOTE)
        enforcer.check_permission(operator_session, Action.DEFER)
        enforcer.check_permission(operator_session, Action.ESCALATE)
    
    def test_check_permission_operator_forbidden(self, operator_session):
        """Operator should be forbidden from reviewer-only actions."""
        enforcer = RoleEnforcer()
        
        with pytest.raises(InsufficientPermissionError) as exc_info:
            enforcer.check_permission(operator_session, Action.APPROVE)
        assert exc_info.value.role == Role.OPERATOR
        assert exc_info.value.action == Action.APPROVE
        
        with pytest.raises(InsufficientPermissionError):
            enforcer.check_permission(operator_session, Action.REJECT)
        
        with pytest.raises(InsufficientPermissionError):
            enforcer.check_permission(operator_session, Action.ASSIGN_SEVERITY)
    
    def test_check_permission_reviewer_all_allowed(self, reviewer_session):
        """Reviewer should be allowed to perform all actions."""
        enforcer = RoleEnforcer()
        
        for action in Action:
            # Should not raise
            enforcer.check_permission(reviewer_session, action)
    
    def test_can_perform_returns_bool(self, operator_session, reviewer_session):
        """can_perform should return bool without raising."""
        enforcer = RoleEnforcer()
        
        assert enforcer.can_perform(operator_session, Action.VIEW_FINDINGS) is True
        assert enforcer.can_perform(operator_session, Action.APPROVE) is False
        assert enforcer.can_perform(reviewer_session, Action.APPROVE) is True
    
    def test_is_operator(self, operator_session, reviewer_session):
        """is_operator should correctly identify operator sessions."""
        enforcer = RoleEnforcer()
        
        assert enforcer.is_operator(operator_session) is True
        assert enforcer.is_operator(reviewer_session) is False
    
    def test_is_reviewer(self, operator_session, reviewer_session):
        """is_reviewer should correctly identify reviewer sessions."""
        enforcer = RoleEnforcer()
        
        assert enforcer.is_reviewer(operator_session) is False
        assert enforcer.is_reviewer(reviewer_session) is True


# ============================================================================
# Property Tests
# ============================================================================

class TestOperatorForbiddenActions:
    """
    Feature: human-decision-workflow, Property 7: Operator Forbidden Actions
    
    For any session with Role.OPERATOR, attempting Action.ASSIGN_SEVERITY,
    Action.APPROVE, or Action.REJECT SHALL raise InsufficientPermissionError.
    
    Validates: Requirements 9.3, 9.5, 9.6, 9.7
    """
    
    @given(
        session_id=st.uuids().map(str),
        reviewer_id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N"))),
    )
    @settings(max_examples=100)
    def test_operator_cannot_approve(self, session_id: str, reviewer_id: str):
        """
        Property 7: Operator Forbidden Actions - APPROVE
        For any Operator session, attempting APPROVE raises InsufficientPermissionError.
        """
        session = ReviewSession(
            session_id=session_id,
            reviewer_id=reviewer_id,
            role=Role.OPERATOR,
            start_time=datetime.now(),
        )
        enforcer = RoleEnforcer()
        
        with pytest.raises(InsufficientPermissionError) as exc_info:
            enforcer.check_permission(session, Action.APPROVE)
        
        assert exc_info.value.role == Role.OPERATOR
        assert exc_info.value.action == Action.APPROVE
    
    @given(
        session_id=st.uuids().map(str),
        reviewer_id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N"))),
    )
    @settings(max_examples=100)
    def test_operator_cannot_reject(self, session_id: str, reviewer_id: str):
        """
        Property 7: Operator Forbidden Actions - REJECT
        For any Operator session, attempting REJECT raises InsufficientPermissionError.
        """
        session = ReviewSession(
            session_id=session_id,
            reviewer_id=reviewer_id,
            role=Role.OPERATOR,
            start_time=datetime.now(),
        )
        enforcer = RoleEnforcer()
        
        with pytest.raises(InsufficientPermissionError) as exc_info:
            enforcer.check_permission(session, Action.REJECT)
        
        assert exc_info.value.role == Role.OPERATOR
        assert exc_info.value.action == Action.REJECT
    
    @given(
        session_id=st.uuids().map(str),
        reviewer_id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N"))),
    )
    @settings(max_examples=100)
    def test_operator_cannot_assign_severity(self, session_id: str, reviewer_id: str):
        """
        Property 7: Operator Forbidden Actions - ASSIGN_SEVERITY
        For any Operator session, attempting ASSIGN_SEVERITY raises InsufficientPermissionError.
        """
        session = ReviewSession(
            session_id=session_id,
            reviewer_id=reviewer_id,
            role=Role.OPERATOR,
            start_time=datetime.now(),
        )
        enforcer = RoleEnforcer()
        
        with pytest.raises(InsufficientPermissionError) as exc_info:
            enforcer.check_permission(session, Action.ASSIGN_SEVERITY)
        
        assert exc_info.value.role == Role.OPERATOR
        assert exc_info.value.action == Action.ASSIGN_SEVERITY
    
    @given(
        session_id=st.uuids().map(str),
        reviewer_id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N"))),
        action=st.sampled_from([Action.APPROVE, Action.REJECT, Action.ASSIGN_SEVERITY]),
    )
    @settings(max_examples=100)
    def test_operator_forbidden_actions_combined(self, session_id: str, reviewer_id: str, action: Action):
        """
        Property 7: Operator Forbidden Actions - Combined
        For any Operator session and any forbidden action, InsufficientPermissionError is raised.
        """
        session = ReviewSession(
            session_id=session_id,
            reviewer_id=reviewer_id,
            role=Role.OPERATOR,
            start_time=datetime.now(),
        )
        enforcer = RoleEnforcer()
        
        with pytest.raises(InsufficientPermissionError):
            enforcer.check_permission(session, action)


class TestReviewerPermittedActions:
    """
    Feature: human-decision-workflow, Property 8: Reviewer Permitted Actions
    
    For any session with Role.REVIEWER, all actions in the Action enum
    SHALL be permitted (no InsufficientPermissionError raised).
    
    Validates: Requirements 9.2, 9.4
    """
    
    @given(
        session_id=st.uuids().map(str),
        reviewer_id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N"))),
        action=st.sampled_from(list(Action)),
    )
    @settings(max_examples=100)
    def test_reviewer_can_perform_any_action(self, session_id: str, reviewer_id: str, action: Action):
        """
        Property 8: Reviewer Permitted Actions
        For any Reviewer session and any action, no exception is raised.
        """
        session = ReviewSession(
            session_id=session_id,
            reviewer_id=reviewer_id,
            role=Role.REVIEWER,
            start_time=datetime.now(),
        )
        enforcer = RoleEnforcer()
        
        # Should not raise any exception
        enforcer.check_permission(session, action)
    
    @given(
        session_id=st.uuids().map(str),
        reviewer_id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N"))),
    )
    @settings(max_examples=100)
    def test_reviewer_permissions_superset_of_operator(self, session_id: str, reviewer_id: str):
        """
        Property 8: Reviewer Permitted Actions - Superset
        Reviewer permissions must be a superset of Operator permissions.
        """
        enforcer = RoleEnforcer()
        
        operator_perms = enforcer.get_allowed_actions(Role.OPERATOR)
        reviewer_perms = enforcer.get_allowed_actions(Role.REVIEWER)
        
        assert operator_perms.issubset(reviewer_perms)
        assert len(reviewer_perms) > len(operator_perms)


class TestOperatorAllowedActions:
    """
    Tests that Operators CAN perform their allowed actions.
    
    Validates: Requirements 9.2
    """
    
    @given(
        session_id=st.uuids().map(str),
        reviewer_id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N"))),
        action=st.sampled_from([
            Action.VIEW_FINDINGS,
            Action.MARK_REVIEWED,
            Action.ADD_NOTE,
            Action.DEFER,
            Action.ESCALATE,
        ]),
    )
    @settings(max_examples=100)
    def test_operator_allowed_actions(self, session_id: str, reviewer_id: str, action: Action):
        """
        For any Operator session and any allowed action, no exception is raised.
        """
        session = ReviewSession(
            session_id=session_id,
            reviewer_id=reviewer_id,
            role=Role.OPERATOR,
            start_time=datetime.now(),
        )
        enforcer = RoleEnforcer()
        
        # Should not raise any exception
        enforcer.check_permission(session, action)
