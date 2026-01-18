"""
Test Execution Layer Duplicate Handler

Tests for duplicate exploration STOP conditions.
"""

import pytest

from execution_layer.types import SafeActionType, SafeAction, DuplicateExplorationConfig
from execution_layer.duplicate import DuplicateHandler, DuplicateCandidate, ExplorationState
from execution_layer.errors import DuplicateExplorationLimitError


class TestDuplicateHandler:
    """Test DuplicateHandler class."""
    
    @pytest.fixture
    def handler(self):
        return DuplicateHandler()
    
    @pytest.fixture
    def action(self):
        return SafeAction(
            action_id="test-1",
            action_type=SafeActionType.NAVIGATE,
            target="https://example.com",
            parameters={},
            description="Test",
        )
    
    def test_start_exploration(self, handler):
        """Should start exploration."""
        state = handler.start_exploration("finding-1")
        assert state.exploration_id
        assert state.original_finding_id == "finding-1"
        assert state.current_depth == 0
        assert state.hypotheses_generated == 0
    
    def test_generate_hypothesis(self, handler):
        """Should generate hypothesis."""
        state = handler.start_exploration("finding-1")
        hypothesis = handler.generate_hypothesis(
            state.exploration_id,
            {"type": "variant", "data": "test"},
        )
        assert hypothesis["hypothesis_id"]
        assert hypothesis["exploration_id"] == state.exploration_id
    
    def test_record_action(self, handler, action):
        """Should record action in exploration."""
        state = handler.start_exploration("finding-1")
        handler.record_action(state.exploration_id, action)
        
        updated_state = handler.get_exploration(state.exploration_id)
        assert updated_state.total_actions == 1
    
    def test_increment_depth(self, handler):
        """Should increment exploration depth."""
        state = handler.start_exploration("finding-1")
        new_depth = handler.increment_depth(state.exploration_id)
        assert new_depth == 1


class TestDuplicateExplorationLimits:
    """Test duplicate exploration STOP conditions."""
    
    @pytest.fixture
    def config(self):
        return DuplicateExplorationConfig(
            max_depth=2,
            max_hypotheses=3,
            max_total_actions=5,
        )
    
    @pytest.fixture
    def handler(self, config):
        return DuplicateHandler(config)
    
    @pytest.fixture
    def action(self):
        return SafeAction(
            action_id="test-1",
            action_type=SafeActionType.NAVIGATE,
            target="https://example.com",
            parameters={},
            description="Test",
        )
    
    def test_max_depth_limit(self, handler):
        """Should stop at max_depth."""
        state = handler.start_exploration("finding-1")
        
        # First two increments should succeed
        handler.increment_depth(state.exploration_id)
        handler.increment_depth(state.exploration_id)
        
        # Third increment should fail (max_depth=2)
        with pytest.raises(DuplicateExplorationLimitError, match="Maximum depth"):
            handler.increment_depth(state.exploration_id)
    
    def test_max_hypotheses_limit(self, handler):
        """Should stop at max_hypotheses."""
        state = handler.start_exploration("finding-1")
        
        # First three hypotheses should succeed
        for i in range(3):
            handler.generate_hypothesis(state.exploration_id, {"index": i})
        
        # Fourth hypothesis should fail (max_hypotheses=3)
        with pytest.raises(DuplicateExplorationLimitError, match="Maximum hypotheses"):
            handler.generate_hypothesis(state.exploration_id, {"index": 3})
    
    def test_max_total_actions_limit(self, handler, action):
        """Should stop at max_total_actions."""
        state = handler.start_exploration("finding-1")
        
        # First five actions should succeed
        for _ in range(5):
            handler.record_action(state.exploration_id, action)
        
        # Sixth action should fail (max_total_actions=5)
        with pytest.raises(DuplicateExplorationLimitError, match="Maximum total actions"):
            handler.record_action(state.exploration_id, action)
    
    def test_exploration_stopped_flag(self, handler):
        """Should set stopped flag when limit reached."""
        state = handler.start_exploration("finding-1")
        
        # Exceed max_depth
        handler.increment_depth(state.exploration_id)
        handler.increment_depth(state.exploration_id)
        
        try:
            handler.increment_depth(state.exploration_id)
        except DuplicateExplorationLimitError:
            pass
        
        assert handler.is_exploration_stopped(state.exploration_id)


class TestHumanDecision:
    """Test human decision recording."""
    
    @pytest.fixture
    def handler(self):
        return DuplicateHandler()
    
    def test_record_human_decision(self, handler):
        """Should record human decision."""
        handler.record_human_decision("finding-1", is_duplicate=True)
        assert handler.get_human_decision("finding-1") is True
    
    def test_record_not_duplicate(self, handler):
        """Should record not-duplicate decision."""
        handler.record_human_decision("finding-1", is_duplicate=False)
        assert handler.get_human_decision("finding-1") is False
    
    def test_no_decision_returns_none(self, handler):
        """Should return None if no decision recorded."""
        assert handler.get_human_decision("finding-1") is None


class TestDuplicateDetection:
    """Test duplicate detection logic."""
    
    @pytest.fixture
    def handler(self):
        return DuplicateHandler()
    
    def test_detect_similar_finding(self, handler):
        """Should detect similar finding."""
        # Use identical fields to ensure high similarity (>= 0.8)
        existing = [
            {
                "finding_id": "existing-1",
                "type": "xss",
                "url": "https://example.com",
                "severity": "high",
                "endpoint": "/api/test",
            },
        ]
        new_finding = {
            "finding_id": "existing-1",  # Same finding_id for 100% match
            "type": "xss",
            "url": "https://example.com",
            "severity": "high",
            "endpoint": "/api/test",
        }
        
        candidate = handler.detect_duplicate("new-1", new_finding, existing)
        assert candidate is not None
        assert candidate.original_finding_id == "existing-1"
        assert candidate.similarity_score >= 0.8
    
    def test_no_duplicate_for_different_finding(self, handler):
        """Should not detect duplicate for different finding."""
        existing = [
            {"finding_id": "existing-1", "type": "xss", "url": "https://example.com"},
        ]
        new_finding = {"finding_id": "new-1", "type": "sqli", "url": "https://other.com"}
        
        candidate = handler.detect_duplicate("new-1", new_finding, existing)
        assert candidate is None
