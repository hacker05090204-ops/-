"""
Execution Layer Human Approval Hook

Mandatory human approval before any execution.
Supports both single action and batch approval.

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import secrets

from execution_layer.types import (
    SafeAction,
    ExecutionToken,
    ExecutionBatch,
)
from execution_layer.errors import (
    HumanApprovalRequired,
    TokenExpiredError,
    TokenAlreadyUsedError,
    TokenMismatchError,
)


@dataclass
class ApprovalRequest:
    """Request for human approval of a single action."""
    request_id: str
    action: SafeAction
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    approved: bool = False
    rejected: bool = False
    rejection_reason: Optional[str] = None
    token: Optional[ExecutionToken] = None
    
    @staticmethod
    def create(action: SafeAction) -> "ApprovalRequest":
        return ApprovalRequest(
            request_id=secrets.token_urlsafe(16),
            action=action,
        )


@dataclass
class BatchApprovalRequest:
    """Request for human approval of multiple actions."""
    request_id: str
    actions: list[SafeAction]
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    approved: bool = False
    rejected: bool = False
    rejection_reason: Optional[str] = None
    token: Optional[ExecutionToken] = None
    
    @staticmethod
    def create(actions: list[SafeAction]) -> "BatchApprovalRequest":
        return BatchApprovalRequest(
            request_id=secrets.token_urlsafe(16),
            actions=actions,
        )


class HumanApprovalHook:
    """Mandatory human approval before any execution.
    
    RULES:
    - Every execution requires human approval
    - Tokens are ONE-TIME USE only
    - Tokens expire after short period
    - Tokens are bound to specific action(s)
    - Batch approval allowed for pre-validated safe actions
    """
    
    def __init__(self, default_validity_minutes: int = 15) -> None:
        self._default_validity = default_validity_minutes
        self._used_tokens: set[str] = set()
        self._pending_requests: dict[str, ApprovalRequest] = {}
        self._pending_batch_requests: dict[str, BatchApprovalRequest] = {}
    
    def request_approval(self, action: SafeAction) -> ApprovalRequest:
        """Request human approval for single action execution."""
        request = ApprovalRequest.create(action)
        self._pending_requests[request.request_id] = request
        return request
    
    def request_batch_approval(self, actions: list[SafeAction]) -> BatchApprovalRequest:
        """Request human approval for batch of actions."""
        if not actions:
            raise ValueError("Cannot request approval for empty action list")
        request = BatchApprovalRequest.create(actions)
        self._pending_batch_requests[request.request_id] = request
        return request
    
    def approve(
        self,
        request_id: str,
        approver_id: str,
        validity_minutes: Optional[int] = None,
    ) -> ExecutionToken:
        """Approve a pending request and generate token."""
        validity = validity_minutes or self._default_validity
        
        # Check single action requests
        if request_id in self._pending_requests:
            request = self._pending_requests[request_id]
            token = ExecutionToken.generate(
                approver_id=approver_id,
                action=request.action,
                validity_minutes=validity,
            )
            request.approved = True
            request.token = token
            return token
        
        # Check batch requests
        if request_id in self._pending_batch_requests:
            request = self._pending_batch_requests[request_id]
            token = ExecutionToken.generate_batch(
                approver_id=approver_id,
                actions=request.actions,
                validity_minutes=validity,
            )
            request.approved = True
            request.token = token
            return token
        
        raise ValueError(f"No pending request with ID '{request_id}'")
    
    def reject(self, request_id: str, reason: str) -> None:
        """Reject a pending request."""
        if request_id in self._pending_requests:
            request = self._pending_requests[request_id]
            request.rejected = True
            request.rejection_reason = reason
            return
        
        if request_id in self._pending_batch_requests:
            request = self._pending_batch_requests[request_id]
            request.rejected = True
            request.rejection_reason = reason
            return
        
        raise ValueError(f"No pending request with ID '{request_id}'")
    
    def validate_token(self, token: ExecutionToken, action: SafeAction) -> bool:
        """Validate token for single action execution.
        
        Raises:
            TokenExpiredError: If token has expired
            TokenAlreadyUsedError: If token was already used
            TokenMismatchError: If token doesn't match action
        """
        # Check if token was already used
        if token.token_id in self._used_tokens:
            raise TokenAlreadyUsedError(
                f"Token '{token.token_id}' has already been used — "
                f"request new approval"
            )
        
        # Check if token has expired
        if token.is_expired:
            raise TokenExpiredError(
                f"Token '{token.token_id}' has expired — request new approval"
            )
        
        # Check if token matches action
        if not token.matches_action(action):
            raise TokenMismatchError(
                f"Token does not match action — request new approval"
            )
        
        return True
    
    def validate_batch_token(
        self,
        token: ExecutionToken,
        actions: list[SafeAction],
    ) -> bool:
        """Validate token for batch execution.
        
        Raises:
            TokenExpiredError: If token has expired
            TokenAlreadyUsedError: If token was already used
            TokenMismatchError: If token doesn't match actions
        """
        # Check if token was already used
        if token.token_id in self._used_tokens:
            raise TokenAlreadyUsedError(
                f"Token '{token.token_id}' has already been used — "
                f"request new approval"
            )
        
        # Check if token has expired
        if token.is_expired:
            raise TokenExpiredError(
                f"Token '{token.token_id}' has expired — request new approval"
            )
        
        # Check if token matches batch
        if not token.matches_batch(actions):
            raise TokenMismatchError(
                f"Token does not match action batch — request new approval"
            )
        
        return True
    
    def invalidate_token(self, token: ExecutionToken) -> None:
        """Invalidate token after use (one-time only)."""
        self._used_tokens.add(token.token_id)
    
    def is_token_used(self, token: ExecutionToken) -> bool:
        """Check if token has been used."""
        return token.token_id in self._used_tokens
    
    def get_pending_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get pending single action request."""
        return self._pending_requests.get(request_id)
    
    def get_pending_batch_request(self, request_id: str) -> Optional[BatchApprovalRequest]:
        """Get pending batch request."""
        return self._pending_batch_requests.get(request_id)
