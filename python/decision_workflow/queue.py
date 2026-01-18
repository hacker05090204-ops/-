"""
Phase-6 Review Queue

Presents pending findings for human review. All input data is read-only.

ARCHITECTURAL CONSTRAINTS:
- Phase-5 ScanResult is read-only
- MCP classifications are read-only
- Status is derived from decisions, not stored
"""

from __future__ import annotations
from typing import Any, Optional

from decision_workflow.types import QueueItem


class ReviewQueue:
    """
    Presents pending findings for human review.
    
    All input data (Phase-5 signals, MCP classifications) is treated as
    read-only. The queue does not modify any input data.
    
    MCP INPUT HANDLING:
    - mcp_classification and mcp_confidence are OPTIONAL
    - Missing MCP data: fields are None
    - Malformed MCP data: treated as missing
    """
    
    def __init__(
        self,
        findings: list[dict[str, Any]],
        mcp_classifications: Optional[dict[str, dict[str, Any]]] = None,
    ):
        """
        Initialize the review queue.
        
        Args:
            findings: List of finding dicts from Phase-5 with keys:
                     - finding_id: str
                     - endpoint: str
                     - signals: list of signal dicts
            mcp_classifications: Optional dict mapping finding_id to MCP data:
                                - classification: str
                                - confidence: float
        """
        self._findings = findings
        self._mcp_classifications = mcp_classifications or {}
        self._items: dict[str, QueueItem] = {}
        
        # Build queue items
        for finding in findings:
            finding_id = finding.get("finding_id", "")
            endpoint = finding.get("endpoint", "")
            signals = tuple(finding.get("signals", []))
            
            # Get MCP data if available
            mcp_data = self._mcp_classifications.get(finding_id, {})
            mcp_classification = mcp_data.get("classification")
            mcp_confidence = mcp_data.get("confidence")
            
            # Validate MCP confidence is in range
            if mcp_confidence is not None:
                try:
                    mcp_confidence = float(mcp_confidence)
                    if not (0.0 <= mcp_confidence <= 1.0):
                        mcp_confidence = None  # Treat as missing
                except (TypeError, ValueError):
                    mcp_confidence = None  # Treat as missing
            
            item = QueueItem(
                finding_id=finding_id,
                endpoint=endpoint,
                signals=signals,
                mcp_classification=mcp_classification,
                mcp_confidence=mcp_confidence,
            )
            self._items[finding_id] = item
    
    def get_pending(self) -> list[QueueItem]:
        """
        Return all pending finding candidates.
        
        Returns:
            List of QueueItem objects.
        """
        return list(self._items.values())
    
    def get_item(self, finding_id: str) -> Optional[QueueItem]:
        """
        Get a specific finding by ID.
        
        Args:
            finding_id: The finding ID to look up.
            
        Returns:
            The QueueItem if found, None otherwise.
        """
        return self._items.get(finding_id)
    
    def __len__(self) -> int:
        """Return the number of items in the queue."""
        return len(self._items)
    
    def __contains__(self, finding_id: str) -> bool:
        """Check if a finding is in the queue."""
        return finding_id in self._items
