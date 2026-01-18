"""
Tests for Retry Manager

Property Tests:
    - Retries are bounded
    - Failure patterns are recorded
    - Escalation to human review works
"""

import pytest
from hypothesis import given, strategies as st, settings

from cyfer_brain.retry import (
    RetryManager,
    RetryAttempt,
    RetryReason,
    FailurePattern,
)
from cyfer_brain.types import (
    Hypothesis,
    MCPClassification,
)
from cyfer_brain.errors import ExplorationError, MCPUnavailableError


class TestRetryManager:
    """Tests for RetryManager."""
    
    def test_manager_creation(self):
        """Test manager can be created."""
        manager = RetryManager()
        assert manager is not None
        assert manager._max_retries == manager.DEFAULT_MAX_RETRIES
    
    def test_successful_execution_no_retry(self):
        """Successful execution should not retry."""
        manager = RetryManager()
        
        hypothesis = Hypothesis(description="Test")
        call_count = [0]
        
        def executor(h: Hypothesis) -> MCPClassification:
            call_count[0] += 1
            return MCPClassification(
                observation_id="obs-1",
                classification="SIGNAL",
            )
        
        result = manager.execute_with_retry(hypothesis, executor)
        
        assert result is not None
        assert result.classification == "SIGNAL"
        assert call_count[0] == 1  # Only called once
    
    def test_retry_on_exploration_error(self):
        """Should retry on ExplorationError."""
        manager = RetryManager(max_retries=2, backoff_base=0.01)
        
        hypothesis = Hypothesis(description="Test")
        call_count = [0]
        
        def executor(h: Hypothesis) -> MCPClassification:
            call_count[0] += 1
            if call_count[0] < 3:
                raise ExplorationError("Transient error")
            return MCPClassification(
                observation_id="obs-1",
                classification="SIGNAL",
            )
        
        result = manager.execute_with_retry(hypothesis, executor)
        
        assert result is not None
        assert call_count[0] == 3  # Initial + 2 retries
    
    def test_mcp_unavailable_no_retry(self):
        """MCPUnavailableError should NOT retry (HARD STOP)."""
        manager = RetryManager(max_retries=3)
        
        hypothesis = Hypothesis(description="Test")
        call_count = [0]
        
        def executor(h: Hypothesis) -> MCPClassification:
            call_count[0] += 1
            raise MCPUnavailableError("MCP is down")
        
        with pytest.raises(MCPUnavailableError):
            manager.execute_with_retry(hypothesis, executor)
        
        # Should only be called once - no retry on MCP unavailable
        assert call_count[0] == 1
    
    def test_max_retries_respected(self):
        """Should not exceed max retries."""
        manager = RetryManager(max_retries=2, backoff_base=0.01)
        
        hypothesis = Hypothesis(description="Test")
        call_count = [0]
        
        def executor(h: Hypothesis) -> MCPClassification:
            call_count[0] += 1
            raise ExplorationError("Always fails")
        
        result = manager.execute_with_retry(hypothesis, executor)
        
        assert result is None  # All retries failed
        assert call_count[0] == 3  # Initial + 2 retries


class TestRetryBounds:
    """Property tests for retry bounds."""
    
    @given(max_retries=st.integers(min_value=0, max_value=5))
    @settings(max_examples=10, deadline=None)  # Disable deadline for retry tests
    def test_retries_bounded_by_max(self, max_retries):
        """Retries must be bounded by max_retries."""
        manager = RetryManager(max_retries=max_retries, backoff_base=0.001)
        
        hypothesis = Hypothesis(description="Test")
        call_count = [0]
        
        def executor(h: Hypothesis) -> MCPClassification:
            call_count[0] += 1
            raise ExplorationError("Always fails")
        
        manager.execute_with_retry(hypothesis, executor)
        
        # Should be called exactly max_retries + 1 times
        assert call_count[0] == max_retries + 1


class TestFailurePatterns:
    """Tests for failure pattern recording."""
    
    def test_failure_pattern_recorded(self):
        """Failures should be recorded in patterns."""
        manager = RetryManager(max_retries=1, backoff_base=0.01)
        
        hypothesis = Hypothesis(description="Test")
        
        def executor(h: Hypothesis) -> MCPClassification:
            raise ExplorationError("Test error")
        
        manager.execute_with_retry(hypothesis, executor)
        
        pattern = manager.get_failure_pattern(hypothesis.id)
        
        assert pattern is not None
        assert pattern.failure_count >= 1
        assert "ExplorationError" in pattern.error_types
    
    def test_retry_history_recorded(self):
        """Retry attempts should be recorded in history."""
        manager = RetryManager(max_retries=2, backoff_base=0.01)
        
        hypothesis = Hypothesis(description="Test")
        
        def executor(h: Hypothesis) -> MCPClassification:
            raise ExplorationError("Test error")
        
        manager.execute_with_retry(hypothesis, executor)
        
        history = manager.get_retry_history(hypothesis.id)
        
        assert len(history) == 3  # Initial + 2 retries
        for attempt in history:
            assert isinstance(attempt, RetryAttempt)
            assert not attempt.success


class TestEscalation:
    """Tests for escalation to human review."""
    
    def test_escalation_after_threshold(self):
        """Should escalate after failure threshold."""
        manager = RetryManager(max_retries=0, backoff_base=0.01)
        manager.ESCALATION_THRESHOLD = 3
        
        hypothesis = Hypothesis(description="Test")
        
        def executor(h: Hypothesis) -> MCPClassification:
            raise ExplorationError("Always fails")
        
        # Execute multiple times to trigger escalation
        for _ in range(5):
            manager.execute_with_retry(hypothesis, executor)
        
        pattern = manager.get_failure_pattern(hypothesis.id)
        
        assert pattern is not None
        assert pattern.needs_human_review
        assert hypothesis.id in manager.get_escalated_hypotheses()
    
    def test_no_escalation_below_threshold(self):
        """Should not escalate below threshold."""
        manager = RetryManager(max_retries=0, backoff_base=0.01)
        manager.ESCALATION_THRESHOLD = 10
        
        hypothesis = Hypothesis(description="Test")
        
        def executor(h: Hypothesis) -> MCPClassification:
            raise ExplorationError("Always fails")
        
        # Execute fewer times than threshold
        for _ in range(3):
            manager.execute_with_retry(hypothesis, executor)
        
        pattern = manager.get_failure_pattern(hypothesis.id)
        
        assert pattern is not None
        assert not pattern.needs_human_review


class TestParameterVariation:
    """Tests for parameter variation on retry."""
    
    def test_variation_applied_on_retry(self):
        """Parameter variation should be applied on retry."""
        manager = RetryManager(max_retries=2, backoff_base=0.01)
        
        hypothesis = Hypothesis(description="Test", testability_score=0.5)
        variations_applied = []
        
        def variation_fn(h: Hypothesis, attempt: int) -> Hypothesis:
            varied = Hypothesis(
                description=f"{h.description} - variation {attempt}",
                testability_score=h.testability_score + (attempt * 0.1),
            )
            variations_applied.append(attempt)
            return varied
        
        call_count = [0]
        
        def executor(h: Hypothesis) -> MCPClassification:
            call_count[0] += 1
            if call_count[0] < 3:
                raise ExplorationError("Retry needed")
            return MCPClassification(
                observation_id="obs-1",
                classification="SIGNAL",
            )
        
        result = manager.execute_with_retry(hypothesis, executor, variation_fn)
        
        assert result is not None
        assert len(variations_applied) == 2  # Variations on retry 1 and 2


class TestFailureSummary:
    """Tests for failure summary."""
    
    def test_failure_summary(self):
        """Should provide summary of failures by type."""
        manager = RetryManager(max_retries=0, backoff_base=0.01)
        
        # Create different failure types
        for i in range(3):
            hypothesis = Hypothesis(description=f"Test {i}")
            
            def executor(h: Hypothesis) -> MCPClassification:
                raise ExplorationError("Error")
            
            manager.execute_with_retry(hypothesis, executor)
        
        summary = manager.get_failure_summary()
        
        assert "ExplorationError" in summary
        assert summary["ExplorationError"] >= 3
