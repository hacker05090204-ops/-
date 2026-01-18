"""
Parallel Exploration Manager - Manages concurrent exploration threads

ARCHITECTURAL CONSTRAINTS:
    1. Parallel threads share GlobalExplorationBudget with atomic operations
    2. Each thread has isolated state (no cross-contamination)
    3. MCP submissions are coordinated (no duplicates)
    4. Rate limiting triggers automatic parallelism reduction
"""

import logging
import threading
import queue
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Callable
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from datetime import datetime, timezone

from .types import (
    Hypothesis,
    Observation,
    MCPClassification,
    ExplorationStats,
    RateLimitStatus,
)
from .boundary import GlobalExplorationBudget, BoundaryManager
from .client import MCPClient
from .errors import MCPUnavailableError, BoundaryExceededError

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


@dataclass
class ThreadState:
    """Isolated state for a single exploration thread.
    
    ARCHITECTURAL CONSTRAINT:
        Each thread has its own state to prevent cross-contamination.
    """
    thread_id: int
    hypotheses_tested: int = 0
    observations_submitted: int = 0
    bugs_found: int = 0
    signals_found: int = 0
    errors: int = 0
    started_at: datetime = field(default_factory=_utc_now)
    completed_at: Optional[datetime] = None


@dataclass
class ParallelResult:
    """Result from parallel exploration."""
    thread_id: int
    hypothesis_id: str
    classification: Optional[MCPClassification] = None
    error: Optional[str] = None
    success: bool = True


class SubmissionCoordinator:
    """Coordinates MCP submissions across threads.
    
    ARCHITECTURAL CONSTRAINT:
        Prevents duplicate submissions and coordinates rate limiting.
    """
    
    def __init__(self, mcp_client: MCPClient):
        self._client = mcp_client
        self._submitted: Set[str] = set()
        self._lock = threading.Lock()
        self._submission_queue: queue.Queue = queue.Queue()
    
    def try_submit(self, observation: Observation) -> Optional[MCPClassification]:
        """Try to submit observation if not already submitted.
        
        Thread-safe submission with duplicate prevention.
        
        Args:
            observation: Observation to submit
            
        Returns:
            MCPClassification if submitted, None if duplicate
        """
        with self._lock:
            if observation.id in self._submitted:
                logger.debug(f"Skipping duplicate submission: {observation.id}")
                return None
            self._submitted.add(observation.id)
        
        # Submit outside lock to avoid blocking
        return self._client.submit_observation(observation)
    
    def is_submitted(self, observation_id: str) -> bool:
        """Check if observation was already submitted."""
        with self._lock:
            return observation_id in self._submitted
    
    def get_submission_count(self) -> int:
        """Get total submission count."""
        with self._lock:
            return len(self._submitted)


class ParallelExplorationManager:
    """Manages concurrent exploration threads.
    
    ARCHITECTURAL CONSTRAINTS:
        - Threads share GlobalExplorationBudget with atomic operations
        - Each thread has isolated state
        - MCP submissions are coordinated (no duplicates)
        - Rate limiting triggers automatic parallelism reduction
    """
    
    DEFAULT_MAX_WORKERS = 4
    MIN_WORKERS = 1
    
    def __init__(
        self,
        mcp_client: MCPClient,
        boundary_manager: BoundaryManager,
        max_workers: int = DEFAULT_MAX_WORKERS
    ):
        """Initialize parallel exploration manager.
        
        Args:
            mcp_client: Client for MCP submissions
            boundary_manager: Manager for exploration boundaries
            max_workers: Maximum number of parallel workers
        """
        self._mcp_client = mcp_client
        self._boundary_manager = boundary_manager
        self._max_workers = max_workers
        self._current_workers = max_workers
        self._coordinator = SubmissionCoordinator(mcp_client)
        self._thread_states: Dict[int, ThreadState] = {}
        self._lock = threading.Lock()
        self._rate_limited = False
    
    def explore_parallel(
        self,
        hypotheses: List[Hypothesis],
        executor_fn: Callable[[Hypothesis], Observation]
    ) -> List[ParallelResult]:
        """Execute hypotheses in parallel.
        
        Args:
            hypotheses: Hypotheses to test
            executor_fn: Function to execute a hypothesis and return observation
            
        Returns:
            List of results from parallel execution
        """
        results = []
        budget = self._boundary_manager.budget
        
        # Check if we can continue
        if budget.is_exhausted():
            raise BoundaryExceededError("Budget exhausted before parallel exploration")
        
        with ThreadPoolExecutor(max_workers=self._current_workers) as executor:
            futures: Dict[Future, Hypothesis] = {}
            
            for hypothesis in hypotheses:
                # Check budget before submitting
                if not budget.consume_action():
                    logger.info("Action budget exhausted, stopping submission")
                    break
                
                future = executor.submit(
                    self._execute_hypothesis,
                    hypothesis,
                    executor_fn,
                    len(futures),  # thread_id
                )
                futures[future] = hypothesis
            
            # Collect results
            for future in as_completed(futures):
                hypothesis = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Check for rate limiting
                    if self._check_rate_limit():
                        self._reduce_parallelism()
                        
                except Exception as e:
                    logger.error(f"Thread error for {hypothesis.id}: {e}")
                    results.append(ParallelResult(
                        thread_id=-1,
                        hypothesis_id=hypothesis.id,
                        error=str(e),
                        success=False,
                    ))
        
        return results
    
    def _execute_hypothesis(
        self,
        hypothesis: Hypothesis,
        executor_fn: Callable[[Hypothesis], Observation],
        thread_id: int
    ) -> ParallelResult:
        """Execute a single hypothesis in a thread.
        
        Args:
            hypothesis: Hypothesis to test
            executor_fn: Function to execute hypothesis
            thread_id: ID of this thread
            
        Returns:
            ParallelResult with classification or error
        """
        # Initialize thread state
        with self._lock:
            if thread_id not in self._thread_states:
                self._thread_states[thread_id] = ThreadState(thread_id=thread_id)
            state = self._thread_states[thread_id]
        
        try:
            # Execute hypothesis to get observation
            observation = executor_fn(hypothesis)
            
            # Check submission budget
            if not self._boundary_manager.budget.consume_submission():
                return ParallelResult(
                    thread_id=thread_id,
                    hypothesis_id=hypothesis.id,
                    error="Submission budget exhausted",
                    success=False,
                )
            
            # Submit to MCP via coordinator (prevents duplicates)
            classification = self._coordinator.try_submit(observation)
            
            if classification is None:
                return ParallelResult(
                    thread_id=thread_id,
                    hypothesis_id=hypothesis.id,
                    error="Duplicate submission skipped",
                    success=False,
                )
            
            # Update thread state
            with self._lock:
                state.hypotheses_tested += 1
                state.observations_submitted += 1
                if classification.is_bug():
                    state.bugs_found += 1
                elif classification.is_signal():
                    state.signals_found += 1
            
            return ParallelResult(
                thread_id=thread_id,
                hypothesis_id=hypothesis.id,
                classification=classification,
                success=True,
            )
            
        except MCPUnavailableError as e:
            # MCP unavailable - HARD STOP
            raise
        except Exception as e:
            with self._lock:
                state.errors += 1
            return ParallelResult(
                thread_id=thread_id,
                hypothesis_id=hypothesis.id,
                error=str(e),
                success=False,
            )
    
    def _check_rate_limit(self) -> bool:
        """Check if rate limiting is active."""
        try:
            status = self._mcp_client.check_rate_limit()
            if status == RateLimitStatus.EXCEEDED:
                self._rate_limited = True
                return True
            elif status == RateLimitStatus.APPROACHING:
                return True
        except Exception:
            pass
        return False
    
    def _reduce_parallelism(self) -> None:
        """Reduce parallelism due to rate limiting."""
        with self._lock:
            if self._current_workers > self.MIN_WORKERS:
                self._current_workers = max(
                    self.MIN_WORKERS,
                    self._current_workers // 2
                )
                logger.warning(
                    f"Rate limiting detected, reducing workers to {self._current_workers}"
                )
    
    def merge_results(
        self,
        results: List[ParallelResult]
    ) -> ExplorationStats:
        """Merge results from parallel execution.
        
        Args:
            results: Results from parallel exploration
            
        Returns:
            Merged exploration statistics
        """
        stats = ExplorationStats()
        
        for result in results:
            if result.success and result.classification:
                stats.observations_submitted += 1
                stats.hypotheses_tested += 1
                
                if result.classification.is_bug():
                    stats.bugs_found += 1
                elif result.classification.is_signal():
                    stats.signals_found += 1
                elif result.classification.is_no_issue():
                    stats.no_issues += 1
                elif result.classification.is_coverage_gap():
                    stats.coverage_gaps += 1
            else:
                stats.errors_encountered += 1
        
        return stats
    
    def get_thread_states(self) -> Dict[int, ThreadState]:
        """Get states of all threads."""
        with self._lock:
            return self._thread_states.copy()
    
    def get_current_workers(self) -> int:
        """Get current number of workers."""
        return self._current_workers
    
    def is_rate_limited(self) -> bool:
        """Check if currently rate limited."""
        return self._rate_limited
    
    def reset(self) -> None:
        """Reset manager state."""
        with self._lock:
            self._thread_states.clear()
            self._current_workers = self._max_workers
            self._rate_limited = False
