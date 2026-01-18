"""
Property Tests for Feedback Reactor

**Feature: cyfer-brain, Property 7: Feedback Reaction Consistency**
**Validates: Requirements 4.1, 4.2, 4.3, 4.4**

**Feature: cyfer-brain, Property 10: Coverage Gap Honesty**
**Validates: Requirements 3.5, 4.5**
"""

import pytest
from hypothesis import given, strategies as st, settings
import sys
import os

# Add parent directory to path for import
test_dir = os.path.dirname(os.path.abspath(__file__))
cyfer_brain_dir = os.path.dirname(test_dir)
python_dir = os.path.dirname(cyfer_brain_dir)
if python_dir not in sys.path:
    sys.path.insert(0, python_dir)

from cyfer_brain.feedback import FeedbackReactor, ExplorationAdjustment
from cyfer_brain.types import Hypothesis, HypothesisStatus, MCPClassification


class TestFeedbackReactionConsistency:
    """
    **Feature: cyfer-brain, Property 7: Feedback Reaction Consistency**
    **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
    
    For any MCP classification, Cyfer Brain's reaction SHALL be
    deterministic based on the classification type.
    """
    
    def test_bug_classification_always_stops_path(self):
        """Verify BUG classification always results in STOP_PATH."""
        reactor = FeedbackReactor()
        
        hypothesis = Hypothesis(
            description="Test hypothesis",
            target_invariant_categories=["Authorization"],
        )
        
        classification = MCPClassification(
            observation_id="test",
            classification="BUG",
            invariant_violated="AUTH_001",
            confidence=0.95,
        )
        
        adjustment = reactor.react_to_classification(hypothesis, classification)
        
        assert adjustment == ExplorationAdjustment.STOP_PATH
    
    def test_signal_classification_continues_or_increases_depth(self):
        """Verify SIGNAL classification results in CONTINUE or INCREASE_DEPTH."""
        reactor = FeedbackReactor()
        
        hypothesis = Hypothesis(
            description="Test hypothesis",
            target_invariant_categories=["Authorization"],
        )
        
        classification = MCPClassification(
            observation_id="test",
            classification="SIGNAL",
            confidence=0.5,
        )
        
        adjustment = reactor.react_to_classification(hypothesis, classification)
        
        assert adjustment in [ExplorationAdjustment.CONTINUE, ExplorationAdjustment.INCREASE_DEPTH]
    
    def test_no_issue_classification_deprioritizes(self):
        """Verify NO_ISSUE classification results in DEPRIORITIZE or STOP_CATEGORY."""
        reactor = FeedbackReactor()
        
        hypothesis = Hypothesis(
            description="Test hypothesis",
            target_invariant_categories=["Authorization"],
        )
        
        classification = MCPClassification(
            observation_id="test",
            classification="NO_ISSUE",
        )
        
        adjustment = reactor.react_to_classification(hypothesis, classification)
        
        assert adjustment in [ExplorationAdjustment.DEPRIORITIZE, ExplorationAdjustment.STOP_CATEGORY]
    
    @given(st.sampled_from(["BUG", "SIGNAL", "NO_ISSUE", "COVERAGE_GAP"]))
    @settings(max_examples=100)
    def test_same_classification_produces_consistent_adjustment(self, classification_type):
        """
        Property test: Same classification type always produces consistent adjustment.
        """
        # Run multiple times with same classification type
        adjustments = []
        
        for _ in range(5):
            reactor = FeedbackReactor()  # Fresh reactor each time
            
            hypothesis = Hypothesis(
                description="Test",
                target_invariant_categories=["Authorization"],
            )
            
            classification = MCPClassification(
                observation_id="test",
                classification=classification_type,
            )
            
            adjustment = reactor.react_to_classification(hypothesis, classification)
            adjustments.append(adjustment)
        
        # All adjustments should be the same for same classification type
        # (with fresh reactor state)
        assert len(set(adjustments)) == 1, \
            f"Inconsistent adjustments for {classification_type}: {adjustments}"


class TestCoverageGapHonesty:
    """
    **Feature: cyfer-brain, Property 10: Coverage Gap Honesty**
    **Validates: Requirements 3.5, 4.5**
    
    For any COVERAGE_GAP classification from MCP, Cyfer Brain SHALL NOT
    interpret it as a finding or claim it as a bug.
    """
    
    def test_coverage_gap_is_not_treated_as_bug(self):
        """Verify COVERAGE_GAP is not treated as a bug."""
        reactor = FeedbackReactor()
        
        hypothesis = Hypothesis(
            description="Test hypothesis",
            target_invariant_categories=["Authorization"],
        )
        
        classification = MCPClassification(
            observation_id="test",
            classification="COVERAGE_GAP",
            coverage_gaps=["AUTH_005 not covered"],
        )
        
        adjustment = reactor.react_to_classification(hypothesis, classification)
        
        # COVERAGE_GAP should result in CONTINUE, not STOP_PATH (which is for bugs)
        assert adjustment != ExplorationAdjustment.STOP_PATH, \
            "COVERAGE_GAP should not be treated as a bug"
        assert adjustment == ExplorationAdjustment.CONTINUE
    
    def test_coverage_gap_does_not_increment_bug_count(self):
        """Verify COVERAGE_GAP does not increment bug statistics."""
        reactor = FeedbackReactor()
        
        hypothesis = Hypothesis(
            description="Test hypothesis",
            target_invariant_categories=["Authorization"],
        )
        
        classification = MCPClassification(
            observation_id="test",
            classification="COVERAGE_GAP",
            coverage_gaps=["Some gap"],
        )
        
        reactor.react_to_classification(hypothesis, classification)
        
        stats = reactor.get_category_stats("Authorization")
        assert stats.bugs == 0, "COVERAGE_GAP should not count as a bug"
        assert stats.coverage_gaps == 1, "COVERAGE_GAP should be tracked separately"
    
    @given(st.lists(st.text(min_size=1), min_size=1, max_size=5))
    @settings(max_examples=50)
    def test_coverage_gaps_are_logged_not_claimed(self, gap_descriptions):
        """
        Property test: Coverage gaps are logged but never claimed as findings.
        """
        reactor = FeedbackReactor()
        
        hypothesis = Hypothesis(
            description="Test",
            target_invariant_categories=["Authorization"],
        )
        
        classification = MCPClassification(
            observation_id="test",
            classification="COVERAGE_GAP",
            coverage_gaps=gap_descriptions,
        )
        
        adjustment = reactor.react_to_classification(hypothesis, classification)
        
        # Should continue, not stop (which would imply finding)
        assert adjustment == ExplorationAdjustment.CONTINUE
        
        # Hypothesis should be resolved but not marked as bug
        assert hypothesis.status == HypothesisStatus.RESOLVED
        assert hypothesis.mcp_classification.classification == "COVERAGE_GAP"


class TestStopLossRules:
    """Test stop-loss rules for diminishing returns."""
    
    def test_consecutive_no_issues_triggers_stop_loss(self):
        """Verify consecutive NO_ISSUE classifications trigger stop-loss."""
        reactor = FeedbackReactor()
        
        # Generate many NO_ISSUE classifications
        for i in range(reactor.CONSECUTIVE_NO_ISSUE_LIMIT):
            hypothesis = Hypothesis(
                description=f"Test {i}",
                target_invariant_categories=["Authorization"],
            )
            
            classification = MCPClassification(
                observation_id=f"test-{i}",
                classification="NO_ISSUE",
            )
            
            adjustment = reactor.react_to_classification(hypothesis, classification)
        
        # After limit, should trigger stop
        assert adjustment == ExplorationAdjustment.STOP_CATEGORY
    
    def test_bug_resets_consecutive_no_issues(self):
        """Verify BUG classification resets consecutive NO_ISSUE counter."""
        reactor = FeedbackReactor()
        
        # Generate some NO_ISSUE classifications
        for i in range(5):
            hypothesis = Hypothesis(
                description=f"Test {i}",
                target_invariant_categories=["Authorization"],
            )
            classification = MCPClassification(
                observation_id=f"test-{i}",
                classification="NO_ISSUE",
            )
            reactor.react_to_classification(hypothesis, classification)
        
        # Now a BUG
        bug_hypothesis = Hypothesis(
            description="Bug test",
            target_invariant_categories=["Authorization"],
        )
        bug_classification = MCPClassification(
            observation_id="bug-test",
            classification="BUG",
            invariant_violated="AUTH_001",
        )
        reactor.react_to_classification(bug_hypothesis, bug_classification)
        
        # Counter should be reset
        assert reactor._state.consecutive_no_issues == 0
    
    def test_signal_resets_consecutive_no_issues(self):
        """Verify SIGNAL classification resets consecutive NO_ISSUE counter."""
        reactor = FeedbackReactor()
        
        # Generate some NO_ISSUE classifications
        for i in range(5):
            hypothesis = Hypothesis(
                description=f"Test {i}",
                target_invariant_categories=["Authorization"],
            )
            classification = MCPClassification(
                observation_id=f"test-{i}",
                classification="NO_ISSUE",
            )
            reactor.react_to_classification(hypothesis, classification)
        
        # Now a SIGNAL
        signal_hypothesis = Hypothesis(
            description="Signal test",
            target_invariant_categories=["Authorization"],
        )
        signal_classification = MCPClassification(
            observation_id="signal-test",
            classification="SIGNAL",
        )
        reactor.react_to_classification(signal_hypothesis, signal_classification)
        
        # Counter should be reset
        assert reactor._state.consecutive_no_issues == 0


class TestHypothesisStatusUpdate:
    """Test that hypothesis status is correctly updated."""
    
    def test_hypothesis_status_updated_to_resolved(self):
        """Verify hypothesis status is updated to RESOLVED after classification."""
        reactor = FeedbackReactor()
        
        hypothesis = Hypothesis(
            description="Test",
            target_invariant_categories=["Authorization"],
            status=HypothesisStatus.SUBMITTED,
        )
        
        classification = MCPClassification(
            observation_id="test",
            classification="SIGNAL",
        )
        
        reactor.react_to_classification(hypothesis, classification)
        
        assert hypothesis.status == HypothesisStatus.RESOLVED
    
    def test_hypothesis_receives_mcp_classification(self):
        """Verify hypothesis receives MCP classification."""
        reactor = FeedbackReactor()
        
        hypothesis = Hypothesis(
            description="Test",
            target_invariant_categories=["Authorization"],
        )
        
        classification = MCPClassification(
            observation_id="test",
            classification="BUG",
            invariant_violated="AUTH_001",
            confidence=0.95,
        )
        
        reactor.react_to_classification(hypothesis, classification)
        
        assert hypothesis.mcp_classification is not None
        assert hypothesis.mcp_classification.classification == "BUG"
        assert hypothesis.mcp_classification.invariant_violated == "AUTH_001"
