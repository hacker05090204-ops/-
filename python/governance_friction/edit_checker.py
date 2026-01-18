"""
Phase-10: Governance & Friction Layer - Forced Edit Checker

Requires human modification before acceptance.
Whitespace-only changes are NOT sufficient.
"""

import hashlib
from typing import Dict, Optional

from governance_friction.errors import ForcedEditViolation


class ForcedEditChecker:
    """
    Requires at least one meaningful edit before acceptance.
    
    SECURITY: This checker ensures humans cannot blindly accept
    generated content. It NEVER:
    - Auto-edits content
    - Suggests specific edits
    - Accepts whitespace-only changes
    - Bypasses the requirement
    """
    
    def __init__(self):
        """Initialize the forced edit checker."""
        self._registered_content: Dict[str, str] = {}  # decision_id -> original_hash
        self._original_content: Dict[str, str] = {}  # decision_id -> original_content
    
    def register_content(self, decision_id: str, original_content: str) -> str:
        """
        Register original content for edit tracking.
        
        Args:
            decision_id: Unique identifier for the decision
            original_content: The original content before editing
            
        Returns:
            Hash of the original content
        """
        content_hash = self._compute_hash(original_content)
        self._registered_content[decision_id] = content_hash
        self._original_content[decision_id] = original_content
        return content_hash
    
    def require_edit(self, decision_id: str, edited_content: str) -> bool:
        """
        Check if a meaningful edit was made.
        
        Args:
            decision_id: Unique identifier for the decision
            edited_content: The content after editing
            
        Returns:
            True if a meaningful edit was made
            
        Raises:
            KeyError: If decision_id not registered
            ForcedEditViolation: If no meaningful edit was made
        """
        original = self._original_content.get(decision_id)
        if original is None:
            raise KeyError(f"No content registered for decision: {decision_id}")
        
        # Check for identical content
        if original == edited_content:
            raise ForcedEditViolation(
                decision_id=decision_id,
                reason="Content is identical to original - no edit made"
            )
        
        # Check for whitespace-only changes
        if self._is_whitespace_only_change(original, edited_content):
            raise ForcedEditViolation(
                decision_id=decision_id,
                reason="Only whitespace changes detected - meaningful edit required"
            )
        
        return True
    
    def validate_edit(self, decision_id: str, edited_content: str) -> bool:
        """
        Validate that an edit was made (alias for require_edit).
        
        Args:
            decision_id: Unique identifier for the decision
            edited_content: The content after editing
            
        Returns:
            True if a meaningful edit was made
            
        Raises:
            KeyError: If decision_id not registered
            ForcedEditViolation: If no meaningful edit was made
        """
        return self.require_edit(decision_id, edited_content)
    
    def get_original_content(self, decision_id: str) -> Optional[str]:
        """
        Get the original content for a decision.
        
        Args:
            decision_id: Unique identifier for the decision
            
        Returns:
            Original content or None if not registered
        """
        return self._original_content.get(decision_id)
    
    def clear_registration(self, decision_id: str) -> None:
        """
        Clear the registration for a decision.
        
        Args:
            decision_id: Unique identifier for the decision
        """
        self._registered_content.pop(decision_id, None)
        self._original_content.pop(decision_id, None)
    
    def _compute_hash(self, content: str) -> str:
        """Compute SHA-256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _is_whitespace_only_change(self, original: str, edited: str) -> bool:
        """
        Check if the only changes are whitespace.
        
        Args:
            original: Original content
            edited: Edited content
            
        Returns:
            True if only whitespace changed
        """
        # Normalize whitespace and compare
        original_normalized = self._normalize_whitespace(original)
        edited_normalized = self._normalize_whitespace(edited)
        
        return original_normalized == edited_normalized
    
    def _normalize_whitespace(self, content: str) -> str:
        """
        Normalize whitespace in content.
        
        Replaces all whitespace sequences with single spaces and strips.
        """
        import re
        return re.sub(r'\s+', ' ', content).strip()
