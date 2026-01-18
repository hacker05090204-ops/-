"""
Execution Layer Recovery & Resilience Module

Tracks #5: Browser Failure Handling
Scope: Tasks 23.2, 23.3, 23.5, 23.8

This module provides the logic to detect browser crashes and manage safe restarts.
It enforces restart limits and safety constraints.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict
from datetime import datetime, timezone

from execution_layer.errors import (
    BrowserFailure,
    BrowserCrashError,
    BrowserTimeoutError,
    BrowserDisconnectError,
    ExecutionLayerError,
)

# Logger setup
logger = logging.getLogger("execution_layer.recovery")

@dataclass
class ResilienceConfig:
    """Configuration for browser resilience."""
    max_restarts_per_decision: int = 3
    max_restarts_total: int = 10
    restart_delay_seconds: float = 1.0
    enable_crash_detection: bool = True


@dataclass
class FailureState:
    """Track failure counts for a decision."""
    decision_id: str
    restart_count: int = 0
    last_failure_time: Optional[datetime] = None
    failure_history: list[Dict[str, str]] = field(default_factory=list)


class CrashDetector:
    """Detects if browser process is dead or unresponsive."""
    
    @staticmethod
    def is_process_alive(pid: int) -> bool:
        """Check if process is running (POSIX only)."""
        if pid <= 0:
            return False
        try:
            # Signal 0 does nothing but checks access
            import os
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            # Process exists but we can't signal it (still alive)
            return True
        except Exception:
            return False


class BrowserResilienceManager:
    """Manages browser recovery and failure tracking."""
    
    def __init__(self, config: ResilienceConfig = ResilienceConfig()):
        self.config = config
        self._states: Dict[str, FailureState] = {}
        self._total_restarts = 0
    
    def get_state(self, decision_id: str) -> FailureState:
        """Get or create failure state for a decision."""
        if decision_id not in self._states:
            self._states[decision_id] = FailureState(decision_id=decision_id)
        return self._states[decision_id]
    
    def record_failure(self, decision_id: str, error: Exception) -> None:
        """Log a failure event."""
        state = self.get_state(decision_id)
        state.last_failure_time = datetime.now(timezone.utc)
        state.failure_history.append({
            "timestamp": state.last_failure_time.isoformat(),
            "error_type": type(error).__name__,
            "error_msg": str(error),
        })
        logger.warning(f"Recorded failure for decision {decision_id}: {error}")
    
    def can_restart(self, decision_id: str) -> bool:
        """Check if restart is allowed under governance limits."""
        state = self.get_state(decision_id)
        
        # Global limit check
        if self._total_restarts >= self.config.max_restarts_total:
            logger.error("Global restart limit reached.")
            return False
            
        # Per-decision limit check
        if state.restart_count >= self.config.max_restarts_per_decision:
            logger.error(f"Decision {decision_id} restart limit reached ({state.restart_count}).")
            return False
            
        return True
    
    async def wait_before_restart(self) -> None:
        """Enforce delay before restart to prevent rapid looping."""
        await asyncio.sleep(self.config.restart_delay_seconds)
    
    def increment_restart_count(self, decision_id: str) -> None:
        """Increment restart counters."""
        state = self.get_state(decision_id)
        state.restart_count += 1
        self._total_restarts += 1
        logger.info(f"Restart authorized for {decision_id}. Count: {state.restart_count}")

    def should_recover(self, error: Exception) -> bool:
        """Determine if an error is recoverable."""
        return isinstance(error, BrowserFailure)

