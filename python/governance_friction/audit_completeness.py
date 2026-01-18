"""
Phase-10: Governance & Friction Layer - Audit Completeness Checker

Ensures complete audit records exist before any confirmation proceeds.
"""

from typing import Dict, Set, List

from governance_friction.types import AuditCompleteness
from governance_friction.errors import AuditIncomplete


class AuditCompletenessChecker:
    """
    Validates audit trail completeness before any confirmation.
    
    SECURITY: This checker ensures all decisions are traceable.
    It NEVER:
    - Auto-populates missing fields
    - Proceeds with incomplete trails
    - Bypasses the requirement
    """
    
    # Required audit items for a complete trail
    REQUIRED_ITEMS: Set[str] = frozenset({
        "deliberation",
        "edit",
        "challenge",
        "cooldown",
    })
    
    def __init__(self):
        """Initialize the audit completeness checker."""
        self._audit_state: Dict[str, Dict[str, bool]] = {}
    
    def initialize_audit(self, decision_id: str) -> None:
        """
        Initialize audit tracking for a decision.
        
        Args:
            decision_id: Unique identifier for the decision
        """
        self._audit_state[decision_id] = {
            item: False for item in self.REQUIRED_ITEMS
        }
    
    def record_item(self, decision_id: str, item: str) -> None:
        """
        Record that an audit item has been completed.
        
        Args:
            decision_id: Unique identifier for the decision
            item: Name of the audit item
        """
        if decision_id not in self._audit_state:
            self.initialize_audit(decision_id)
        
        if item in self.REQUIRED_ITEMS:
            self._audit_state[decision_id][item] = True
    
    def check_completeness(self, decision_id: str) -> AuditCompleteness:
        """
        Check if audit trail is complete.
        
        Args:
            decision_id: Unique identifier for the decision
            
        Returns:
            AuditCompleteness with status of all items
        """
        state = self._audit_state.get(decision_id, {})
        
        has_deliberation = state.get("deliberation", False)
        has_edit = state.get("edit", False)
        has_challenge = state.get("challenge", False)
        has_cooldown = state.get("cooldown", False)
        
        # Find missing items
        missing = []
        if not has_deliberation:
            missing.append("deliberation")
        if not has_edit:
            missing.append("edit")
        if not has_challenge:
            missing.append("challenge")
        if not has_cooldown:
            missing.append("cooldown")
        
        return AuditCompleteness(
            decision_id=decision_id,
            has_deliberation=has_deliberation,
            has_edit=has_edit,
            has_challenge=has_challenge,
            has_cooldown=has_cooldown,
            missing_items=tuple(missing),
        )
    
    def require_completeness(self, decision_id: str) -> AuditCompleteness:
        """
        Require that audit trail is complete.
        
        Args:
            decision_id: Unique identifier for the decision
            
        Returns:
            AuditCompleteness if complete
            
        Raises:
            AuditIncomplete: If any required item is missing
        """
        completeness = self.check_completeness(decision_id)
        
        if not completeness.is_complete:
            raise AuditIncomplete(
                decision_id=decision_id,
                missing_items=list(completeness.missing_items),
            )
        
        return completeness
    
    def get_missing_items(self, decision_id: str) -> List[str]:
        """
        Get list of missing audit items.
        
        Args:
            decision_id: Unique identifier for the decision
            
        Returns:
            List of missing item names
        """
        completeness = self.check_completeness(decision_id)
        return list(completeness.missing_items)
    
    def is_complete(self, decision_id: str) -> bool:
        """
        Check if audit trail is complete.
        
        Args:
            decision_id: Unique identifier for the decision
            
        Returns:
            True if all required items are present
        """
        completeness = self.check_completeness(decision_id)
        return completeness.is_complete
    
    def clear_audit(self, decision_id: str) -> None:
        """
        Clear audit state for a decision.
        
        Args:
            decision_id: Unique identifier for the decision
        """
        self._audit_state.pop(decision_id, None)
