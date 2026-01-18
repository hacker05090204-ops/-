"""
Test Execution Layer Action Validation

Tests for SAFE_ACTIONS allow-list and FORBIDDEN_ACTIONS list.
"""

import pytest
from hypothesis import given, strategies as st, settings

from execution_layer.types import SafeActionType, ForbiddenActionType, SafeAction
from execution_layer.actions import (
    SAFE_ACTIONS,
    FORBIDDEN_ACTIONS,
    FORBIDDEN_KEYWORDS,
    ActionValidator,
)
from execution_layer.errors import UnsafeActionError, ForbiddenActionError


class TestSafeActionsList:
    """Test SAFE_ACTIONS allow-list."""
    
    def test_safe_actions_is_frozenset(self):
        """SAFE_ACTIONS should be immutable."""
        assert isinstance(SAFE_ACTIONS, frozenset)
    
    def test_safe_actions_contains_expected(self):
        """SAFE_ACTIONS should contain expected actions."""
        expected = {
            SafeActionType.NAVIGATE,
            SafeActionType.CLICK,
            SafeActionType.INPUT_TEXT,
            SafeActionType.SCROLL,
            SafeActionType.WAIT,
            SafeActionType.SCREENSHOT,
            SafeActionType.GET_TEXT,
            SafeActionType.GET_ATTRIBUTE,
            SafeActionType.HOVER,
            SafeActionType.SELECT_OPTION,
        }
        assert SAFE_ACTIONS == expected
    
    def test_safe_actions_count(self):
        """SAFE_ACTIONS should have exactly 10 actions."""
        assert len(SAFE_ACTIONS) == 10


class TestForbiddenActionsList:
    """Test FORBIDDEN_ACTIONS list."""
    
    def test_forbidden_actions_is_frozenset(self):
        """FORBIDDEN_ACTIONS should be immutable."""
        assert isinstance(FORBIDDEN_ACTIONS, frozenset)
    
    def test_forbidden_actions_contains_auth(self):
        """FORBIDDEN_ACTIONS should contain auth-related actions."""
        assert ForbiddenActionType.LOGIN in FORBIDDEN_ACTIONS
        assert ForbiddenActionType.AUTHENTICATE in FORBIDDEN_ACTIONS
        assert ForbiddenActionType.BYPASS_AUTH in FORBIDDEN_ACTIONS
    
    def test_forbidden_actions_contains_captcha(self):
        """FORBIDDEN_ACTIONS should contain CAPTCHA bypass."""
        assert ForbiddenActionType.BYPASS_CAPTCHA in FORBIDDEN_ACTIONS
    
    def test_forbidden_actions_contains_data_modification(self):
        """FORBIDDEN_ACTIONS should contain data modification actions."""
        assert ForbiddenActionType.MODIFY_DATA in FORBIDDEN_ACTIONS
        assert ForbiddenActionType.DELETE_DATA in FORBIDDEN_ACTIONS
    
    def test_forbidden_actions_contains_payment(self):
        """FORBIDDEN_ACTIONS should contain payment actions."""
        assert ForbiddenActionType.PAYMENT in FORBIDDEN_ACTIONS
        assert ForbiddenActionType.CHECKOUT in FORBIDDEN_ACTIONS


class TestActionValidator:
    """Test ActionValidator class."""
    
    @pytest.fixture
    def validator(self):
        return ActionValidator()
    
    def test_validate_safe_action(self, validator):
        """Should validate safe actions."""
        action = SafeAction(
            action_id="test-1",
            action_type=SafeActionType.NAVIGATE,
            target="https://example.com/products",
            parameters={},
            description="Navigate to products",
        )
        assert validator.validate(action) is True
    
    def test_reject_forbidden_keyword_password(self, validator):
        """Should reject actions with password in parameters."""
        action = SafeAction(
            action_id="test-1",
            action_type=SafeActionType.INPUT_TEXT,
            target="#input",
            parameters={"text": "password123"},
            description="Enter password",
        )
        with pytest.raises(ForbiddenActionError, match="forbidden keyword"):
            validator.validate(action)
    
    def test_reject_admin_path(self, validator):
        """Should reject actions targeting admin paths."""
        action = SafeAction(
            action_id="test-1",
            action_type=SafeActionType.NAVIGATE,
            target="https://example.com/admin/dashboard",
            parameters={},
            description="Navigate to admin",
        )
        with pytest.raises(ForbiddenActionError, match="admin path"):
            validator.validate(action)
    
    def test_reject_login_path(self, validator):
        """Should reject actions targeting login paths."""
        action = SafeAction(
            action_id="test-1",
            action_type=SafeActionType.NAVIGATE,
            target="https://example.com/login",
            parameters={},
            description="Navigate to login",
        )
        with pytest.raises(ForbiddenActionError, match="auth path"):
            validator.validate(action)
    
    def test_reject_checkout_path(self, validator):
        """Should reject actions targeting checkout paths."""
        action = SafeAction(
            action_id="test-1",
            action_type=SafeActionType.NAVIGATE,
            target="https://example.com/checkout",
            parameters={},
            description="Navigate to checkout",
        )
        with pytest.raises(ForbiddenActionError, match="payment path"):
            validator.validate(action)
    
    def test_is_safe_returns_bool(self, validator):
        """is_safe should return boolean without raising."""
        safe_action = SafeAction(
            action_id="test-1",
            action_type=SafeActionType.NAVIGATE,
            target="https://example.com/products",
            parameters={},
            description="Safe action",
        )
        unsafe_action = SafeAction(
            action_id="test-2",
            action_type=SafeActionType.NAVIGATE,
            target="https://example.com/admin",
            parameters={},
            description="Unsafe action",
        )
        assert validator.is_safe(safe_action) is True
        assert validator.is_safe(unsafe_action) is False


class TestForbiddenKeywords:
    """Test FORBIDDEN_KEYWORDS list."""
    
    def test_forbidden_keywords_is_frozenset(self):
        """FORBIDDEN_KEYWORDS should be immutable."""
        assert isinstance(FORBIDDEN_KEYWORDS, frozenset)
    
    def test_contains_sensitive_keywords(self):
        """Should contain sensitive keywords."""
        assert "password" in FORBIDDEN_KEYWORDS
        assert "secret" in FORBIDDEN_KEYWORDS
        assert "api_key" in FORBIDDEN_KEYWORDS
        assert "credit_card" in FORBIDDEN_KEYWORDS
        assert "ssn" in FORBIDDEN_KEYWORDS
