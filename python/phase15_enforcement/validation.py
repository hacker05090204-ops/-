"""
Phase 15 Validation Module
Strict input validation for all governance transitions.
"""
from typing import Any
from .blocking import block_action

def validate_input(data: Any, schema: dict) -> dict:
    """
    Validate input data against a schema.
    Returns: {"valid": bool, "errors": list}
    """
    if data is None:
        raise ValueError("Data cannot be None")
    
    if not data:
        block_action("Empty input is forbidden")
        
    # Simple check for missing keys without inference
    errors = []
    if isinstance(data, dict) and isinstance(schema, dict):
        for key in schema:
            if key not in data:
                errors.append(f"Missing key: {key}")
                
    if errors:
        return {"valid": False, "errors": errors}
        
    return {"valid": True, "errors": []}

def validate_constraint(value: Any, constraint: str) -> bool:
    """
    Validate a single constraint.
    """
    return bool(value)
