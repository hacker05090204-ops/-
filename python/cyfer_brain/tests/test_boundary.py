"""
Property Tests for Boundary Manager

**Feature: cyfer-brain, Property 6: Boundary Enforcement**
**Validates: Requirements 7.3, 7.5**

For any exploration session, Cyfer Brain SHALL stop when boundaries
are reached and SHALL NOT claim completeness.
"""

import pytest
from hypothesis import given, strategies as st, settings
import threading
import sys
import os

# Add parent directory to path for import
test_dir = os.path.dirname(os.path.abspath(__file__))
cyfer_brain_dir = os.path.dirname(test_dir)
python_dir = os.path.dirname(cyfer_brain_dir)
if python_dir not in sys.path:
    sys.path.insert(0, python_dir)

from cyfer_brain.boundary import (
    BoundaryManager,
    GlobalExplorationBudget,
    AtomicInt,
)
from cyfer_brain.types import (
    ExplorationBoundary,
    ExplorationStats,
    ExplorationSummary,
    BoundaryStatus,
    Hypothesis,
)


class TestBoundaryEnforcement:
    """
    **Feature: cyfer-brain, Property 6: Boundary Enforcement**
    **Validates: Requirements 7.3, 7.5**
    
    For any exploration session, Cyfer Brain SHALL stop when boundaries
    are reached and SHALL NOT claim completeness.
    """
    
    def test_stops_when_action_budget_exhausted(self):
        """Verify exploration stops when action budget is exhausted."""
        boundary = ExplorationBoundary(max_actions=5)
        manager = BoundaryManager(boundary)
        
        # Consume all actions
        for _ in range(5):
            assert manager.consume_action()
        
        # Should not be able to continue
        assert not manager.can_continue()
        assert not manager.consume_action()
    
    def test_stops_when_submission_budget_exhausted(self):
        """Verify exploration stops when MCP submission budget is exhausted."""
        boundary = ExplorationBoundary(max_mcp_submissions=3)
        manager = BoundaryManager(boundary)
        
        # Consume all submissions
        for _ in range(3):
            assert manager.consume_submission()
        
        # Should not be able to continue
        assert not manager.can_continue()
        assert not manager.consume_submission()
    
    def test_summary_does_not_claim_completeness(self):
        """Verify exploration summary does not claim completeness."""
        manager = BoundaryManager()
        stats = ExplorationStats()
        
        summary = manager.generate_exploration_summary(stats)
        
        # Summary should NOT have coverage_percentage or is_complete
        assert not hasattr(summary, "coverage_percentage") or summary.__dict__.get("coverage_percentage") is None
        assert not hasattr(summary, "is_complete") or summary.__dict__.get("is_complete") is None
    
    @given(
        st.integers(min_value=1, max_value=100),
        st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=50)
    def test_budget_exhaustion_is_deterministic(self, max_actions, max_submissions):
        """
        Property test: Budget exhaustion is deterministic.
        """
        boundary = ExplorationBoundary(
            max_actions=max_actions,
            max_mcp_submissions=max_submissions,
        )
        manager = BoundaryManager(boundary)
        
        # Consume exactly max_actions
        consumed = 0
        while manager.consume_action():
            consumed += 1
        
        assert consumed == max_actions
        
        # Reset and test submissions
        manager.reset(boundary)
        consumed = 0
        while manager.consume_submission():
            consumed += 1
        
        assert consumed == max_submissions


class TestGlobalExplorationBudget:
    """Test GlobalExplorationBudget thread safety."""
    
    def test_atomic_action_consumption(self):
        """Verify action consumption is atomic."""
        boundary = ExplorationBoundary(max_actions=100)
        budget = GlobalExplorationBudget(boundary)
        
        consumed = []
        
        def consume_actions():
            local_consumed = 0
            while budget.consume_action():
                local_consumed += 1
            consumed.append(local_consumed)
        
        # Run multiple threads
        threads = [threading.Thread(target=consume_actions) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Total consumed should equal max_actions
        assert sum(consumed) == 100
    
    def test_atomic_submission_consumption(self):
        """Verify submission consumption is atomic."""
        boundary = ExplorationBoundary(max_mcp_submissions=50)
        budget = GlobalExplorationBudget(boundary)
        
        consumed = []
        
        def consume_submissions():
            local_consumed = 0
            while budget.consume_submission():
                local_consumed += 1
            consumed.append(local_consumed)
        
        # Run multiple threads
        threads = [threading.Thread(target=consume_submissions) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Total consumed should equal max_mcp_submissions
        assert sum(consumed) == 50
    
    def test_budget_status_transitions(self):
        """Verify budget status transitions correctly."""
        boundary = ExplorationBoundary(max_actions=10)
        budget = GlobalExplorationBudget(boundary)
        
        # Initially within bounds
        assert budget.get_status() == BoundaryStatus.WITHIN_BOUNDS
        
        # Consume most actions
        for _ in range(9):
            budget.consume_action()
        
        # Should be approaching limit
        assert budget.get_status() == BoundaryStatus.APPROACHING_LIMIT
        
        # Consume last action
        budget.consume_action()
        
        # Should be at limit
        assert budget.get_status() in [BoundaryStatus.LIMIT_REACHED, BoundaryStatus.EXCEEDED]


class TestAtomicInt:
    """Test AtomicInt thread safety."""
    
    def test_atomic_decrement(self):
        """Verify decrement is atomic."""
        atomic = AtomicInt(1000)
        
        results = []
        
        def decrement_many():
            local_results = []
            for _ in range(100):
                local_results.append(atomic.decrement())
            results.extend(local_results)
        
        threads = [threading.Thread(target=decrement_many) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Final value should be 0
        assert atomic.get() == 0
        
        # All results should be unique (no race conditions)
        assert len(results) == 1000
        assert len(set(results)) == 1000
    
    def test_try_consume_is_atomic(self):
        """Verify try_consume is atomic."""
        atomic = AtomicInt(100)
        
        consumed = []
        
        def try_consume_many():
            local_consumed = 0
            while atomic.try_consume():
                local_consumed += 1
            consumed.append(local_consumed)
        
        threads = [threading.Thread(target=try_consume_many) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Total consumed should equal initial value
        assert sum(consumed) == 100


class TestPrioritizeRemaining:
    """Test hypothesis prioritization within budget."""
    
    def test_prioritizes_by_testability(self):
        """Verify hypotheses are prioritized by testability."""
        manager = BoundaryManager()
        
        hypotheses = [
            Hypothesis(description="Low", testability_score=0.2),
            Hypothesis(description="High", testability_score=0.9),
            Hypothesis(description="Medium", testability_score=0.5),
        ]
        
        prioritized = manager.prioritize_remaining(hypotheses)
        
        # Should be sorted by testability descending
        assert prioritized[0].testability_score == 0.9
        assert prioritized[1].testability_score == 0.5
        assert prioritized[2].testability_score == 0.2
    
    def test_limits_to_remaining_budget(self):
        """Verify prioritization limits to remaining budget."""
        boundary = ExplorationBoundary(max_actions=2, max_mcp_submissions=2)
        manager = BoundaryManager(boundary)
        
        hypotheses = [
            Hypothesis(description=f"H{i}", testability_score=0.5)
            for i in range(10)
        ]
        
        prioritized = manager.prioritize_remaining(hypotheses)
        
        # Should be limited to min(max_actions, max_mcp_submissions)
        assert len(prioritized) <= 2
    
    @given(st.lists(st.floats(min_value=0.0, max_value=1.0, allow_nan=False), min_size=1, max_size=20))
    @settings(max_examples=50)
    def test_prioritization_maintains_order(self, testability_scores):
        """Property test: Prioritization always maintains descending order."""
        manager = BoundaryManager()
        
        hypotheses = [
            Hypothesis(description=f"H{i}", testability_score=score)
            for i, score in enumerate(testability_scores)
        ]
        
        prioritized = manager.prioritize_remaining(hypotheses)
        
        # Verify descending order
        for i in range(len(prioritized) - 1):
            assert prioritized[i].testability_score >= prioritized[i + 1].testability_score


class TestExplorationSummary:
    """Test exploration summary generation."""
    
    def test_summary_includes_stop_reason(self):
        """Verify summary includes reason for stopping."""
        boundary = ExplorationBoundary(max_actions=1)
        manager = BoundaryManager(boundary)
        
        # Exhaust budget
        manager.consume_action()
        
        stats = ExplorationStats()
        summary = manager.generate_exploration_summary(stats)
        
        assert summary.stopped_reason != ""
        assert "exhausted" in summary.stopped_reason.lower() or "exceeded" in summary.stopped_reason.lower()
    
    def test_summary_includes_boundary_status(self):
        """Verify summary includes boundary status."""
        manager = BoundaryManager()
        stats = ExplorationStats()
        
        summary = manager.generate_exploration_summary(stats)
        
        assert summary.boundary_status is not None
        assert isinstance(summary.boundary_status, BoundaryStatus)
