"""
Execution Layer Action Validation

Explicit SAFE ACTION allow-list and FORBIDDEN action list.
Actions not in SAFE_ACTIONS are rejected.
Actions in FORBIDDEN_ACTIONS cause HARD STOP.

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

from typing import FrozenSet
from execution_layer.types import SafeActionType, ForbiddenActionType, SafeAction
from execution_layer.errors import UnsafeActionError, ForbiddenActionError


# Explicit allow-list of safe actions
SAFE_ACTIONS: FrozenSet[SafeActionType] = frozenset({
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
})


# Explicit forbidden actions — HARD STOP
FORBIDDEN_ACTIONS: FrozenSet[ForbiddenActionType] = frozenset({
    ForbiddenActionType.LOGIN,
    ForbiddenActionType.AUTHENTICATE,
    ForbiddenActionType.CREATE_ACCOUNT,
    ForbiddenActionType.DELETE_ACCOUNT,
    ForbiddenActionType.MODIFY_DATA,
    ForbiddenActionType.DELETE_DATA,
    ForbiddenActionType.BYPASS_CAPTCHA,
    ForbiddenActionType.BYPASS_AUTH,
    ForbiddenActionType.SUBMIT_FORM,
    ForbiddenActionType.UPLOAD_FILE,
    ForbiddenActionType.DOWNLOAD_FILE,
    ForbiddenActionType.EXECUTE_SCRIPT,
    ForbiddenActionType.IMPERSONATE,
    ForbiddenActionType.ACCESS_ADMIN,
    ForbiddenActionType.PAYMENT,
    ForbiddenActionType.CHECKOUT,
})


# Keywords that indicate forbidden behavior in action parameters
FORBIDDEN_KEYWORDS: FrozenSet[str] = frozenset({
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "auth",
    "login",
    "signin",
    "signup",
    "register",
    "captcha",
    "recaptcha",
    "hcaptcha",
    "admin",
    "root",
    "sudo",
    "delete",
    "remove",
    "drop",
    "truncate",
    "payment",
    "checkout",
    "credit_card",
    "creditcard",
    "cvv",
    "ssn",
    "social_security",
})


class ActionValidator:
    """Validates actions against allow-list and forbidden list."""
    
    def __init__(self) -> None:
        self._safe_actions = SAFE_ACTIONS
        self._forbidden_actions = FORBIDDEN_ACTIONS
        self._forbidden_keywords = FORBIDDEN_KEYWORDS
    
    def validate(self, action: SafeAction) -> bool:
        """Validate action is safe to execute.
        
        Raises:
            ForbiddenActionError: If action is in FORBIDDEN_ACTIONS
            UnsafeActionError: If action is not in SAFE_ACTIONS
        """
        # Check if action type is forbidden
        self._check_forbidden_action_type(action)
        
        # Check if action type is in safe list
        self._check_safe_action_type(action)
        
        # Check parameters for forbidden keywords
        self._check_forbidden_keywords(action)
        
        # Check target for forbidden patterns
        self._check_forbidden_target(action)
        
        return True
    
    def _check_forbidden_action_type(self, action: SafeAction) -> None:
        """Check if action type matches any forbidden action."""
        action_type_str = action.action_type.value.lower()
        for forbidden in self._forbidden_actions:
            if forbidden.value.lower() in action_type_str:
                raise ForbiddenActionError(
                    f"Action type '{action.action_type.value}' matches forbidden "
                    f"action '{forbidden.value}' — HARD STOP"
                )
    
    def _check_safe_action_type(self, action: SafeAction) -> None:
        """Check if action type is in safe list."""
        if action.action_type not in self._safe_actions:
            raise UnsafeActionError(
                f"Action type '{action.action_type.value}' is not in "
                f"SAFE_ACTIONS allow-list — HARD STOP"
            )
    
    def _check_forbidden_keywords(self, action: SafeAction) -> None:
        """Check parameters for forbidden keywords."""
        params_str = str(action.parameters).lower()
        for keyword in self._forbidden_keywords:
            if keyword in params_str:
                raise ForbiddenActionError(
                    f"Action parameters contain forbidden keyword '{keyword}' — HARD STOP"
                )
    
    def _check_forbidden_target(self, action: SafeAction) -> None:
        """Check target URL/selector for forbidden patterns."""
        target_lower = action.target.lower()
        
        # Check for admin paths
        admin_patterns = ["/admin", "/wp-admin", "/administrator", "/backend"]
        for pattern in admin_patterns:
            if pattern in target_lower:
                raise ForbiddenActionError(
                    f"Target '{action.target}' contains admin path — HARD STOP"
                )
        
        # Check for auth paths
        auth_patterns = ["/login", "/signin", "/signup", "/register", "/auth"]
        for pattern in auth_patterns:
            if pattern in target_lower:
                raise ForbiddenActionError(
                    f"Target '{action.target}' contains auth path — HARD STOP"
                )
        
        # Check for payment paths
        payment_patterns = ["/checkout", "/payment", "/cart/checkout", "/pay"]
        for pattern in payment_patterns:
            if pattern in target_lower:
                raise ForbiddenActionError(
                    f"Target '{action.target}' contains payment path — HARD STOP"
                )
    
    def is_safe(self, action: SafeAction) -> bool:
        """Check if action is safe without raising exceptions."""
        try:
            self.validate(action)
            return True
        except (UnsafeActionError, ForbiddenActionError):
            return False
