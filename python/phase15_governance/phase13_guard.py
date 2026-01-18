"""
Phase-15 Phase-13 Guard Module

Enforces Phase-13 read-only access. Blocks all mutations.

MANDATORY DECLARATION:
"Phase-15 may ONLY implement enforcement, validation, logging, and blocking."
"""

from typing import Optional

from phase15_governance.errors import GovernanceBlockedError
from phase15_governance.audit import log_event


# Actions that are allowed (read-only)
ALLOWED_ACTIONS = frozenset({"read", "observe", "reference", "consume"})

# Actions that are blocked (mutations)
BLOCKED_ACTIONS = frozenset({
    "write", "delete", "update", "modify",
    "append", "truncate", "overwrite", "remove",
})


def check_phase13_access(
    action: str,
    target: Optional[str] = None,
) -> bool:
    """
    Check if Phase-13 access is allowed.
    
    Args:
        action: Action type
        target: Target (must be phase13 for this guard)
    
    Returns:
        True if action is allowed
    
    Raises:
        GovernanceBlockedError: If action is blocked
    """
    # Log all Phase-13 interactions
    if action in ALLOWED_ACTIONS:
        log_event(
            event_type="phase13_interaction",
            data={"action": action, "target": target},
            attribution="SYSTEM",
        )
        return True
    
    # Block mutation actions
    if action in BLOCKED_ACTIONS:
        log_event(
            event_type="phase13_write_blocked",
            data={"action": action, "target": target, "reason": "phase13_immutable"},
            attribution="SYSTEM",
        )
        raise GovernanceBlockedError(f"Phase-13 is read-only: '{action}' is blocked")
    
    # Unknown actions are blocked by default
    log_event(
        event_type="phase13_write_blocked",
        data={"action": action, "target": target, "reason": "unknown_action_blocked"},
        attribution="SYSTEM",
    )
    raise GovernanceBlockedError(f"Unknown action '{action}' is blocked for Phase-13")
