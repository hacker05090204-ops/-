"""
Retry Manager - Handles retries with parameter variations

ARCHITECTURAL CONSTRAINTS:
    1. Retries are BOUNDED (max retry count)
    2. Failure patterns are recorded for analysis
    3. Persistent failures escalate to human review
    4. Retries do NOT bypass MCP classification
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from enum import Enum, auto
from datetime import datetime, timezone

from .types import (
    Hypothesis,
    Observation,
    ExplorationAction,
    MCPClassification,
)
from .errors import ExplorationError, MCPUnavailableError

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class RetryReason(Enum):
    """Reasons for retry."""
    TIMEOUT = auto()
    NETWORK_ERROR = auto()
    RATE_LIMITED = auto()
    TRANSIENT_ERROR = auto()
    PARAMETER_VARIATION = auto()


@dataclass
class RetryAttempt:
    """Record of a retry attempt."""
    attempt_number: int
    reason: RetryReason
    parameters: Dict[str, Any]
    timestamp: datetime = field(default_factory=_utc_now)
    success: bool = False
    error_message: Optional[str] = None


@dataclass
class FailurePattern:
    """Pattern of failures for analysis."""
    hypothesis_id: str
    failure_count: int = 0
    retry_count: int = 0
    last_error: Optional[str] = None
    error_types: List[str] = field(default_factory=list)
    needs_human_review: bool = False


class RetryManager:
    """Manages retries with parameter variations.
    
    ARCHITECTURAL CONSTRAINTS:
        - Retries are BOUNDED
        - Failure patterns are recorded
        - Persistent failures escalate to human review
        - Retries do NOT bypass MCP classification
    """
    
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BACKOFF_BASE = 1.0  # seconds
    DEFAULT_BACKOFF_MULTIPLIER = 2.0
    ESCALATION_THRESHOLD = 5  # Escalate after 5 failures
    
    def __init__(
        self,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_base: float = DEFAULT_BACKOFF_BASE,
        backoff_multiplier: float = DEFAULT_BACKOFF_MULTIPLIER
    ):
        """Initialize retry manager.
        
        Args:
            max_retries: Maximum retry attempts per hypothesis
            backoff_base: Base backoff time in seconds
            backoff_multiplier: Multiplier for exponential backoff
        """
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._backoff_multiplier = backoff_multiplier
        self._failure_patterns: Dict[str, FailurePattern] = {}
        self._retry_history: Dict[str, List[RetryAttempt]] = {}
    
    def execute_with_retry(
        self,
        hypothesis: Hypothesis,
        executor_fn: Callable[[Hypothesis], MCPClassification],
        variation_fn: Optional[Callable[[Hypothesis, int], Hypothesis]] = None
    ) -> Optional[MCPClassification]:
        """Execute hypothesis with retry logic.
        
        Args:
            hypothesis: Hypothesis to execute
            executor_fn: Function to execute hypothesis
            variation_fn: Optional function to vary parameters on retry
            
        Returns:
            MCPClassification if successful, None if all retries failed
            
        Raises:
            MCPUnavailableError: If MCP is unavailable (HARD STOP)
        """
        attempts = []
        last_error = None
        
        for attempt in range(self._max_retries + 1):
            try:
                # Apply variation on retry
                current_hypothesis = hypothesis
                if attempt > 0 and variation_fn:
                    current_hypothesis = variation_fn(hypothesis, attempt)
                    logger.info(f"Retry {attempt} with parameter variation")
                
                # Execute
                classification = executor_fn(current_hypothesis)
                
                # Record success
                attempts.append(RetryAttempt(
                    attempt_number=attempt,
                    reason=RetryReason.PARAMETER_VARIATION if attempt > 0 else RetryReason.TRANSIENT_ERROR,
                    parameters=self._extract_parameters(current_hypothesis),
                    success=True,
                ))
                
                self._retry_history[hypothesis.id] = attempts
                return classification
                
            except MCPUnavailableError:
                # MCP unavailable - HARD STOP, do not retry
                raise
                
            except ExplorationError as e:
                last_error = str(e)
                reason = self._classify_error(e)
                
                attempts.append(RetryAttempt(
                    attempt_number=attempt,
                    reason=reason,
                    parameters=self._extract_parameters(hypothesis),
                    success=False,
                    error_message=last_error,
                ))
                
                # Record failure pattern
                self._record_failure(hypothesis.id, last_error, type(e).__name__)
                
                # Check if should retry
                if attempt < self._max_retries:
                    backoff = self._calculate_backoff(attempt)
                    logger.info(f"Retry {attempt + 1}/{self._max_retries} after {backoff}s")
                    time.sleep(backoff)
                else:
                    logger.warning(f"Max retries exceeded for {hypothesis.id}")
                    
            except Exception as e:
                last_error = str(e)
                self._record_failure(hypothesis.id, last_error, type(e).__name__)
                
                if attempt >= self._max_retries:
                    break
                    
                backoff = self._calculate_backoff(attempt)
                time.sleep(backoff)
        
        # All retries failed
        self._retry_history[hypothesis.id] = attempts
        self._check_escalation(hypothesis.id)
        return None
    
    def _classify_error(self, error: Exception) -> RetryReason:
        """Classify error for retry reason."""
        error_str = str(error).lower()
        
        if "timeout" in error_str:
            return RetryReason.TIMEOUT
        elif "rate" in error_str or "limit" in error_str:
            return RetryReason.RATE_LIMITED
        elif "network" in error_str or "connection" in error_str:
            return RetryReason.NETWORK_ERROR
        else:
            return RetryReason.TRANSIENT_ERROR
    
    def _calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff time."""
        return self._backoff_base * (self._backoff_multiplier ** attempt)
    
    def _extract_parameters(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        """Extract parameters from hypothesis for logging."""
        return {
            "id": hypothesis.id,
            "description": hypothesis.description[:50],
            "testability": hypothesis.testability_score,
        }
    
    def _record_failure(
        self,
        hypothesis_id: str,
        error_message: str,
        error_type: str
    ) -> None:
        """Record failure pattern."""
        if hypothesis_id not in self._failure_patterns:
            self._failure_patterns[hypothesis_id] = FailurePattern(
                hypothesis_id=hypothesis_id
            )
        
        pattern = self._failure_patterns[hypothesis_id]
        pattern.failure_count += 1
        pattern.last_error = error_message
        
        if error_type not in pattern.error_types:
            pattern.error_types.append(error_type)
    
    def _check_escalation(self, hypothesis_id: str) -> None:
        """Check if failure should be escalated to human review."""
        pattern = self._failure_patterns.get(hypothesis_id)
        
        if pattern and pattern.failure_count >= self.ESCALATION_THRESHOLD:
            pattern.needs_human_review = True
            logger.warning(
                f"Hypothesis {hypothesis_id} escalated to human review "
                f"after {pattern.failure_count} failures"
            )
    
    def get_failure_pattern(self, hypothesis_id: str) -> Optional[FailurePattern]:
        """Get failure pattern for a hypothesis."""
        return self._failure_patterns.get(hypothesis_id)
    
    def get_retry_history(self, hypothesis_id: str) -> List[RetryAttempt]:
        """Get retry history for a hypothesis."""
        return self._retry_history.get(hypothesis_id, [])
    
    def get_escalated_hypotheses(self) -> List[str]:
        """Get list of hypotheses needing human review."""
        return [
            h_id for h_id, pattern in self._failure_patterns.items()
            if pattern.needs_human_review
        ]
    
    def get_failure_summary(self) -> Dict[str, int]:
        """Get summary of failures by error type."""
        summary: Dict[str, int] = {}
        
        for pattern in self._failure_patterns.values():
            for error_type in pattern.error_types:
                summary[error_type] = summary.get(error_type, 0) + 1
        
        return summary
    
    def reset(self) -> None:
        """Reset retry manager state."""
        self._failure_patterns.clear()
        self._retry_history.clear()
