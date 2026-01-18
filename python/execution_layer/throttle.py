"""
Execution Layer Per-Host Throttling

Enforces rate limiting per target host to prevent abuse and detection.
MANDATORY: All executions MUST pass through throttle validation.

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional
from urllib.parse import urlparse
import time

from execution_layer.errors import (
    ThrottleConfigError,
    ThrottleLimitExceededError,
)


@dataclass
class ExecutionThrottleConfig:
    """Configuration for per-host throttling.
    
    MANDATORY: This config MUST be provided. HARD FAIL if missing.
    
    Attributes:
        min_delay_per_action_seconds: Minimum delay between actions (default: 2.0)
        max_actions_per_host_per_minute: Maximum actions per host per minute (default: 10)
        burst_allowance: Allow burst of actions before throttling (default: 3)
    """
    min_delay_per_action_seconds: float = 2.0
    max_actions_per_host_per_minute: int = 10
    burst_allowance: int = 3
    
    def __post_init__(self) -> None:
        if self.min_delay_per_action_seconds < 0.5:
            raise ThrottleConfigError(
                f"min_delay_per_action_seconds must be >= 0.5, got {self.min_delay_per_action_seconds}"
            )
        if self.min_delay_per_action_seconds > 60.0:
            raise ThrottleConfigError(
                f"min_delay_per_action_seconds must be <= 60.0, got {self.min_delay_per_action_seconds}"
            )
        if self.max_actions_per_host_per_minute < 1:
            raise ThrottleConfigError(
                f"max_actions_per_host_per_minute must be >= 1, got {self.max_actions_per_host_per_minute}"
            )
        if self.max_actions_per_host_per_minute > 60:
            raise ThrottleConfigError(
                f"max_actions_per_host_per_minute must be <= 60, got {self.max_actions_per_host_per_minute}"
            )
        if self.burst_allowance < 0:
            raise ThrottleConfigError(
                f"burst_allowance must be >= 0, got {self.burst_allowance}"
            )


@dataclass
class HostActionRecord:
    """Record of actions against a specific host."""
    host: str
    action_timestamps: list[datetime] = field(default_factory=list)
    last_action_at: Optional[datetime] = None
    
    def record_action(self) -> None:
        """Record an action against this host."""
        now = datetime.now(timezone.utc)
        self.action_timestamps.append(now)
        self.last_action_at = now
        # Prune old timestamps (older than 1 minute)
        cutoff = now - timedelta(minutes=1)
        self.action_timestamps = [t for t in self.action_timestamps if t > cutoff]
    
    def actions_in_last_minute(self) -> int:
        """Count actions in the last minute."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=1)
        return len([t for t in self.action_timestamps if t > cutoff])
    
    def seconds_since_last_action(self) -> Optional[float]:
        """Get seconds since last action, or None if no actions."""
        if self.last_action_at is None:
            return None
        now = datetime.now(timezone.utc)
        return (now - self.last_action_at).total_seconds()


@dataclass
class ThrottleDecision:
    """Result of throttle check."""
    allowed: bool
    wait_seconds: float = 0.0
    reason: str = ""
    host: str = ""
    actions_in_window: int = 0


class ExecutionThrottle:
    """Per-host throttle enforcer.
    
    MANDATORY: All executions MUST pass through throttle validation.
    - Enforces minimum delay between actions
    - Enforces maximum actions per host per minute
    - Logs all throttle decisions to audit log
    - HARD FAIL if config is missing or invalid
    """
    
    def __init__(self, config: ExecutionThrottleConfig) -> None:
        if config is None:
            raise ThrottleConfigError("ExecutionThrottleConfig is REQUIRED — HARD FAIL")
        self._config = config
        self._host_records: dict[str, HostActionRecord] = {}
        self._throttle_log: list[ThrottleDecision] = []
    
    def extract_host(self, target: str) -> str:
        """Extract host from target URL or return target as-is."""
        if target.startswith(("http://", "https://")):
            parsed = urlparse(target)
            return parsed.netloc.lower()
        return target.lower()
    
    def check_throttle(self, target: str) -> ThrottleDecision:
        """Check if action against target is allowed.
        
        Returns:
            ThrottleDecision with allowed=True if action can proceed,
            or allowed=False with wait_seconds indicating required delay.
        """
        host = self.extract_host(target)
        
        # Get or create host record
        if host not in self._host_records:
            self._host_records[host] = HostActionRecord(host=host)
        
        record = self._host_records[host]
        actions_in_window = record.actions_in_last_minute()
        
        # Check rate limit
        if actions_in_window >= self._config.max_actions_per_host_per_minute:
            decision = ThrottleDecision(
                allowed=False,
                wait_seconds=60.0,  # Wait full minute
                reason=f"Rate limit exceeded: {actions_in_window}/{self._config.max_actions_per_host_per_minute} actions/minute",
                host=host,
                actions_in_window=actions_in_window,
            )
            self._throttle_log.append(decision)
            return decision
        
        # Check minimum delay (with burst allowance)
        seconds_since_last = record.seconds_since_last_action()
        if seconds_since_last is not None:
            if actions_in_window > self._config.burst_allowance:
                if seconds_since_last < self._config.min_delay_per_action_seconds:
                    wait_needed = self._config.min_delay_per_action_seconds - seconds_since_last
                    decision = ThrottleDecision(
                        allowed=False,
                        wait_seconds=wait_needed,
                        reason=f"Minimum delay not met: {seconds_since_last:.2f}s < {self._config.min_delay_per_action_seconds}s",
                        host=host,
                        actions_in_window=actions_in_window,
                    )
                    self._throttle_log.append(decision)
                    return decision
        
        # Action allowed
        decision = ThrottleDecision(
            allowed=True,
            wait_seconds=0.0,
            reason="Action allowed",
            host=host,
            actions_in_window=actions_in_window,
        )
        self._throttle_log.append(decision)
        return decision
    
    def record_action(self, target: str) -> None:
        """Record that an action was executed against target."""
        host = self.extract_host(target)
        if host not in self._host_records:
            self._host_records[host] = HostActionRecord(host=host)
        self._host_records[host].record_action()
    
    async def wait_if_needed(self, target: str) -> ThrottleDecision:
        """Check throttle and wait if needed. Raises on hard limit.
        
        Raises:
            ThrottleLimitExceededError: If rate limit exceeded (HARD FAIL)
        """
        import asyncio
        
        decision = self.check_throttle(target)
        
        if not decision.allowed:
            # Check if this is a hard rate limit (not just delay)
            if decision.actions_in_window >= self._config.max_actions_per_host_per_minute:
                raise ThrottleLimitExceededError(
                    f"Rate limit exceeded for host '{decision.host}': "
                    f"{decision.actions_in_window}/{self._config.max_actions_per_host_per_minute} "
                    f"actions/minute — HARD FAIL"
                )
            
            # Wait for minimum delay
            if decision.wait_seconds > 0:
                await asyncio.sleep(decision.wait_seconds)
                # Re-check after waiting
                decision = self.check_throttle(target)
        
        return decision
    
    def get_throttle_log(self) -> list[ThrottleDecision]:
        """Get all throttle decisions for audit."""
        return list(self._throttle_log)
    
    def get_host_stats(self, host: str) -> Optional[dict]:
        """Get stats for a specific host."""
        host = host.lower()
        if host not in self._host_records:
            return None
        record = self._host_records[host]
        return {
            "host": host,
            "actions_in_last_minute": record.actions_in_last_minute(),
            "last_action_at": record.last_action_at.isoformat() if record.last_action_at else None,
            "seconds_since_last_action": record.seconds_since_last_action(),
        }
    
    def reset_host(self, host: str) -> None:
        """Reset throttle state for a host (for testing)."""
        host = host.lower()
        if host in self._host_records:
            del self._host_records[host]
    
    def reset_all(self) -> None:
        """Reset all throttle state (for testing)."""
        self._host_records.clear()
        self._throttle_log.clear()
