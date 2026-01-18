"""
Tests for Phase-6 Review Queue.

Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from decision_workflow.queue import ReviewQueue
from decision_workflow.types import QueueItem


# ============================================================================
# Unit Tests
# ============================================================================

class TestReviewQueueBasic:
    """Basic unit tests for ReviewQueue."""
    
    def test_empty_queue(self):
        """Empty queue should have no items."""
        queue = ReviewQueue([])
        assert len(queue) == 0
        assert queue.get_pending() == []
    
    def test_queue_with_findings(self):
        """Queue should contain all findings."""
        findings = [
            {"finding_id": "f1", "endpoint": "/api/test", "signals": []},
            {"finding_id": "f2", "endpoint": "/api/other", "signals": []},
        ]
        queue = ReviewQueue(findings)
        
        assert len(queue) == 2
        assert "f1" in queue
        assert "f2" in queue
    
    def test_get_item(self):
        """get_item should return the correct item."""
        findings = [
            {"finding_id": "f1", "endpoint": "/api/test", "signals": [{"type": "error"}]},
        ]
        queue = ReviewQueue(findings)
        
        item = queue.get_item("f1")
        assert item is not None
        assert item.finding_id == "f1"
        assert item.endpoint == "/api/test"
        assert len(item.signals) == 1
    
    def test_get_item_not_found(self):
        """get_item should return None for unknown finding."""
        queue = ReviewQueue([])
        assert queue.get_item("unknown") is None
    
    def test_queue_with_mcp_classifications(self):
        """Queue should include MCP classifications when available."""
        findings = [
            {"finding_id": "f1", "endpoint": "/api/test", "signals": []},
        ]
        mcp = {
            "f1": {"classification": "XSS", "confidence": 0.85},
        }
        queue = ReviewQueue(findings, mcp)
        
        item = queue.get_item("f1")
        assert item.mcp_classification == "XSS"
        assert item.mcp_confidence == 0.85
    
    def test_queue_with_missing_mcp(self):
        """Queue should handle missing MCP data gracefully."""
        findings = [
            {"finding_id": "f1", "endpoint": "/api/test", "signals": []},
        ]
        queue = ReviewQueue(findings)
        
        item = queue.get_item("f1")
        assert item.mcp_classification is None
        assert item.mcp_confidence is None
    
    def test_queue_with_invalid_mcp_confidence(self):
        """Queue should treat invalid MCP confidence as missing."""
        findings = [
            {"finding_id": "f1", "endpoint": "/api/test", "signals": []},
        ]
        mcp = {
            "f1": {"classification": "XSS", "confidence": 1.5},  # Invalid: > 1.0
        }
        queue = ReviewQueue(findings, mcp)
        
        item = queue.get_item("f1")
        assert item.mcp_classification == "XSS"
        assert item.mcp_confidence is None  # Treated as missing
    
    def test_queue_with_malformed_mcp_confidence(self):
        """Queue should treat malformed MCP confidence as missing."""
        findings = [
            {"finding_id": "f1", "endpoint": "/api/test", "signals": []},
        ]
        mcp = {
            "f1": {"classification": "XSS", "confidence": "not a number"},
        }
        queue = ReviewQueue(findings, mcp)
        
        item = queue.get_item("f1")
        assert item.mcp_classification == "XSS"
        assert item.mcp_confidence is None  # Treated as missing


# ============================================================================
# Property Tests
# ============================================================================

class TestQueueItemDisplay:
    """
    Property: Queue items contain all signals and available MCP data.
    
    Validates: Requirements 1.2, 1.3, 1.4
    """
    
    @given(
        finding_id=st.uuids().map(str),
        endpoint=st.text(min_size=1, max_size=100),
        num_signals=st.integers(min_value=0, max_value=10),
    )
    @settings(max_examples=100)
    def test_queue_item_contains_all_signals(
        self,
        finding_id: str,
        endpoint: str,
        num_signals: int,
    ):
        """
        Property: Queue items contain all signals from Phase-5.
        """
        signals = [{"type": f"signal_{i}", "data": f"data_{i}"} for i in range(num_signals)]
        findings = [
            {"finding_id": finding_id, "endpoint": endpoint, "signals": signals},
        ]
        queue = ReviewQueue(findings)
        
        item = queue.get_item(finding_id)
        assert item is not None
        assert len(item.signals) == num_signals
        for i, signal in enumerate(item.signals):
            assert signal["type"] == f"signal_{i}"
    
    @given(
        finding_id=st.uuids().map(str),
        classification=st.text(min_size=1, max_size=50),
        confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_queue_item_contains_mcp_data(
        self,
        finding_id: str,
        classification: str,
        confidence: float,
    ):
        """
        Property: Queue items contain MCP classification and confidence when available.
        """
        findings = [
            {"finding_id": finding_id, "endpoint": "/test", "signals": []},
        ]
        mcp = {
            finding_id: {"classification": classification, "confidence": confidence},
        }
        queue = ReviewQueue(findings, mcp)
        
        item = queue.get_item(finding_id)
        assert item is not None
        assert item.mcp_classification == classification
        assert item.mcp_confidence == confidence
    
    @given(
        finding_id=st.uuids().map(str),
    )
    @settings(max_examples=100)
    def test_queue_item_handles_missing_mcp(self, finding_id: str):
        """
        Property: Queue items handle missing MCP data gracefully.
        """
        findings = [
            {"finding_id": finding_id, "endpoint": "/test", "signals": []},
        ]
        queue = ReviewQueue(findings)
        
        item = queue.get_item(finding_id)
        assert item is not None
        assert item.mcp_classification is None
        assert item.mcp_confidence is None
