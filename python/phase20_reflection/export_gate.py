"""
Phase-20 Export Gate: Reflection Requirement for Export

Enforces reflection requirement before Phase-19 export.
Gate is PROCEDURAL only - does NOT analyze content.
"""

from .reflection_logger import has_reflection_for_session


def require_reflection_before_export(session_id: str) -> bool:
    """
    Check if reflection exists before allowing export.
    
    Args:
        session_id: UUID of the session.
        
    Returns:
        True if reflection (or decline) exists, False otherwise.
        
    Note:
        - This is a PROCEDURAL check only
        - It does NOT analyze reflection content
        - It does NOT score reflection quality
        - It does NOT require minimum length
        - It does NOT require keywords
        - Decline counts as valid reflection
    """
    return has_reflection_for_session(session_id)


# NO validate_reflection_quality function exists
# NO require_minimum_length function exists
# NO require_keywords function exists
# NO block_based_on_content function exists
