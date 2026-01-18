"""
Phase-9 Duplicate Hint Engine Tests

Tests for duplicate warning functionality.
"""

import pytest
from datetime import datetime

from browser_assistant.duplicate_hint import DuplicateHintEngine


class TestDuplicateHintEngine:
    """Test duplicate hint engine functionality."""
    
    def test_register_finding(self, duplicate_engine):
        """Verify findings can be registered."""
        fid = duplicate_engine.register_finding(
            url="https://example.com/vuln",
            content="XSS vulnerability in search parameter",
        )
        
        assert fid is not None
        assert duplicate_engine.get_known_findings_count() == 1
    
    def test_register_finding_with_id(self, duplicate_engine):
        """Verify findings can be registered with custom ID."""
        fid = duplicate_engine.register_finding(
            url="https://example.com/vuln",
            content="XSS vulnerability",
            finding_id="custom-001",
        )
        
        assert fid == "custom-001"
    
    def test_check_no_duplicates(self, duplicate_engine):
        """Verify no hint when no similar findings."""
        hint = duplicate_engine.check_for_duplicates(
            url="https://example.com/page",
            content="Some unique content",
        )
        
        assert hint is None
    
    def test_check_finds_similar(self, duplicate_engine):
        """Verify hint when similar finding exists."""
        # Register a finding
        duplicate_engine.register_finding(
            url="https://example.com/search",
            content="XSS vulnerability in search parameter q",
            finding_id="finding-001",
        )
        
        # Check for similar
        hint = duplicate_engine.check_for_duplicates(
            url="https://example.com/search",
            content="XSS vulnerability in search parameter q value",
        )
        
        assert hint is not None
        assert hint.similar_finding_id == "finding-001"
        assert hint.similarity_score >= 0.7
    
    def test_hint_is_heuristic(self, duplicate_engine):
        """Verify hint is marked as heuristic."""
        duplicate_engine.register_finding(
            url="https://example.com/search",
            content="XSS vulnerability",
        )
        
        hint = duplicate_engine.check_for_duplicates(
            url="https://example.com/search",
            content="XSS vulnerability found",
        )
        
        if hint:
            assert hint.is_heuristic is True
            assert hint.human_confirmation_required is True
            assert hint.does_not_block is True
            assert "heuristic" in hint.similarity_disclaimer.lower()
    
    def test_hint_does_not_block(self, duplicate_engine):
        """Verify hint never blocks."""
        duplicate_engine.register_finding(
            url="https://example.com/page",
            content="Exact same content",
        )
        
        # Even with identical content, should not block
        hint = duplicate_engine.check_for_duplicates(
            url="https://example.com/page",
            content="Exact same content",
        )
        
        if hint:
            assert hint.does_not_block is True
    
    def test_similarity_threshold(self, duplicate_engine):
        """Verify similarity threshold is respected."""
        duplicate_engine.register_finding(
            url="https://example.com/page1",
            content="AAAA",
        )
        
        # Very different content should not trigger hint
        hint = duplicate_engine.check_for_duplicates(
            url="https://example.com/page2",
            content="ZZZZ completely different",
        )
        
        assert hint is None
    
    def test_compute_similarity_identical(self, duplicate_engine):
        """Verify identical content has similarity 1.0."""
        similarity = duplicate_engine._compute_similarity(
            "Exact same text",
            "Exact same text",
        )
        
        assert similarity == 1.0
    
    def test_compute_similarity_different(self, duplicate_engine):
        """Verify different content has low similarity."""
        similarity = duplicate_engine._compute_similarity(
            "AAAA BBBB CCCC",
            "XXXX YYYY ZZZZ",
        )
        
        assert similarity < 0.5
    
    def test_compute_similarity_empty(self, duplicate_engine):
        """Verify empty content has similarity 0.0."""
        assert duplicate_engine._compute_similarity("", "test") == 0.0
        assert duplicate_engine._compute_similarity("test", "") == 0.0
        assert duplicate_engine._compute_similarity("", "") == 0.0
    
    def test_clear_findings(self, duplicate_engine):
        """Verify findings can be cleared."""
        for i in range(5):
            duplicate_engine.register_finding(
                url=f"https://example.com/page{i}",
                content=f"Content {i}",
            )
        
        count = duplicate_engine.clear_findings()
        assert count == 5
        assert duplicate_engine.get_known_findings_count() == 0
    
    def test_findings_limit_enforced(self, duplicate_engine):
        """Verify findings storage limit is enforced."""
        duplicate_engine._max_findings = 10
        
        for i in range(15):
            duplicate_engine.register_finding(
                url=f"https://example.com/page{i}",
                content=f"Content {i}",
            )
        
        assert duplicate_engine.get_known_findings_count() == 10


class TestDuplicateHintEngineNoForbiddenMethods:
    """Verify engine has no forbidden methods."""
    
    def test_no_block_duplicate(self, duplicate_engine):
        """Verify block_duplicate method does not exist."""
        assert not hasattr(duplicate_engine, "block_duplicate")
    
    def test_no_auto_reject(self, duplicate_engine):
        """Verify auto_reject method does not exist."""
        assert not hasattr(duplicate_engine, "auto_reject")
    
    def test_no_confirm_duplicate(self, duplicate_engine):
        """Verify confirm_duplicate method does not exist."""
        assert not hasattr(duplicate_engine, "confirm_duplicate")
    
    def test_no_filter_duplicates(self, duplicate_engine):
        """Verify filter_duplicates method does not exist."""
        assert not hasattr(duplicate_engine, "filter_duplicates")
    
    def test_no_is_duplicate(self, duplicate_engine):
        """Verify is_duplicate method does not exist."""
        assert not hasattr(duplicate_engine, "is_duplicate")
    
    def test_no_mark_as_duplicate(self, duplicate_engine):
        """Verify mark_as_duplicate method does not exist."""
        assert not hasattr(duplicate_engine, "mark_as_duplicate")
    
    def test_no_reject_duplicate(self, duplicate_engine):
        """Verify reject_duplicate method does not exist."""
        assert not hasattr(duplicate_engine, "reject_duplicate")
