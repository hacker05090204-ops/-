"""
Phase-15 Validator Module

Validates inputs against static constraints only.
This module does NOT make decisions or score inputs.

MANDATORY DECLARATION:
"Phase-15 may ONLY implement enforcement, validation, logging, and blocking."
"""

from typing import Any, Optional

from phase15_governance.errors import ValidationError


def validate_input(
    value: Any,
    constraint: Optional[dict[str, Any]],
) -> bool:
    """
    Validate input against a static constraint.
    
    Args:
        value: Value to validate
        constraint: Static constraint definition (required)
    
    Returns:
        True if valid
    
    Raises:
        ValueError: If constraint is None or dynamic
        ValidationError: If validation fails
    """
    if constraint is None:
        raise ValueError("constraint is required")
    
    # Reject dynamic constraints (functions)
    if callable(constraint):
        raise ValueError("constraint must be static, not dynamic")
    
    if not isinstance(constraint, dict):
        raise ValueError("constraint must be static dict")
    
    constraint_type = constraint.get("type")
    
    if constraint_type == "string":
        if not isinstance(value, str):
            raise ValidationError("value must be a string")
        
        max_length = constraint.get("max_length")
        if max_length is not None and len(value) > max_length:
            raise ValidationError(f"value exceeds max_length of {max_length}")
    
    return True
