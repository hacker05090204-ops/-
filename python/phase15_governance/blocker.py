"""
Phase-15 Blocker Module

Blocks prohibited actions. Does NOT decide, allow, or permit.

MANDATORY DECLARATION:
"Phase-15 may ONLY implement enforcement, validation, logging, and blocking."
"""

from typing import Any, Optional

from phase15_governance.errors import GovernanceBlockedError
from phase15_governance.audit import log_event


def block_if_prohibited(
    action: Optional[str],
    target: Optional[str] = None,
    autonomous: bool = False,
    auto: bool = False,
    batch: bool = False,
    **kwargs: Any,
) -> None:
    """
    Block action if it is prohibited.
    
    Args:
        action: Action type (required)
        target: Target of action
        autonomous: If True, block
        auto: If True, block
        batch: If True, block
    
    Raises:
        ValueError: If action is None
        GovernanceBlockedError: If action is prohibited
    """
    if action is None:
        raise ValueError("action is required")
    
    # Block autonomous actions
    if autonomous:
        log_event(
            event_type="action_blocked",
            data={"action": action, "reason": "autonomous_blocked"},
            attribution="SYSTEM",
        )
        raise GovernanceBlockedError("Autonomous actions are blocked")
    
    # Block auto-execute
    if auto:
        log_event(
            event_type="action_blocked",
            data={"action": action, "reason": "auto_blocked"},
            attribution="SYSTEM",
        )
        raise GovernanceBlockedError("Auto-execute is blocked")

    # Block batch operations
    if batch:
        log_event(
            event_type="action_blocked",
            data={"action": action, "reason": "batch_blocked"},
            attribution="SYSTEM",
        )
        raise GovernanceBlockedError("Batch operations are blocked")
    
    # Block phase13 write
    if action == "write" and target == "phase13":
        log_event(
            event_type="action_blocked",
            data={"action": action, "target": target, "reason": "phase13_write_blocked"},
            attribution="SYSTEM",
        )
        raise GovernanceBlockedError("Write to phase13 is blocked")
    
    # Block scheduling
    if action == "schedule" and kwargs.get("background"):
        log_event(
            event_type="action_blocked",
            data={"action": action, "reason": "scheduling_blocked"},
            attribution="SYSTEM",
        )
        raise GovernanceBlockedError("Scheduling is blocked")
    
    # Block prohibited actions by name
    if action in ("learn", "optimize", "adapt"):
        log_event(
            event_type="action_blocked",
            data={"action": action, "reason": "prohibited_action"},
            attribution="SYSTEM",
        )
        raise GovernanceBlockedError(f"Action '{action}' is prohibited")
