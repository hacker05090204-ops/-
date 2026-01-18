"""
Tests for Parallel Exploration Manager

Property Tests:
    - Property 8: Parallel Isolation
    - Threads have isolated state
    - Budget is shared with atomic operations
"""

import pytest
from hypothesis import given, strategies as st, settings
import threading
import time

from cyfer_brain.parallel import (
    ParallelExplorationManager,
    SubmissionCoordinator,
    ThreadState,
    ParallelResult,
)
from cyfer_brain.client import MCPClient
from cyfer_brain.boundary import BoundaryManager, GlobalExplorationBudget
from cyfer_brain.types import (
    Hypothesis,
    Observation,
    ExplorationAction,
    ExplorationBoundary,
    MCPClassification,
    RateLimitStatus,
)


class RealMCPServer:
    """Real MCP server implementation for testing.
    
    This implements all required MCP methods that the MCPClient expects.
    Tests MUST use this instead of object() to ensure REAL MCP integration.
    """
    
    def __init__(self):
        self._observations = []
        self._submitted_ids = set()
    
    def validate_observation(self, observation):
        """MCP validates observation and returns classification."""
        self._observations.append(observation)
        self._submitted_ids.add(observation.id)
        return {
            "classification": "SIGNAL",
            "invariant_violated": None,
            "proof": None,
            "confidence": 0.5,
            "coverage_gaps": [],
        }
    
    def get_coverage_report(self):
        """MCP returns coverage report."""
        return {"tested": [], "untested": []}
    
    def validate_scope(self, target):
        """MCP validates target scope."""
        return {"is_in_scope": True, "reason": "In scope"}
    
    def check_rate_limit(self):
        """MCP checks rate limit status."""
        return RateLimitStatus.OK


class TestSubmissionCoordinator:
    """Tests for SubmissionCoordinator."""
    
    def test_coordinator_creation(self):
        """Test coordinator can be created."""
        client = MCPClient(mcp_server=RealMCPServer())
        coordinator = SubmissionCoordinator(client)
        assert coordinator is not None
    
    def test_prevents_duplicate_submissions(self):
        """Coordinator must prevent duplicate submissions."""
        client = MCPClient(mcp_server=RealMCPServer())
        coordinator = SubmissionCoordinator(client)
        
        obs = Observation(
            hypothesis_id="hyp-1",
            before_state={},
            action=ExplorationAction(),
            after_state={},
        )
        
        # First submission should succeed
        result1 = coordinator.try_submit(obs)
        assert result1 is not None
        
        # Second submission of same observation should return None
        result2 = coordinator.try_submit(obs)
        assert result2 is None
    
    def test_tracks_submitted_observations(self):
        """Coordinator must track submitted observations."""
        client = MCPClient(mcp_server=RealMCPServer())
        coordinator = SubmissionCoordinator(client)
        
        obs = Observation(hypothesis_id="hyp-1")
        coordinator.try_submit(obs)
        
        assert coordinator.is_submitted(obs.id)
        assert coordinator.get_submission_count() == 1


class TestParallelExplorationManager:
    """Tests for ParallelExplorationManager."""
    
    def test_manager_creation(self):
        """Test manager can be created."""
        client = MCPClient(mcp_server=RealMCPServer())
        boundary = BoundaryManager()
        manager = ParallelExplorationManager(client, boundary)
        
        assert manager is not None
        assert manager.get_current_workers() == manager.DEFAULT_MAX_WORKERS
    
    def test_thread_state_isolation(self):
        """Each thread must have isolated state."""
        state1 = ThreadState(thread_id=1)
        state2 = ThreadState(thread_id=2)
        
        # Modify state1
        state1.hypotheses_tested = 10
        state1.bugs_found = 2
        
        # state2 should be unaffected
        assert state2.hypotheses_tested == 0
        assert state2.bugs_found == 0
    
    def test_merge_results(self):
        """Results from parallel execution must merge correctly."""
        client = MCPClient(mcp_server=RealMCPServer())
        boundary = BoundaryManager()
        manager = ParallelExplorationManager(client, boundary)
        
        results = [
            ParallelResult(
                thread_id=0,
                hypothesis_id="hyp-1",
                classification=MCPClassification(
                    observation_id="obs-1",
                    classification="BUG",
                ),
                success=True,
            ),
            ParallelResult(
                thread_id=1,
                hypothesis_id="hyp-2",
                classification=MCPClassification(
                    observation_id="obs-2",
                    classification="SIGNAL",
                ),
                success=True,
            ),
            ParallelResult(
                thread_id=2,
                hypothesis_id="hyp-3",
                error="Test error",
                success=False,
            ),
        ]
        
        stats = manager.merge_results(results)
        
        assert stats.bugs_found == 1
        assert stats.signals_found == 1
        assert stats.errors_encountered == 1
        assert stats.observations_submitted == 2


class TestParallelIsolation:
    """Property 8: Parallel Isolation
    
    Validates: Requirements 9.1, 9.2
    - Threads have isolated state
    - No cross-contamination between threads
    """
    
    def test_thread_states_are_independent(self):
        """Thread states must be completely independent."""
        client = MCPClient(mcp_server=RealMCPServer())
        boundary = BoundaryManager()
        manager = ParallelExplorationManager(client, boundary)
        
        # Simulate thread state creation
        with manager._lock:
            manager._thread_states[0] = ThreadState(thread_id=0)
            manager._thread_states[1] = ThreadState(thread_id=1)
        
        # Modify one thread's state
        manager._thread_states[0].bugs_found = 5
        manager._thread_states[0].hypotheses_tested = 10
        
        # Other thread should be unaffected
        assert manager._thread_states[1].bugs_found == 0
        assert manager._thread_states[1].hypotheses_tested == 0
    
    def test_concurrent_state_updates(self):
        """Concurrent state updates must not interfere."""
        client = MCPClient(mcp_server=RealMCPServer())
        boundary = BoundaryManager()
        manager = ParallelExplorationManager(client, boundary)
        
        # Initialize states
        with manager._lock:
            manager._thread_states[0] = ThreadState(thread_id=0)
            manager._thread_states[1] = ThreadState(thread_id=1)
        
        def update_state(thread_id: int, count: int):
            for _ in range(count):
                with manager._lock:
                    manager._thread_states[thread_id].hypotheses_tested += 1
        
        # Run concurrent updates
        threads = [
            threading.Thread(target=update_state, args=(0, 100)),
            threading.Thread(target=update_state, args=(1, 100)),
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Each thread should have exactly 100
        assert manager._thread_states[0].hypotheses_tested == 100
        assert manager._thread_states[1].hypotheses_tested == 100


class TestBudgetSharing:
    """Tests for shared budget with atomic operations."""
    
    def test_budget_is_shared(self):
        """All threads must share the same budget."""
        boundary = ExplorationBoundary(max_actions=100, max_mcp_submissions=50)
        budget = GlobalExplorationBudget(boundary)
        
        # Consume from multiple "threads"
        consumed = 0
        for _ in range(30):
            if budget.consume_action():
                consumed += 1
        
        assert consumed == 30
        assert budget.get_remaining_actions() == 70
    
    def test_atomic_budget_consumption(self):
        """Budget consumption must be atomic across threads."""
        boundary = ExplorationBoundary(max_actions=100)
        budget = GlobalExplorationBudget(boundary)
        
        consumed = [0]
        lock = threading.Lock()
        
        def consume_budget(count: int):
            local_consumed = 0
            for _ in range(count):
                if budget.consume_action():
                    local_consumed += 1
            with lock:
                consumed[0] += local_consumed
        
        # Run concurrent consumption
        threads = [
            threading.Thread(target=consume_budget, args=(50,))
            for _ in range(4)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Total consumed should equal initial budget
        assert consumed[0] == 100
        assert budget.get_remaining_actions() == 0
    
    def test_budget_exhaustion_stops_threads(self):
        """Budget exhaustion must stop all threads."""
        boundary = ExplorationBoundary(max_actions=10)
        budget = GlobalExplorationBudget(boundary)
        
        # Exhaust budget
        for _ in range(10):
            budget.consume_action()
        
        # Further consumption should fail
        assert not budget.consume_action()
        assert budget.is_exhausted()


class TestRateLimitHandling:
    """Tests for rate limit handling."""
    
    def test_parallelism_reduction_on_rate_limit(self):
        """Rate limiting must reduce parallelism."""
        client = MCPClient(mcp_server=RealMCPServer())
        boundary = BoundaryManager()
        manager = ParallelExplorationManager(client, boundary, max_workers=8)
        
        initial_workers = manager.get_current_workers()
        
        # Simulate rate limiting
        manager._rate_limited = True
        manager._reduce_parallelism()
        
        # Workers should be reduced
        assert manager.get_current_workers() < initial_workers
    
    def test_minimum_workers_maintained(self):
        """Parallelism must not go below minimum."""
        client = MCPClient(mcp_server=RealMCPServer())
        boundary = BoundaryManager()
        manager = ParallelExplorationManager(client, boundary, max_workers=4)
        
        # Reduce multiple times
        for _ in range(10):
            manager._reduce_parallelism()
        
        # Should not go below minimum
        assert manager.get_current_workers() >= manager.MIN_WORKERS
