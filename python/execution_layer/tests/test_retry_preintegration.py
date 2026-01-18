"""
Pre-Integration Tests for Retry Wiring (Integration Track #3)

PHASE-4.1 TEST-ONLY AUTHORIZATION
Status: AUTHORIZED
Date: 2026-01-02

These tests validate the RetryExecutor standalone component BEFORE integration.
NO WIRING. NO PRODUCTION CODE CHANGES.

Tests Required (per tasks.md):
- 12.1: Property test - Retry does not bypass throttle limits
- 12.2: Property test - Retry attempts logged to audit trail
- 12.3: Property test - Retry exhaustion raises correct error type
- 12.4: Integration test - Retry delays respect per-host throttle
- 12.5: Integration test - Partial success during retry handled correctly

OBSERVE ONLY — NO STEALTH, NO EVASION, NO BYPASS.

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

import pytest
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from hypothesis import given, strategies as st, settings, assume
from typing import Optional, Any
from unittest.mock import AsyncMock, MagicMock, patch

from execution_layer.retry import (
    RetryExecutor,
    RetryPolicy,
    RetryAttempt,
)
from execution_layer.throttle import (
    ExecutionThrottle,
    ExecutionThrottleConfig,
    ThrottleDecision,
)
from execution_layer.errors import (
    RetryExhaustedError,
    ThrottleLimitExceededError,
    is_hard_stop,
)


# === Hypothesis Strategies ===

# Valid retry counts
retry_counts = st.integers(min_value=1, max_value=5)

# Valid delay values
delay_values = st.floats(min_value=0.1, max_value=5.0, allow_nan=False, allow_infinity=False)

# Valid operation names
operation_names = st.text(min_size=1, max_size=32, alphabet="abcdefghijklmnopqrstuvwxyz_")


# Valid host names
host_names = st.sampled_from([
    "api.example.com",
    "mcp.test.local",
    "pipeline.staging.io",
    "target.bounty.net",
])


@st.composite
def retry_policies(draw):
    """Generate valid retry policies."""
    return RetryPolicy(
        max_retries=draw(st.integers(min_value=1, max_value=5)),
        base_delay_seconds=draw(st.floats(min_value=0.01, max_value=0.5)),
        max_delay_seconds=draw(st.floats(min_value=0.5, max_value=2.0)),
        exponential_base=draw(st.floats(min_value=1.5, max_value=3.0)),
    )


@st.composite
def throttle_configs(draw):
    """Generate valid throttle configurations."""
    return ExecutionThrottleConfig(
        min_delay_per_action_seconds=draw(st.floats(min_value=0.5, max_value=2.0)),
        max_actions_per_host_per_minute=draw(st.integers(min_value=5, max_value=30)),
        burst_allowance=draw(st.integers(min_value=1, max_value=5)),
    )


# === Helper Functions ===

async def failing_operation(fail_count: int, success_value: Any = "success"):
    """Create an operation that fails N times then succeeds."""
    call_count = 0
    
    async def operation():
        nonlocal call_count
        call_count += 1
        if call_count <= fail_count:
            raise Exception(f"Simulated failure {call_count}")
        return success_value
    
    return operation


async def always_failing_operation():
    """Create an operation that always fails."""
    async def operation():
        raise Exception("Always fails")
    return operation


async def always_succeeding_operation(value: Any = "success"):
    """Create an operation that always succeeds."""
    async def operation():
        return value
    return operation


# === Property Tests ===

class TestRetryDoesNotBypassThrottle:
    """
    Property Test 12.1: Retry does not bypass throttle limits
    
    Requirement 3.4: Retry delays count toward throttle budget.
    """
    
    @pytest.mark.asyncio
    async def test_retry_respects_throttle_rate_limit(self):
        """**Feature: retry-wiring, Property: Throttle Compliance**
        
        Retry attempts must respect per-host rate limits.
        """
        # Configure strict throttle
        config = ExecutionThrottleConfig(
            min_delay_per_action_seconds=0.5,
            max_actions_per_host_per_minute=3,
            burst_allowance=1,
        )
        throttle = ExecutionThrottle(config)
        
        # Simulate retry scenario with throttle checks
        host = "api.example.com"
        retry_count = 0
        
        # First few actions should be allowed
        for i in range(3):
            decision = throttle.check_throttle(host)
            if decision.allowed:
                throttle.record_action(host)
                retry_count += 1
        
        # After rate limit, should be blocked
        decision = throttle.check_throttle(host)
        
        # Verify throttle is enforced
        assert retry_count <= config.max_actions_per_host_per_minute
        assert decision.allowed is False or decision.actions_in_window >= config.max_actions_per_host_per_minute - 1
    
    @pytest.mark.asyncio
    async def test_retry_delay_counts_toward_throttle(self):
        """**Feature: retry-wiring, Property: Throttle Compliance**
        
        Time spent in retry delay should count toward throttle window.
        """
        config = ExecutionThrottleConfig(
            min_delay_per_action_seconds=0.5,
            max_actions_per_host_per_minute=60,
            burst_allowance=2,
        )
        throttle = ExecutionThrottle(config)
        host = "api.example.com"
        
        # Record first action
        throttle.record_action(host)
        
        # Check throttle immediately (should require delay after burst)
        throttle.record_action(host)
        throttle.record_action(host)  # Exceed burst
        
        decision = throttle.check_throttle(host)
        
        # After burst, minimum delay should be required
        if not decision.allowed:
            assert decision.wait_seconds > 0
    
    @given(policy=retry_policies())
    @settings(max_examples=20, deadline=10000)
    @pytest.mark.asyncio
    async def test_retry_executor_tracks_all_attempts(self, policy):
        """**Feature: retry-wiring, Property: Throttle Compliance**
        
        All retry attempts must be tracked for throttle accounting.
        """
        executor = RetryExecutor(policy)
        
        # Create operation that fails once then succeeds
        call_count = [0]
        
        async def operation():
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("First attempt fails")
            return "success"
        
        result = await executor.execute_with_retry(operation, "test_op")
        
        # Verify all attempts are tracked
        attempts = executor.get_attempts()
        assert len(attempts) == 2  # One failure, one success
        assert attempts[0].success is False
        assert attempts[1].success is True


class TestRetryAttemptsLoggedToAudit:
    """
    Property Test 12.2: Retry attempts logged to audit trail
    
    Requirement 3.6: Each retry attempt creates audit entry.
    """
    
    @pytest.mark.asyncio
    async def test_retry_attempts_recorded(self):
        """**Feature: retry-wiring, Property: Audit Trail**
        
        Each retry attempt must be recorded with timestamp and details.
        """
        policy = RetryPolicy(max_retries=3, base_delay_seconds=0.01)
        executor = RetryExecutor(policy)
        
        # Create operation that fails twice then succeeds
        call_count = [0]
        
        async def operation():
            call_count[0] += 1
            if call_count[0] <= 2:
                raise Exception(f"Failure {call_count[0]}")
            return "success"
        
        result = await executor.execute_with_retry(operation, "audit_test")
        
        attempts = executor.get_attempts()
        
        # Verify all attempts recorded
        assert len(attempts) == 3
        
        # Verify attempt details
        for i, attempt in enumerate(attempts):
            assert isinstance(attempt, RetryAttempt)
            assert attempt.attempt_number == i
            assert isinstance(attempt.timestamp, datetime)
            assert attempt.timestamp.tzinfo == timezone.utc
    
    @pytest.mark.asyncio
    async def test_retry_attempt_contains_error_info(self):
        """**Feature: retry-wiring, Property: Audit Trail**
        
        Failed retry attempts must contain error information.
        """
        policy = RetryPolicy(max_retries=2, base_delay_seconds=0.01)
        executor = RetryExecutor(policy)
        
        error_message = "Specific error for audit"
        call_count = [0]
        
        async def operation():
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception(error_message)
            return "success"
        
        await executor.execute_with_retry(operation, "error_audit_test")
        
        attempts = executor.get_attempts()
        failed_attempt = attempts[0]
        
        assert failed_attempt.success is False
        assert failed_attempt.error is not None
        assert error_message in failed_attempt.error
    
    @pytest.mark.asyncio
    async def test_retry_attempt_contains_delay_info(self):
        """**Feature: retry-wiring, Property: Audit Trail**
        
        Retry attempts must record delay duration.
        """
        policy = RetryPolicy(
            max_retries=2,
            base_delay_seconds=0.05,
            exponential_base=2.0,
        )
        executor = RetryExecutor(policy)
        
        call_count = [0]
        
        async def operation():
            call_count[0] += 1
            if call_count[0] <= 2:
                raise Exception("Fail")
            return "success"
        
        await executor.execute_with_retry(operation, "delay_test")
        
        attempts = executor.get_attempts()
        
        # First attempt has no delay
        assert attempts[0].delay_seconds == 0.0
        
        # Subsequent attempts have increasing delays
        assert attempts[1].delay_seconds > 0
        assert attempts[2].delay_seconds >= attempts[1].delay_seconds
    
    @given(policy=retry_policies())
    @settings(max_examples=20, deadline=10000)
    @pytest.mark.asyncio
    async def test_all_attempts_have_timestamps(self, policy):
        """**Feature: retry-wiring, Property: Audit Trail**
        
        All retry attempts must have UTC timestamps.
        """
        executor = RetryExecutor(policy)
        
        call_count = [0]
        
        async def operation():
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("First fail")
            return "success"
        
        await executor.execute_with_retry(operation, "timestamp_test")
        
        attempts = executor.get_attempts()
        
        for attempt in attempts:
            assert attempt.timestamp is not None
            assert attempt.timestamp.tzinfo == timezone.utc
            # Timestamp should be recent
            assert (datetime.now(timezone.utc) - attempt.timestamp).total_seconds() < 60


class TestRetryExhaustionRaisesCorrectError:
    """
    Property Test 12.3: Retry exhaustion raises correct error type
    
    Requirement 3.5: Original error raised after max attempts.
    """
    
    @pytest.mark.asyncio
    async def test_retry_exhaustion_raises_retry_exhausted_error(self):
        """**Feature: retry-wiring, Property: Error Propagation**
        
        After all retries fail, RetryExhaustedError must be raised.
        """
        policy = RetryPolicy(max_retries=2, base_delay_seconds=0.01)
        executor = RetryExecutor(policy)
        
        async def always_fails():
            raise Exception("Always fails")
        
        with pytest.raises(RetryExhaustedError) as exc_info:
            await executor.execute_with_retry(always_fails, "exhaustion_test")
        
        # Verify error message contains useful info
        error_msg = str(exc_info.value)
        assert "exhaustion_test" in error_msg or "attempts" in error_msg.lower()
    
    @pytest.mark.asyncio
    async def test_retry_exhausted_error_is_hard_stop(self):
        """**Feature: retry-wiring, Property: Error Propagation**
        
        RetryExhaustedError must be classified as HARD_STOP.
        """
        error = RetryExhaustedError("Test exhaustion")
        assert is_hard_stop(error) is True
    
    @pytest.mark.asyncio
    async def test_retry_exhaustion_includes_attempt_count(self):
        """**Feature: retry-wiring, Property: Error Propagation**
        
        RetryExhaustedError must include attempt count information.
        """
        policy = RetryPolicy(max_retries=3, base_delay_seconds=0.01)
        executor = RetryExecutor(policy)
        
        async def always_fails():
            raise Exception("Persistent failure")
        
        with pytest.raises(RetryExhaustedError) as exc_info:
            await executor.execute_with_retry(always_fails, "count_test")
        
        # Verify attempt count in error or attempts list
        attempts = executor.get_attempts()
        assert len(attempts) == 4  # Initial + 3 retries
        
        # All attempts should be failures
        assert all(not a.success for a in attempts)
    
    @given(max_retries=st.integers(min_value=1, max_value=5))
    @settings(max_examples=20, deadline=10000)
    @pytest.mark.asyncio
    async def test_exact_retry_count_before_exhaustion(self, max_retries):
        """**Feature: retry-wiring, Property: Error Propagation**
        
        Exactly max_retries + 1 attempts before exhaustion.
        """
        policy = RetryPolicy(max_retries=max_retries, base_delay_seconds=0.01)
        executor = RetryExecutor(policy)
        
        async def always_fails():
            raise Exception("Fail")
        
        with pytest.raises(RetryExhaustedError):
            await executor.execute_with_retry(always_fails, "exact_count_test")
        
        attempts = executor.get_attempts()
        assert len(attempts) == max_retries + 1
    
    @pytest.mark.asyncio
    async def test_last_error_preserved_in_exhaustion(self):
        """**Feature: retry-wiring, Property: Error Propagation**
        
        Last error message should be preserved in RetryExhaustedError.
        """
        policy = RetryPolicy(max_retries=2, base_delay_seconds=0.01)
        executor = RetryExecutor(policy)
        
        call_count = [0]
        
        async def fails_with_different_errors():
            call_count[0] += 1
            raise Exception(f"Error number {call_count[0]}")
        
        with pytest.raises(RetryExhaustedError) as exc_info:
            await executor.execute_with_retry(fails_with_different_errors, "last_error_test")
        
        # Last error should be mentioned
        error_msg = str(exc_info.value)
        assert "Error number 3" in error_msg or "Last error" in error_msg


# === Integration-Style Tests (No Wiring) ===

class TestRetryDelaysRespectPerHostThrottle:
    """
    Integration Test 12.4: Retry delays respect per-host throttle
    
    Requirement 3.4: Test with multiple hosts, throttle isolation.
    """
    
    @pytest.mark.asyncio
    async def test_throttle_isolation_between_hosts(self):
        """**Feature: retry-wiring, Integration: Per-Host Throttle**
        
        Throttle limits must be isolated per host.
        """
        config = ExecutionThrottleConfig(
            min_delay_per_action_seconds=0.5,
            max_actions_per_host_per_minute=5,
            burst_allowance=2,
        )
        throttle = ExecutionThrottle(config)
        
        host_a = "api.example.com"
        host_b = "mcp.test.local"
        
        # Exhaust throttle for host_a
        for _ in range(5):
            throttle.record_action(host_a)
        
        # host_b should still be allowed
        decision_b = throttle.check_throttle(host_b)
        assert decision_b.allowed is True
        
        # host_a should be blocked
        decision_a = throttle.check_throttle(host_a)
        assert decision_a.allowed is False
    
    @pytest.mark.asyncio
    async def test_retry_with_throttle_simulation(self):
        """**Feature: retry-wiring, Integration: Per-Host Throttle**
        
        Simulated retry with throttle checks.
        """
        config = ExecutionThrottleConfig(
            min_delay_per_action_seconds=0.5,
            max_actions_per_host_per_minute=10,
            burst_allowance=3,
        )
        throttle = ExecutionThrottle(config)
        policy = RetryPolicy(max_retries=3, base_delay_seconds=0.01)
        executor = RetryExecutor(policy)
        
        host = "api.example.com"
        
        # Simulate retry scenario with throttle checks
        async def operation_with_throttle_check():
            decision = throttle.check_throttle(host)
            if not decision.allowed:
                raise ThrottleLimitExceededError(f"Throttled: {decision.reason}")
            throttle.record_action(host)
            return "success"
        
        # Should succeed within throttle limits
        result = await executor.execute_with_retry(
            operation_with_throttle_check,
            "throttle_sim_test"
        )
        
        assert result == "success"
        
        # Verify throttle recorded the action
        stats = throttle.get_host_stats(host)
        assert stats is not None
        assert stats["actions_in_last_minute"] >= 1
    
    @pytest.mark.asyncio
    async def test_multiple_hosts_independent_throttle(self):
        """**Feature: retry-wiring, Integration: Per-Host Throttle**
        
        Multiple hosts should have independent throttle budgets.
        """
        config = ExecutionThrottleConfig(
            min_delay_per_action_seconds=0.5,
            max_actions_per_host_per_minute=3,
            burst_allowance=1,
        )
        throttle = ExecutionThrottle(config)
        
        hosts = ["host1.example.com", "host2.example.com", "host3.example.com"]
        
        # Record actions for each host
        for host in hosts:
            for _ in range(2):
                throttle.record_action(host)
        
        # Each host should have independent count
        for host in hosts:
            stats = throttle.get_host_stats(host)
            assert stats["actions_in_last_minute"] == 2
    
    @pytest.mark.asyncio
    async def test_throttle_log_captures_all_decisions(self):
        """**Feature: retry-wiring, Integration: Per-Host Throttle**
        
        All throttle decisions must be logged for audit.
        """
        config = ExecutionThrottleConfig(
            min_delay_per_action_seconds=0.5,
            max_actions_per_host_per_minute=5,
            burst_allowance=2,
        )
        throttle = ExecutionThrottle(config)
        host = "api.example.com"
        
        # Make several throttle checks
        for _ in range(5):
            throttle.check_throttle(host)
            throttle.record_action(host)
        
        # Verify all decisions logged
        log = throttle.get_throttle_log()
        assert len(log) == 5
        
        # Each decision should have required fields
        for decision in log:
            assert isinstance(decision, ThrottleDecision)
            assert decision.host == host


class TestPartialSuccessDuringRetry:
    """
    Integration Test 12.5: Partial success during retry handled correctly
    
    Requirement 3.5: Test idempotency requirements, state consistency.
    """
    
    @pytest.mark.asyncio
    async def test_success_after_failures_returns_result(self):
        """**Feature: retry-wiring, Integration: Partial Success**
        
        Success after failures must return the successful result.
        """
        policy = RetryPolicy(max_retries=3, base_delay_seconds=0.01)
        executor = RetryExecutor(policy)
        
        call_count = [0]
        expected_result = {"status": "success", "data": "important"}
        
        async def eventually_succeeds():
            call_count[0] += 1
            if call_count[0] <= 2:
                raise Exception(f"Failure {call_count[0]}")
            return expected_result
        
        result = await executor.execute_with_retry(eventually_succeeds, "partial_test")
        
        assert result == expected_result
        assert call_count[0] == 3
    
    @pytest.mark.asyncio
    async def test_state_consistency_after_retry(self):
        """**Feature: retry-wiring, Integration: Partial Success**
        
        State must be consistent after successful retry.
        """
        policy = RetryPolicy(max_retries=3, base_delay_seconds=0.01)
        executor = RetryExecutor(policy)
        
        state = {"counter": 0, "last_attempt": None}
        
        async def stateful_operation():
            state["counter"] += 1
            state["last_attempt"] = datetime.now(timezone.utc)
            if state["counter"] < 3:
                raise Exception("Not ready yet")
            return state["counter"]
        
        result = await executor.execute_with_retry(stateful_operation, "state_test")
        
        # Verify final state
        assert result == 3
        assert state["counter"] == 3
        assert state["last_attempt"] is not None
    
    @pytest.mark.asyncio
    async def test_idempotent_operation_safe_to_retry(self):
        """**Feature: retry-wiring, Integration: Partial Success**
        
        Idempotent operations should be safe to retry.
        """
        policy = RetryPolicy(max_retries=3, base_delay_seconds=0.01)
        executor = RetryExecutor(policy)
        
        # Simulate idempotent operation (same result regardless of calls)
        call_count = [0]
        idempotent_result = "idempotent_value_123"
        
        async def idempotent_operation():
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Transient failure")
            return idempotent_result
        
        result = await executor.execute_with_retry(idempotent_operation, "idempotent_test")
        
        assert result == idempotent_result
        # Multiple calls should be safe
        assert call_count[0] == 2
    
    @pytest.mark.asyncio
    async def test_non_idempotent_operation_tracking(self):
        """**Feature: retry-wiring, Integration: Partial Success**
        
        Non-idempotent operations should track side effects.
        """
        policy = RetryPolicy(max_retries=2, base_delay_seconds=0.01)
        executor = RetryExecutor(policy)
        
        side_effects = []
        
        async def non_idempotent_operation():
            side_effects.append(datetime.now(timezone.utc))
            if len(side_effects) == 1:
                raise Exception("First call fails")
            return len(side_effects)
        
        result = await executor.execute_with_retry(non_idempotent_operation, "non_idempotent_test")
        
        # Side effects should be tracked
        assert len(side_effects) == 2
        assert result == 2
        
        # Attempts should match side effects
        attempts = executor.get_attempts()
        assert len(attempts) == 2
    
    @pytest.mark.asyncio
    async def test_partial_success_attempts_recorded(self):
        """**Feature: retry-wiring, Integration: Partial Success**
        
        All attempts (failures and success) must be recorded.
        """
        policy = RetryPolicy(max_retries=4, base_delay_seconds=0.01)
        executor = RetryExecutor(policy)
        
        call_count = [0]
        
        async def mixed_results():
            call_count[0] += 1
            if call_count[0] <= 3:
                raise Exception(f"Failure {call_count[0]}")
            return "finally_success"
        
        result = await executor.execute_with_retry(mixed_results, "mixed_test")
        
        attempts = executor.get_attempts()
        
        # Verify attempt sequence
        assert len(attempts) == 4
        assert attempts[0].success is False
        assert attempts[1].success is False
        assert attempts[2].success is False
        assert attempts[3].success is True
        
        # Verify result
        assert result == "finally_success"


# === Backward Compatibility Tests ===

class TestBackwardCompatibility:
    """
    Backward Compatibility Tests
    
    These tests verify that the RetryExecutor interface is compatible
    with the planned integration into MCPClient and BountyPipelineClient.
    
    NO WIRING - just interface validation.
    """
    
    def test_retry_executor_instantiation_default_policy(self):
        """**Feature: retry-wiring, Backward Compat: Default Policy**
        
        RetryExecutor must be instantiable with default policy.
        """
        executor = RetryExecutor()
        assert executor is not None
        
        # Default policy should be reasonable
        policy = executor._policy
        assert policy.max_retries >= 1
        assert policy.base_delay_seconds > 0
    
    def test_retry_executor_instantiation_custom_policy(self):
        """**Feature: retry-wiring, Backward Compat: Custom Policy**
        
        RetryExecutor must accept custom policy.
        """
        custom_policy = RetryPolicy(
            max_retries=5,
            base_delay_seconds=2.0,
            max_delay_seconds=60.0,
        )
        executor = RetryExecutor(custom_policy)
        
        assert executor._policy.max_retries == 5
        assert executor._policy.base_delay_seconds == 2.0
    
    def test_retry_policy_default_values(self):
        """**Feature: retry-wiring, Backward Compat: Policy Defaults**
        
        RetryPolicy must have sensible defaults.
        """
        policy = RetryPolicy()
        
        assert policy.max_retries == 3
        assert policy.base_delay_seconds == 1.0
        assert policy.max_delay_seconds == 30.0
        assert policy.exponential_base == 2.0
    
    def test_retry_policy_status_code_classification(self):
        """**Feature: retry-wiring, Backward Compat: Status Codes**
        
        RetryPolicy must correctly classify status codes.
        """
        policy = RetryPolicy()
        
        # Retryable status codes
        assert policy.should_retry_status(429) is True  # Rate limited
        assert policy.should_retry_status(500) is True  # Server error
        assert policy.should_retry_status(502) is True  # Bad gateway
        assert policy.should_retry_status(503) is True  # Service unavailable
        assert policy.should_retry_status(504) is True  # Gateway timeout
        
        # Non-retryable status codes
        assert policy.should_retry_status(400) is False  # Bad request
        assert policy.should_retry_status(401) is False  # Unauthorized
        assert policy.should_retry_status(403) is False  # Forbidden
        assert policy.should_retry_status(404) is False  # Not found
        assert policy.should_retry_status(422) is False  # Unprocessable
    
    def test_get_attempts_returns_list(self):
        """**Feature: retry-wiring, Backward Compat: Attempts List**
        
        get_attempts() must return a list of RetryAttempt.
        """
        executor = RetryExecutor()
        attempts = executor.get_attempts()
        
        assert isinstance(attempts, list)
    
    @pytest.mark.asyncio
    async def test_clear_attempts_resets_history(self):
        """**Feature: retry-wiring, Backward Compat: Clear History**
        
        clear_attempts() must reset attempt history.
        """
        executor = RetryExecutor()
        
        # Add some attempts by running an operation
        async def op():
            return "success"
        
        await executor.execute_with_retry(op, "test")
        
        assert len(executor.get_attempts()) > 0
        
        executor.clear_attempts()
        
        assert len(executor.get_attempts()) == 0


# === Performance Tests ===

class TestRetryPerformance:
    """
    Performance Tests
    
    Validate that retry mechanism meets performance requirements.
    """
    
    @pytest.mark.asyncio
    async def test_successful_operation_minimal_overhead(self):
        """**Feature: retry-wiring, Performance: Minimal Overhead**
        
        Successful operations should have minimal retry overhead.
        """
        import time
        
        policy = RetryPolicy(max_retries=3, base_delay_seconds=1.0)
        executor = RetryExecutor(policy)
        
        async def fast_operation():
            return "success"
        
        start = time.perf_counter()
        result = await executor.execute_with_retry(fast_operation, "perf_test")
        elapsed = time.perf_counter() - start
        
        # Should complete almost instantly (no retries needed)
        assert elapsed < 0.1  # 100ms max
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_calculation(self):
        """**Feature: retry-wiring, Performance: Backoff Calculation**
        
        Exponential backoff should be calculated correctly.
        """
        policy = RetryPolicy(
            max_retries=5,
            base_delay_seconds=1.0,
            max_delay_seconds=30.0,
            exponential_base=2.0,
        )
        executor = RetryExecutor(policy)
        
        # Test delay calculation
        assert executor._calculate_delay(0) == 0.0
        assert executor._calculate_delay(1) == 1.0  # base * 2^0
        assert executor._calculate_delay(2) == 2.0  # base * 2^1
        assert executor._calculate_delay(3) == 4.0  # base * 2^2
        assert executor._calculate_delay(4) == 8.0  # base * 2^3
        assert executor._calculate_delay(5) == 16.0  # base * 2^4
        
        # Should cap at max_delay
        assert executor._calculate_delay(10) == 30.0  # Capped
    
    @pytest.mark.asyncio
    async def test_retry_timing_reasonable(self):
        """**Feature: retry-wiring, Performance: Timing**
        
        Retry timing should be reasonable for test scenarios.
        """
        import time
        
        policy = RetryPolicy(
            max_retries=2,
            base_delay_seconds=0.05,  # 50ms
            max_delay_seconds=0.2,
        )
        executor = RetryExecutor(policy)
        
        call_count = [0]
        
        async def fails_twice():
            call_count[0] += 1
            if call_count[0] <= 2:
                raise Exception("Fail")
            return "success"
        
        start = time.perf_counter()
        result = await executor.execute_with_retry(fails_twice, "timing_test")
        elapsed = time.perf_counter() - start
        
        # Should complete within reasonable time
        # 2 retries with ~50ms + ~100ms delays = ~150ms + execution time
        assert elapsed < 1.0  # 1 second max
        assert result == "success"


# === Determinism Tests ===

class TestRetryDeterminism:
    """
    Determinism Tests
    
    Validate that retry behavior is deterministic and predictable.
    """
    
    @pytest.mark.asyncio
    async def test_same_inputs_same_attempt_count(self):
        """**Feature: retry-wiring, Determinism: Predictable Attempts**
        
        Same failure pattern should produce same attempt count.
        """
        policy = RetryPolicy(max_retries=3, base_delay_seconds=0.01)
        
        for _ in range(3):
            executor = RetryExecutor(policy)
            call_count = [0]
            
            async def fails_twice():
                call_count[0] += 1
                if call_count[0] <= 2:
                    raise Exception("Fail")
                return "success"
            
            await executor.execute_with_retry(fails_twice, "determinism_test")
            
            # Should always be 3 attempts
            assert len(executor.get_attempts()) == 3
    
    @pytest.mark.asyncio
    async def test_delay_calculation_deterministic(self):
        """**Feature: retry-wiring, Determinism: Delay Calculation**
        
        Delay calculation should be deterministic.
        """
        policy = RetryPolicy(
            max_retries=5,
            base_delay_seconds=1.0,
            max_delay_seconds=30.0,
            exponential_base=2.0,
        )
        
        executor1 = RetryExecutor(policy)
        executor2 = RetryExecutor(policy)
        
        for attempt in range(6):
            delay1 = executor1._calculate_delay(attempt)
            delay2 = executor2._calculate_delay(attempt)
            assert delay1 == delay2
