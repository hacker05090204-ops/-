"""
Phase-29 API Validation

GOVERNANCE:
- Enforces human_initiated=True on all requests
- Rejects automation patterns
- NO background execution
- NO inference or scoring
"""

from typing import Any
from phase29_api.types import GovernanceViolationError


def validate_human_initiated(request_data: dict[str, Any]) -> None:
    """Validate that human_initiated is exactly True.
    
    GOVERNANCE: HARD FAIL if human_initiated is not boolean True.
    
    Args:
        request_data: Request body dictionary
        
    Raises:
        GovernanceViolationError: If human_initiated is not True
    """
    human_initiated = request_data.get("human_initiated")
    
    # STRICT CHECK: Must be exactly boolean True
    if human_initiated is not True:
        raise GovernanceViolationError(
            "GOVERNANCE VIOLATION: human_initiated=true required"
        )


def validate_session_id(request_data: dict[str, Any]) -> str:
    """Validate and extract session_id.
    
    Args:
        request_data: Request body dictionary
        
    Returns:
        session_id string
        
    Raises:
        ValueError: If session_id is missing or invalid
    """
    session_id = request_data.get("session_id")
    if not session_id or not isinstance(session_id, str):
        raise ValueError("session_id is required and must be a string")
    return session_id


def validate_action(action_data: dict[str, Any]) -> None:
    """Validate browser action data.
    
    GOVERNANCE: Actions must be explicit, not automated.
    
    Args:
        action_data: Action dictionary
        
    Raises:
        ValueError: If action is invalid
        GovernanceViolationError: If action appears automated
    """
    action_type = action_data.get("action_type")
    target = action_data.get("target")
    
    if not action_type:
        raise ValueError("action_type is required")
    
    if not target:
        raise ValueError("target is required")
    
    valid_types = {"navigate", "click", "scroll", "input_text", "screenshot", "wait", "hover"}
    if action_type not in valid_types:
        raise ValueError(f"Invalid action_type: {action_type}")
    
    # GOVERNANCE: Check for automation patterns in target
    automation_patterns = ["auto:", "script:", "eval:"]
    target_lower = target.lower()
    for pattern in automation_patterns:
        if pattern in target_lower:
            raise GovernanceViolationError(
                f"GOVERNANCE VIOLATION: Automation pattern detected in target: {pattern}"
            )


def validate_no_automation_metadata(metadata: dict[str, Any]) -> None:
    """Validate that initiation metadata doesn't indicate automation.
    
    GOVERNANCE: Reject requests that appear to be automated.
    
    Args:
        metadata: Initiation metadata dictionary
        
    Raises:
        GovernanceViolationError: If automation is detected
    """
    if not metadata:
        return
    
    user_action = metadata.get("user_action", "")
    element_id = metadata.get("element_id", "")
    
    # Check for automation indicators
    automation_indicators = [
        "auto",
        "script",
        "bot",
        "automated",
        "programmatic",
    ]
    
    for indicator in automation_indicators:
        if indicator in user_action.lower() or indicator in element_id.lower():
            raise GovernanceViolationError(
                f"GOVERNANCE VIOLATION: Automation indicator detected: {indicator}"
            )
