"""
Execution Layer Retry Policy

Explicit timeout and retry policies with exponential backoff.

OBSERVE ONLY — NO STEALTH, NO EVASION, NO BYPASS.

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TypeVar, Callable, Awaitable, Optional
import asyncio
import logging

from execution_layer.errors import RetryExhaustedError


logger = logging.getLogger(__name__)
T = TypeVar("T")


@dataclass
class RetryPolicy:
    """Retry policy with exponential backoff."""
    max_retries: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    exponential_base: float = 2.0
    
    # Status codes to retry
    retry_status_codes: tuple[int, ...] = (429, 500, 502, 503, 504)
    
    # Status codes to NOT retry (client errors)
    no_retry_status_codes: tuple[int, ...] = (400, 401, 403, 404, 405, 422)
    
    def should_retry_status(self, status_code: int) -> bool:
        """Check if status code should trigger retry."""
        if status_code in self.no_retry_status_codes:
            return False
        return status_code in self.retry_status_codes


@dataclass
class RetryAttempt:
    """Record of a retry attempt."""
    attempt_number: int
    timestamp: datetime
    delay_seconds: float
    reason: str
    success: bool
    error: Optional[str] = None


class RetryExecutor:
    """Execute operations with retry policy.
    
    OBSERVE ONLY — NO STEALTH, NO EVASION, NO BYPASS.
    """
    
    def __init__(self, policy: Optional[RetryPolicy] = None) -> None:
        self._policy = policy or RetryPolicy()
        self._attempts: list[RetryAttempt] = []
    
    async def execute_with_retry(
        self,
        operation: Callable[[], Awaitable[T]],
        operation_name: str,
    ) -> T:
        """Execute operation with retry policy.
        
        Raises:
            RetryExhaustedError: After all retries fail (HARD FAIL)
        """
        last_error: Optional[Exception] = None
        
        for attempt in range(self._policy.max_retries + 1):
            delay = self._calculate_delay(attempt) if attempt > 0 else 0.0
            
            if delay > 0:
                logger.info(
                    f"Retry {attempt}/{self._policy.max_retries} for {operation_name} "
                    f"after {delay:.2f}s delay"
                )
                await asyncio.sleep(delay)
            
            try:
                result = await operation()
                self._attempts.append(RetryAttempt(
                    attempt_number=attempt,
                    timestamp=datetime.now(timezone.utc),
                    delay_seconds=delay,
                    reason="initial" if attempt == 0 else "retry",
                    success=True,
                ))
                return result
            except Exception as e:
                last_error = e
                self._attempts.append(RetryAttempt(
                    attempt_number=attempt,
                    timestamp=datetime.now(timezone.utc),
                    delay_seconds=delay,
                    reason="initial" if attempt == 0 else "retry",
                    success=False,
                    error=str(e),
                ))
                logger.warning(
                    f"Attempt {attempt + 1}/{self._policy.max_retries + 1} "
                    f"for {operation_name} failed: {e}"
                )
        
        raise RetryExhaustedError(
            f"All {self._policy.max_retries + 1} attempts for {operation_name} "
            f"failed. Last error: {last_error} — HARD FAIL"
        )

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff."""
        if attempt == 0:
            return 0.0
        delay = self._policy.base_delay_seconds * (
            self._policy.exponential_base ** (attempt - 1)
        )
        return min(delay, self._policy.max_delay_seconds)
    
    def get_attempts(self) -> list[RetryAttempt]:
        """Get all retry attempts for audit."""
        return list(self._attempts)
    
    def clear_attempts(self) -> None:
        """Clear retry attempt history."""
        self._attempts.clear()
