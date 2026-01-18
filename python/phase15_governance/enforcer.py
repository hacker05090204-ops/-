"""
Phase-15 Enforcer Module

Enforces pre-defined rules. Does NOT decide, recommend, or infer.

MANDATORY DECLARATION:
"Phase-15 may ONLY implement enforcement, validation, logging, and blocking."
"""

from typing import Any, Optional

from phase15_governance.errors import GovernanceBlockedError
from phase15_governance.audit import log_event


def enforce_rule(
    rule: Optional[dict[str, Any]],
    context: dict[str, Any],
) -> bool:
    """
    Enforce a pre-defined rule.
    
    Args:
        rule: Rule definition (required)
        context: Execution context
    
    Returns:
        True if rule allows action
    
    Raises:
        ValueError: If rule is None or human_initiated missing
        GovernanceBlockedError: If rule blocks action
    """
    if rule is None:
        raise ValueError("rule is required")
    
    # Require human initiation
    if "human_initiated" not in context:
        raise ValueError("human_initiated is required in context")
    
    if not context.get("human_initiated"):
        raise ValueError("human_initiated must be True")
    
    rule_type = rule.get("type")
    rule_target = rule.get("target")
    
    action = context.get("action")
    target = context.get("target")
    
    # Block write to phase13
    if rule_type == "block_write" and rule_target == "phase13":
        if action == "write" and target == "phase13":
            log_event(
                event_type="enforcement_block",
                data={"rule": rule, "context": context, "reason": "phase13_write_blocked"},
                attribution="SYSTEM",
            )
            raise GovernanceBlockedError("Write to phase13 is blocked")

    # Allow rule - just log and return
    if rule_type == "allow":
        log_event(
            event_type="enforcement_allow",
            data={"rule": rule, "context": context},
            attribution="SYSTEM",
        )
        return True
    
    return True
