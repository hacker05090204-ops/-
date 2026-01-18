"""
Tests for Phase-8 Duplicate Detector

Verifies that:
- Duplicate detection returns warnings only
- Warnings are non-blocking
- Similarity is heuristic
- No auto-reject or auto-defer
"""

import pytest
from datetime import datetime

from intelligence_layer.duplicate import DuplicateDetector
from intelligence_layer.data_access import DataAccessLayer
from intelligence_layer.types import DuplicateWarning, SimilarFinding
from intelligence_layer.tests.conftest import create_sample_decision


class TestDuplicateDetectorBasic:
    """Basic tests for duplicate detector."""
    
    def test_check_duplicates_returns_warning(self, duplicate_detector):
        """Verify check_duplicates returns a DuplicateWarning."""
        warning = duplicate_detector.check_duplicates(
            finding_id="new-finding",
            finding_content="Test content",
            target_id="target-001",
        )
        
        assert isinstance(warning, DuplicateWarning)
    
    def test_warning_is_non_blocking(self, duplicate_detector):
        """Verify warning does not block - always returns, never raises."""
        # Should not raise any exception
        warning = duplicate_detector.check_duplicates(
            finding_id="new-finding",
            finding_content="Test content",
            target_id="target-001",
        )
        
        # Warning should always be returned
        assert warning is not None
        assert isinstance(warning, DuplicateWarning)
    
    def test_human_decision_required_always_true(self, duplicate_detector):
        """Verify human_decision_required is always True."""
        warning = duplicate_detector.check_duplicates(
            finding_id="new-finding",
            finding_content="Test content",
            target_id="target-001",
        )
        
        assert warning.human_decision_required is True
    
    def test_is_heuristic_always_true(self, duplicate_detector):
        """Verify is_heuristic is always True."""
        warning = duplicate_detector.check_duplicates(
            finding_id="new-finding",
            finding_content="Test content",
            target_id="target-001",
        )
        
        assert warning.is_heuristic is True
    
    def test_similarity_disclaimer_present(self, duplicate_detector):
        """Verify similarity disclaimer is present."""
        warning = duplicate_detector.check_duplicates(
            finding_id="new-finding",
            finding_content="Test content",
            target_id="target-001",
        )
        
        assert "heuristic" in warning.similarity_disclaimer.lower()
        assert "human" in warning.similarity_disclaimer.lower()


class TestDuplicateDetectorSimilarity:
    """Tests for similarity computation."""
    
    def test_identical_content_high_similarity(self):
        """Verify identical content returns high similarity."""
        decisions = [
            create_sample_decision(
                decision_id="dec-001",
                finding_id="find-001",
                target_id="target-001",
                content="XSS vulnerability in login form",
            ),
        ]
        data_access = DataAccessLayer(decisions=decisions)
        detector = DuplicateDetector(data_access)
        
        warning = detector.check_duplicates(
            finding_id="new-finding",
            finding_content="XSS vulnerability in login form",
            target_id="target-001",
        )
        
        assert warning.highest_similarity > 0.9
    
    def test_different_content_low_similarity(self):
        """Verify different content returns low similarity."""
        decisions = [
            create_sample_decision(
                decision_id="dec-001",
                finding_id="find-001",
                target_id="target-001",
                content="SQL injection in search endpoint",
            ),
        ]
        data_access = DataAccessLayer(decisions=decisions)
        detector = DuplicateDetector(data_access)
        
        warning = detector.check_duplicates(
            finding_id="new-finding",
            finding_content="CSRF token missing on profile update",
            target_id="target-001",
        )
        
        assert warning.highest_similarity < 0.5
    
    def test_compute_similarity_range(self):
        """Verify compute_similarity returns value in [0, 1]."""
        data_access = DataAccessLayer()
        detector = DuplicateDetector(data_access)
        
        # Test various content pairs
        test_cases = [
            ("identical", "identical"),
            ("completely different", "nothing alike"),
            ("", ""),
            ("short", "short text"),
        ]
        
        for content_a, content_b in test_cases:
            similarity = detector.compute_similarity(content_a, content_b)
            assert 0.0 <= similarity <= 1.0
    
    def test_empty_content_returns_zero_similarity(self):
        """Verify empty content returns zero similarity."""
        data_access = DataAccessLayer()
        detector = DuplicateDetector(data_access)
        
        assert detector.compute_similarity("", "test") == 0.0
        assert detector.compute_similarity("test", "") == 0.0
        assert detector.compute_similarity("", "") == 0.0


class TestDuplicateDetectorThreshold:
    """Tests for similarity threshold."""
    
    def test_threshold_filters_similar_findings(self):
        """Verify threshold filters similar findings."""
        decisions = [
            create_sample_decision(
                decision_id="dec-001",
                finding_id="find-001",
                target_id="target-001",
                content="XSS vulnerability in login form",
            ),
            create_sample_decision(
                decision_id="dec-002",
                finding_id="find-002",
                target_id="target-001",
                content="Completely unrelated content about database",
            ),
        ]
        data_access = DataAccessLayer(decisions=decisions)
        detector = DuplicateDetector(data_access, similarity_threshold=0.8)
        
        warning = detector.check_duplicates(
            finding_id="new-finding",
            finding_content="XSS vulnerability in login form",
            target_id="target-001",
        )
        
        # Only the similar finding should be included
        assert len(warning.similar_findings) == 1
        assert warning.similar_findings[0].finding_id == "find-001"
    
    def test_configurable_threshold(self):
        """Verify threshold is configurable."""
        decisions = [
            create_sample_decision(
                decision_id="dec-001",
                finding_id="find-001",
                target_id="target-001",
                content="XSS vulnerability",
            ),
        ]
        data_access = DataAccessLayer(decisions=decisions)
        
        # High threshold - should not match
        detector_high = DuplicateDetector(data_access, similarity_threshold=0.99)
        warning_high = detector_high.check_duplicates(
            finding_id="new-finding",
            finding_content="XSS vulnerability in form",
            target_id="target-001",
        )
        
        # Low threshold - should match
        detector_low = DuplicateDetector(data_access, similarity_threshold=0.3)
        warning_low = detector_low.check_duplicates(
            finding_id="new-finding",
            finding_content="XSS vulnerability in form",
            target_id="target-001",
        )
        
        assert len(warning_high.similar_findings) <= len(warning_low.similar_findings)


class TestDuplicateDetectorEdgeCases:
    """Tests for edge cases."""
    
    def test_empty_history_returns_empty_warning(self, empty_data_access):
        """Verify empty history returns warning with no similar findings."""
        detector = DuplicateDetector(empty_data_access)
        
        warning = detector.check_duplicates(
            finding_id="new-finding",
            finding_content="Test content",
            target_id="target-001",
        )
        
        assert len(warning.similar_findings) == 0
        assert warning.highest_similarity == 0.0
    
    def test_same_finding_id_excluded(self):
        """Verify same finding ID is excluded from results."""
        decisions = [
            create_sample_decision(
                decision_id="dec-001",
                finding_id="find-001",
                target_id="target-001",
                content="Test content",
            ),
        ]
        data_access = DataAccessLayer(decisions=decisions)
        detector = DuplicateDetector(data_access)
        
        warning = detector.check_duplicates(
            finding_id="find-001",  # Same as existing
            finding_content="Test content",
            target_id="target-001",
        )
        
        # Should not include itself
        assert len(warning.similar_findings) == 0


class TestDuplicateDetectorNoForbiddenMethods:
    """Tests to verify no forbidden methods exist."""
    
    def test_no_auto_reject_method(self, duplicate_detector):
        """Verify auto_reject method does not exist."""
        assert not hasattr(duplicate_detector, "auto_reject")
    
    def test_no_auto_defer_method(self, duplicate_detector):
        """Verify auto_defer method does not exist."""
        assert not hasattr(duplicate_detector, "auto_defer")
    
    def test_no_block_finding_method(self, duplicate_detector):
        """Verify block_finding method does not exist."""
        assert not hasattr(duplicate_detector, "block_finding")
    
    def test_no_filter_duplicates_method(self, duplicate_detector):
        """Verify filter_duplicates method does not exist."""
        assert not hasattr(duplicate_detector, "filter_duplicates")
    
    def test_no_confirm_duplicate_method(self, duplicate_detector):
        """Verify confirm_duplicate method does not exist."""
        assert not hasattr(duplicate_detector, "confirm_duplicate")
    
    def test_no_is_duplicate_method(self, duplicate_detector):
        """Verify is_duplicate method does not exist."""
        assert not hasattr(duplicate_detector, "is_duplicate")


class TestSimilarFindingDisclaimer:
    """Tests for SimilarFinding disclaimer."""
    
    def test_similar_finding_has_score_disclaimer(self):
        """Verify SimilarFinding has score disclaimer."""
        decisions = [
            create_sample_decision(
                decision_id="dec-001",
                finding_id="find-001",
                target_id="target-001",
                content="Test content",
            ),
        ]
        data_access = DataAccessLayer(decisions=decisions)
        detector = DuplicateDetector(data_access, similarity_threshold=0.0)
        
        warning = detector.check_duplicates(
            finding_id="new-finding",
            finding_content="Test content",
            target_id="target-001",
        )
        
        if warning.similar_findings:
            for similar in warning.similar_findings:
                assert "advisory" in similar.score_disclaimer.lower()
                assert "certainty" in similar.score_disclaimer.lower()
