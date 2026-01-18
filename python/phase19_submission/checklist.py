"""
Phase-19 Submission Checklist

GOVERNANCE CONSTRAINTS:
- Static checklist only
- No scoring, ranking, priority, or severity
- Neutral, descriptive wording only
- Human checks items manually
- No auto-check functionality

This module provides a static submission checklist.
All items are equal - no priority or importance indicators.
"""

from typing import List, Dict
from dataclasses import dataclass, field
from datetime import datetime

from .types import ChecklistItem, SubmissionLog, SubmissionAction


# STATIC CHECKLIST ITEMS - Neutral language, no scoring
# Items are ordered alphabetically by item_id
STATIC_CHECKLIST_ITEMS: List[ChecklistItem] = [
    ChecklistItem(
        item_id="A",
        description="Export report in desired format",
    ),
    ChecklistItem(
        item_id="B",
        description="Open submission URL in browser",
    ),
    ChecklistItem(
        item_id="C",
        description="Paste report content into submission form",
    ),
    ChecklistItem(
        item_id="D",
        description="Review submission before sending",
    ),
    ChecklistItem(
        item_id="E",
        description="Submit via platform interface",
    ),
]


@dataclass
class ChecklistState:
    """
    State of checklist items.
    
    GOVERNANCE:
    - No auto-check
    - Human checks manually
    - All items equal (no priority)
    """
    checked_items: Dict[str, bool] = field(default_factory=dict)
    logs: List[SubmissionLog] = field(default_factory=list)


class SubmissionChecklist:
    """
    Static submission checklist.
    
    GOVERNANCE:
    - Static items only
    - No scoring or ranking
    - Human checks manually
    - Neutral language
    """
    
    def __init__(self):
        """Initialize checklist with static items."""
        self._items = list(STATIC_CHECKLIST_ITEMS)
        self._state = ChecklistState()
    
    def get_items(self) -> List[ChecklistItem]:
        """
        Get all checklist items.
        
        Returns items in alphabetical order by item_id.
        No priority or importance indicators.
        """
        return sorted(self._items, key=lambda i: i.item_id)
    
    def check_item(
        self,
        item_id: str,
        human_checked: bool,
    ) -> bool:
        """
        Mark item as checked by human.
        
        Args:
            item_id: ID of item to check
            human_checked: MUST be True (human action required)
            
        Returns:
            True if item was checked
            
        Note:
            This does NOT auto-check. Human must explicitly
            set human_checked=True to check an item.
        """
        if not human_checked:
            # Do not auto-check
            return False
        
        # Find item
        item_exists = any(i.item_id == item_id for i in self._items)
        if not item_exists:
            return False
        
        # Mark as checked
        self._state.checked_items[item_id] = True
        
        # Log the action with HUMAN attribution
        log = SubmissionLog(
            timestamp=datetime.now(),
            action=SubmissionAction.CHECK_ITEM,
            attribution="HUMAN",
            details=f"Checked item: {item_id}",
        )
        self._state.logs.append(log)
        
        return True
    
    def uncheck_item(
        self,
        item_id: str,
        human_unchecked: bool,
    ) -> bool:
        """
        Mark item as unchecked by human.
        
        Args:
            item_id: ID of item to uncheck
            human_unchecked: MUST be True (human action required)
            
        Returns:
            True if item was unchecked
        """
        if not human_unchecked:
            return False
        
        if item_id in self._state.checked_items:
            self._state.checked_items[item_id] = False
            return True
        
        return False
    
    def is_checked(self, item_id: str) -> bool:
        """Check if item is checked."""
        return self._state.checked_items.get(item_id, False)
    
    def get_checked_count(self) -> int:
        """Get count of checked items."""
        return sum(1 for v in self._state.checked_items.values() if v)
    
    def get_total_count(self) -> int:
        """Get total item count."""
        return len(self._items)
    
    def get_logs(self) -> List[SubmissionLog]:
        """Get all checklist logs."""
        return list(self._state.logs)
