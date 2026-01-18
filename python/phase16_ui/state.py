"""
Phase-16 UI State Module

GOVERNANCE CONSTRAINT:
UI state MUST be declarative only — no inference or derivation.
No derived states like isImportant, isRecommended, priority.
No computed emphasis based on data content.

This module stores UI state WITHOUT:
- Computing importance
- Deriving priority
- Inferring relevance
- Calculating scores
- Determining severity
"""

from typing import Any, Optional
from dataclasses import dataclass, field


@dataclass
class UIState:
    """
    Declarative UI state container.
    
    Stores data exactly as received — no inference, no derivation.
    
    FORBIDDEN FIELDS (will never exist):
    - is_important, isImportant
    - is_recommended, isRecommended
    - priority, relevance, confidence
    - score, rank, severity
    - next_action, nextAction
    - suggested_step, suggestedStep
    """
    
    # Raw data storage — no transformation
    _data: dict[str, Any] = field(default_factory=dict)
    
    # Session tracking
    session_id: Optional[str] = None
    
    # UI visibility states (not content-derived)
    is_cve_panel_open: bool = False
    is_confirmation_open: bool = False
    is_evidence_preview_open: bool = False
    
    # Current view (not a recommendation)
    current_view: str = "default"
    
    def set_data(self, key: str, value: Any) -> None:
        """
        Store data without transformation or derivation.
        
        Args:
            key: Data key
            value: Data value (stored as-is)
        """
        # Store exactly as received — no inference
        self._data[key] = value
        # NO derived fields created
        # NO importance computed
        # NO priority derived
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """
        Retrieve data exactly as stored.
        
        Args:
            key: Data key
            default: Default value if key not found
            
        Returns:
            Stored value (unchanged)
        """
        return self._data.get(key, default)
    
    def clear_data(self, key: str) -> None:
        """Remove data by key."""
        self._data.pop(key, None)
    
    def clear_all(self) -> None:
        """Clear all stored data."""
        self._data.clear()
    
    def open_cve_panel(self) -> None:
        """Open CVE panel (UI state only)."""
        self.is_cve_panel_open = True
    
    def close_cve_panel(self) -> None:
        """Close CVE panel (UI state only)."""
        self.is_cve_panel_open = False
    
    def open_confirmation(self) -> None:
        """Open confirmation dialog (UI state only)."""
        self.is_confirmation_open = True
    
    def close_confirmation(self) -> None:
        """Close confirmation dialog (UI state only)."""
        self.is_confirmation_open = False
    
    def open_evidence_preview(self) -> None:
        """Open evidence preview (UI state only)."""
        self.is_evidence_preview_open = True
    
    def close_evidence_preview(self) -> None:
        """Close evidence preview (UI state only)."""
        self.is_evidence_preview_open = False
    
    def set_view(self, view: str) -> None:
        """
        Set current view (not a recommendation).
        
        Args:
            view: View name
        """
        self.current_view = view
