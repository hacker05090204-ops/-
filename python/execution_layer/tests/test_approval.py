"""
Test Execution Layer Human Approval

Tests for token single-use, expiry, and batch approval.
"""

import pytest
from datetime import datetime, timezone, timedelta
from hypothesis import given, strategies as st, settings

from execution_layer.types import SafeActionType, SafeAction, ExecutionToken
from execution_layer.approval import (
    HumanApprovalHook,
    ApprovalRequest,
    BatchApprovalRequest,
)
from execution_layer.errors import (
    TokenExpiredError,
    TokenAlreadyUsedError,
    TokenMismatchError,
)


class TestApprovalRequest:
    """Test ApprovalRequest dataclass."""
    
    def test_create_request(self):
        """Should create approval request."""
        action = SafeAction(
            action_id="test-1",
            action_type=SafeActionType.NAVIGATE,
            target="https://example.com",
            parameters={},
            description="Test",
        )
        request = ApprovalRequest.create(action)
        assert request.request_id
        assert request.action == action
        assert not request.approved
        assert not request.rejected


class TestBatchApprovalRequest:
    """Test BatchApprovalRequest dataclass."""
    
    def test_create_batch_request(self):
        """Should create batch approval request."""
        actions = [
            SafeAction(
                action_id=f"test-{i}",
                action_type=SafeActionType.NAVIGATE,
                target=f"https://example{i}.com",
                parameters={},
                description=f"Test {i}",
            )
            for i in range(3)
        ]
        request = BatchApprovalRequest.create(actions)
        assert request.request_id
        assert len(request.actions) == 3
        assert not request.approved


class TestHumanApprovalHook:
    """Test HumanApprovalHook class."""
    
    @pytest.fixture
    def hook(self):
        return HumanApprovalHook()
    
    @pytest.fixture
    def action(self):
        return SafeAction(
            action_id="test-1",
            action_type=SafeActionType.NAVIGATE,
            target="https://example.com",
            parameters={},
            description="Test",
        )
    
    def test_request_approval(self, hook, action):
        """Should create approval request."""
        request = hook.request_approval(action)
        assert request.request_id
        assert request.action == action
    
    def test_approve_request(self, hook, action):
        """Should approve request and generate token."""
        request = hook.request_approval(action)
        token = hook.approve(request.request_id, "human-1")
        assert token.token_id
        assert token.approver_id == "human-1"
        assert request.approved
    
    def test_reject_request(self, hook, action):
        """Should reject request with reason."""
        request = hook.request_approval(action)
        hook.reject(request.request_id, "Not needed")
        assert request.rejected
        assert request.rejection_reason == "Not needed"
    
    def test_token_single_use(self, hook, action):
        """Token should be invalidated after use."""
        request = hook.request_approval(action)
        token = hook.approve(request.request_id, "human-1")
        
        # First validation should pass
        assert hook.validate_token(token, action)
        
        # Invalidate token
        hook.invalidate_token(token)
        
        # Second validation should fail
        with pytest.raises(TokenAlreadyUsedError):
            hook.validate_token(token, action)
    
    def test_token_expiry(self, hook, action):
        """Expired token should be rejected."""
        # Create expired token
        now = datetime.now(timezone.utc)
        token = ExecutionToken(
            token_id="test-token",
            approver_id="human-1",
            approved_at=now - timedelta(hours=1),
            action_hash=action.compute_hash(),
            expires_at=now - timedelta(minutes=30),
        )
        
        with pytest.raises(TokenExpiredError):
            hook.validate_token(token, action)
    
    def test_token_mismatch(self, hook, action):
        """Token for different action should be rejected."""
        request = hook.request_approval(action)
        token = hook.approve(request.request_id, "human-1")
        
        different_action = SafeAction(
            action_id="test-2",
            action_type=SafeActionType.CLICK,
            target="#button",
            parameters={},
            description="Different action",
        )
        
        with pytest.raises(TokenMismatchError):
            hook.validate_token(token, different_action)


class TestBatchApproval:
    """Test batch approval functionality."""
    
    @pytest.fixture
    def hook(self):
        return HumanApprovalHook()
    
    @pytest.fixture
    def actions(self):
        return [
            SafeAction(
                action_id=f"test-{i}",
                action_type=SafeActionType.NAVIGATE,
                target=f"https://example{i}.com",
                parameters={},
                description=f"Test {i}",
            )
            for i in range(3)
        ]
    
    def test_request_batch_approval(self, hook, actions):
        """Should create batch approval request."""
        request = hook.request_batch_approval(actions)
        assert request.request_id
        assert len(request.actions) == 3
    
    def test_approve_batch(self, hook, actions):
        """Should approve batch and generate batch token."""
        request = hook.request_batch_approval(actions)
        token = hook.approve(request.request_id, "human-1")
        assert token.is_batch
        assert token.batch_size == 3
    
    def test_batch_token_matches_actions(self, hook, actions):
        """Batch token should match the actions."""
        request = hook.request_batch_approval(actions)
        token = hook.approve(request.request_id, "human-1")
        assert token.matches_batch(actions)
    
    def test_batch_token_single_use(self, hook, actions):
        """Batch token should be single-use."""
        request = hook.request_batch_approval(actions)
        token = hook.approve(request.request_id, "human-1")
        
        # First validation should pass
        assert hook.validate_batch_token(token, actions)
        
        # Invalidate token
        hook.invalidate_token(token)
        
        # Second validation should fail
        with pytest.raises(TokenAlreadyUsedError):
            hook.validate_batch_token(token, actions)
    
    def test_batch_token_wrong_actions(self, hook, actions):
        """Batch token should not match different actions."""
        request = hook.request_batch_approval(actions)
        token = hook.approve(request.request_id, "human-1")
        
        different_actions = [
            SafeAction(
                action_id=f"different-{i}",
                action_type=SafeActionType.CLICK,
                target=f"#button{i}",
                parameters={},
                description=f"Different {i}",
            )
            for i in range(3)
        ]
        
        with pytest.raises(TokenMismatchError):
            hook.validate_batch_token(token, different_actions)
    
    def test_empty_batch_rejected(self, hook):
        """Empty batch should be rejected."""
        with pytest.raises(ValueError):
            hook.request_batch_approval([])
