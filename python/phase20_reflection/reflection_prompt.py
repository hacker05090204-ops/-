"""
Phase-20 Reflection Prompt: Static Prompt Display

Provides static, hardcoded prompt text for reflection.
NO suggestions. NO auto-complete. NO content generation.
"""

from dataclasses import dataclass


# Static disclaimer - NEVER generated, NEVER modified
_DISCLAIMER = """══════════════════════════════════════════════════════════
THIS REFLECTION IS NOT ANALYZED, NOT VERIFIED, NOT SCORED.
Write freely. Your words are recorded as-is for audit only.
══════════════════════════════════════════════════════════"""


@dataclass(frozen=True)
class ReflectionInput:
    """
    Container for reflection input from human.
    
    This is a simple container - NO validation, NO analysis.
    """
    
    session_id: str
    """Session ID for this reflection."""
    
    text: str
    """Raw text entered by human. NOT ANALYZED."""
    
    declined: bool
    """True if human chose to decline."""
    
    decline_reason: str
    """Reason for decline if declined, empty otherwise."""


def get_reflection_prompt() -> str:
    """
    Get the static reflection prompt with disclaimer.
    
    Returns:
        Static prompt text including NOT ANALYZED disclaimer.
        
    Note:
        This prompt is HARDCODED. It is NEVER generated.
        It contains NO suggestions, NO recommendations.
    """
    return _DISCLAIMER


def prompt_for_reflection(session_id: str) -> ReflectionInput:
    """
    Create a reflection input container for a session.
    
    This function creates an EMPTY container that will be
    populated by the UI layer with human input.
    
    Args:
        session_id: UUID of the current session.
        
    Returns:
        Empty ReflectionInput ready for human input.
        
    Note:
        This function does NOT prompt the user directly.
        It creates a container for the UI layer to use.
        The actual prompting is done by Phase-16 UI.
    """
    # Return empty container - UI will populate
    return ReflectionInput(
        session_id=session_id,
        text="",
        declined=False,
        decline_reason="",
    )
