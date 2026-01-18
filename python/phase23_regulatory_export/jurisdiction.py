"""
Phase-23 Jurisdiction: Human jurisdiction selection.

Jurisdiction is ALWAYS selected by human — NO auto-selection.
"""

from .types import JurisdictionSelection


# Static list of available jurisdictions (defined at build time)
_AVAILABLE_JURISDICTIONS: tuple[tuple[str, str], ...] = (
    ("US", "United States"),
    ("EU", "European Union"),
    ("UK", "United Kingdom"),
    ("CA", "Canada"),
    ("AU", "Australia"),
    ("OTHER", "Other / Not Listed"),
)


def get_available_jurisdictions() -> tuple[tuple[str, str], ...]:
    """
    Get available jurisdictions for selection.
    
    This is a STATIC list — no dynamic generation.
    
    Returns:
        Tuple of (code, name) pairs.
    """
    return _AVAILABLE_JURISDICTIONS


def select_jurisdiction(
    jurisdiction_code: str,
    jurisdiction_name: str,
    selected_by: str,
    timestamp: str,
) -> JurisdictionSelection:
    """
    Record human jurisdiction selection.
    
    This function:
    - Records human selection
    - Does NOT auto-select
    - Does NOT recommend
    - Does NOT interpret legal requirements
    - Always sets human_initiated=True
    - Always sets actor="HUMAN"
    
    Args:
        jurisdiction_code: Code of selected jurisdiction.
        jurisdiction_name: Name of selected jurisdiction.
        selected_by: Free-text identifier of selector (NOT verified).
        timestamp: ISO-8601 timestamp.
        
    Returns:
        Immutable JurisdictionSelection.
    """
    return JurisdictionSelection(
        jurisdiction_code=jurisdiction_code,
        jurisdiction_name=jurisdiction_name,
        selected_by=selected_by,
        timestamp=timestamp,
        human_initiated=True,  # ALWAYS True
        actor="HUMAN",  # ALWAYS "HUMAN"
    )

