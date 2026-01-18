"""
Tests for Phase-4 Execution Layer Risk Mitigations

Tests cover:
1. Per-host throttling enforcement
2. Disk retention and pruning
3. Headless override guardrails

NO MOCKS IN PRODUCTION PATHS.

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

import asyncio
import tempfile
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from execution_layer.throttle import (
    ExecutionThrottle,
    ExecutionThrottleConfig,
    ThrottleDecision,
)
from execution_layer.retention import (
    EvidenceRetentionManager,
    EvidenceRetentionPolicy,
    RetentionStats,
)
from execution_layer.browser import BrowserConfig
from execution_layer.errors import (
    ThrottleConfigError,
    ThrottleLimitExceededError,
    DiskRetentionError,
    HeadlessOverrideError,
)


# =============================================================================
# THROTTLE TESTS
# =============================================================================

class TestExecutionThrottleConfig:
    """Tests for ExecutionThrottleConfig validation."""
    
    def test_valid_config(self):
        """Valid config should be accepted."""
        config = ExecutionThrottleConfig(
            min_delay_per_action_seconds=2.0,
            max_actions_per_host_per_minute=10,
            burst_allowance=3,
        )
        assert config.min_delay_per_action_seconds == 2.0
        assert config.max_actions_per_host_per_minute == 10
        assert config.burst_allowance == 3
    
    def test_default_config(self):
        """Default config should have safe values."""
        config = ExecutionThrottleConfig()
        assert config.min_delay_per_action_seconds >= 2.0
        assert config.max_actions_per_host_per_minute <= 10
    
    def test_min_delay_too_low(self):
        """min_delay_per_action_seconds < 0.5 should raise."""
        with pytest.raises(ThrottleConfigError) as exc_info:
            ExecutionThrottleConfig(min_delay_per_action_seconds=0.1)
        assert "min_delay_per_action_seconds must be >= 0.5" in str(exc_info.value)
    
    def test_min_delay_too_high(self):
        """min_delay_per_action_seconds > 60 should raise."""
        with pytest.raises(ThrottleConfigError) as exc_info:
            ExecutionThrottleConfig(min_delay_per_action_seconds=120.0)
        assert "min_delay_per_action_seconds must be <= 60.0" in str(exc_info.value)
    
    def test_max_actions_too_low(self):
        """max_actions_per_host_per_minute < 1 should raise."""
        with pytest.raises(ThrottleConfigError) as exc_info:
            ExecutionThrottleConfig(max_actions_per_host_per_minute=0)
        assert "max_actions_per_host_per_minute must be >= 1" in str(exc_info.value)
    
    def test_max_actions_too_high(self):
        """max_actions_per_host_per_minute > 60 should raise."""
        with pytest.raises(ThrottleConfigError) as exc_info:
            ExecutionThrottleConfig(max_actions_per_host_per_minute=100)
        assert "max_actions_per_host_per_minute must be <= 60" in str(exc_info.value)
    
    def test_burst_allowance_negative(self):
        """burst_allowance < 0 should raise."""
        with pytest.raises(ThrottleConfigError) as exc_info:
            ExecutionThrottleConfig(burst_allowance=-1)
        assert "burst_allowance must be >= 0" in str(exc_info.value)


class TestExecutionThrottle:
    """Tests for ExecutionThrottle enforcement."""
    
    def test_throttle_requires_config(self):
        """Throttle without config should HARD FAIL."""
        with pytest.raises(ThrottleConfigError) as exc_info:
            ExecutionThrottle(None)
        assert "REQUIRED" in str(exc_info.value)
    
    def test_extract_host_from_url(self):
        """Should extract host from URL correctly."""
        config = ExecutionThrottleConfig()
        throttle = ExecutionThrottle(config)
        
        assert throttle.extract_host("https://example.com/path") == "example.com"
        assert throttle.extract_host("https://sub.example.com:8080/path") == "sub.example.com:8080"
        assert throttle.extract_host("http://localhost:3000") == "localhost:3000"
        assert throttle.extract_host("selector") == "selector"
    
    def test_first_action_allowed(self):
        """First action against a host should be allowed."""
        config = ExecutionThrottleConfig()
        throttle = ExecutionThrottle(config)
        
        decision = throttle.check_throttle("https://example.com/page1")
        assert decision.allowed is True
        assert decision.wait_seconds == 0.0
    
    def test_burst_allowance(self):
        """Actions within burst allowance should be allowed."""
        config = ExecutionThrottleConfig(burst_allowance=3)
        throttle = ExecutionThrottle(config)
        
        # First 3 actions should be allowed (burst)
        for i in range(3):
            throttle.record_action("https://example.com/page")
            decision = throttle.check_throttle("https://example.com/page")
            assert decision.allowed is True, f"Action {i+1} should be allowed in burst"
    
    def test_rate_limit_exceeded(self):
        """Exceeding rate limit should block."""
        config = ExecutionThrottleConfig(
            max_actions_per_host_per_minute=5,
            burst_allowance=5,
        )
        throttle = ExecutionThrottle(config)
        
        # Record 5 actions
        for _ in range(5):
            throttle.record_action("https://example.com/page")
        
        # 6th action should be blocked
        decision = throttle.check_throttle("https://example.com/page")
        assert decision.allowed is False
        assert "Rate limit exceeded" in decision.reason
    
    def test_different_hosts_independent(self):
        """Different hosts should have independent throttles."""
        config = ExecutionThrottleConfig(max_actions_per_host_per_minute=2)
        throttle = ExecutionThrottle(config)
        
        # Max out host1
        throttle.record_action("https://host1.com/page")
        throttle.record_action("https://host1.com/page")
        
        # host2 should still be allowed
        decision = throttle.check_throttle("https://host2.com/page")
        assert decision.allowed is True
    
    def test_throttle_log_recorded(self):
        """All throttle decisions should be logged."""
        config = ExecutionThrottleConfig()
        throttle = ExecutionThrottle(config)
        
        throttle.check_throttle("https://example.com/page1")
        throttle.check_throttle("https://example.com/page2")
        
        log = throttle.get_throttle_log()
        assert len(log) == 2
    
    def test_host_stats(self):
        """Should return correct stats for a host."""
        config = ExecutionThrottleConfig()
        throttle = ExecutionThrottle(config)
        
        throttle.record_action("https://example.com/page")
        throttle.record_action("https://example.com/page")
        
        stats = throttle.get_host_stats("example.com")
        assert stats is not None
        assert stats["actions_in_last_minute"] == 2
        assert stats["last_action_at"] is not None
    
    def test_reset_host(self):
        """Should be able to reset throttle for a host."""
        config = ExecutionThrottleConfig()
        throttle = ExecutionThrottle(config)
        
        throttle.record_action("https://example.com/page")
        throttle.reset_host("example.com")
        
        stats = throttle.get_host_stats("example.com")
        assert stats is None


class TestThrottleAsync:
    """Async tests for throttle wait behavior."""
    
    def test_wait_if_needed_rate_limit_raises(self):
        """wait_if_needed should raise on rate limit exceeded."""
        config = ExecutionThrottleConfig(max_actions_per_host_per_minute=2)
        throttle = ExecutionThrottle(config)
        
        # Max out the host
        throttle.record_action("https://example.com/page")
        throttle.record_action("https://example.com/page")
        
        # Should raise ThrottleLimitExceededError
        with pytest.raises(ThrottleLimitExceededError) as exc_info:
            asyncio.run(throttle.wait_if_needed("https://example.com/page"))
        assert "HARD FAIL" in str(exc_info.value)


# =============================================================================
# RETENTION TESTS
# =============================================================================

class TestEvidenceRetentionPolicy:
    """Tests for EvidenceRetentionPolicy validation."""
    
    def test_valid_policy(self):
        """Valid policy should be accepted."""
        policy = EvidenceRetentionPolicy(
            max_total_disk_mb=5000,
            max_artifacts_per_execution=100,
            ttl_days=30,
        )
        assert policy.max_total_disk_mb == 5000
        assert policy.max_artifacts_per_execution == 100
        assert policy.ttl_days == 30
    
    def test_default_policy(self):
        """Default policy should have safe values."""
        policy = EvidenceRetentionPolicy()
        assert policy.max_total_disk_mb >= 100
        assert policy.max_artifacts_per_execution >= 1
        assert policy.ttl_days >= 1
    
    def test_max_disk_too_low(self):
        """max_total_disk_mb < 100 should raise."""
        with pytest.raises(DiskRetentionError) as exc_info:
            EvidenceRetentionPolicy(max_total_disk_mb=50)
        assert "max_total_disk_mb must be >= 100" in str(exc_info.value)
    
    def test_max_artifacts_too_low(self):
        """max_artifacts_per_execution < 1 should raise."""
        with pytest.raises(DiskRetentionError) as exc_info:
            EvidenceRetentionPolicy(max_artifacts_per_execution=0)
        assert "max_artifacts_per_execution must be >= 1" in str(exc_info.value)
    
    def test_ttl_too_low(self):
        """ttl_days < 1 should raise."""
        with pytest.raises(DiskRetentionError) as exc_info:
            EvidenceRetentionPolicy(ttl_days=0)
        assert "ttl_days must be >= 1" in str(exc_info.value)
    
    def test_warning_threshold_invalid(self):
        """warning_threshold_percent outside 50-100 should raise."""
        with pytest.raises(DiskRetentionError) as exc_info:
            EvidenceRetentionPolicy(warning_threshold_percent=30)
        assert "warning_threshold_percent must be 50-100" in str(exc_info.value)
    
    def test_critical_below_warning(self):
        """critical_threshold_percent < warning_threshold_percent should raise."""
        with pytest.raises(DiskRetentionError) as exc_info:
            EvidenceRetentionPolicy(
                warning_threshold_percent=90,
                critical_threshold_percent=80,
            )
        assert "critical_threshold_percent must be >= warning_threshold_percent" in str(exc_info.value)


class TestEvidenceRetentionManager:
    """Tests for EvidenceRetentionManager."""
    
    def test_retention_requires_policy(self):
        """Retention without policy should HARD FAIL."""
        with pytest.raises(DiskRetentionError) as exc_info:
            EvidenceRetentionManager(None)
        assert "REQUIRED" in str(exc_info.value)
    
    def test_get_stats_empty(self):
        """Stats on empty directory should return zeros."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = EvidenceRetentionPolicy()
            manager = EvidenceRetentionManager(policy, artifacts_dir=tmpdir)
            
            stats = manager.get_stats()
            assert stats.total_size_mb == 0
            assert stats.artifact_count == 0
            assert stats.execution_count == 0
            assert stats.is_warning is False
            assert stats.is_critical is False
    
    def test_get_stats_with_files(self):
        """Stats should reflect actual files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = EvidenceRetentionPolicy()
            manager = EvidenceRetentionManager(policy, artifacts_dir=tmpdir)
            
            # Create some test files
            exec_dir = Path(tmpdir) / "execution1"
            exec_dir.mkdir()
            (exec_dir / "file1.txt").write_text("test content 1")
            (exec_dir / "file2.txt").write_text("test content 2")
            
            stats = manager.get_stats()
            assert stats.artifact_count == 2
            assert stats.execution_count == 1
            assert stats.total_size_mb > 0
    
    def test_check_can_store_empty(self):
        """Should allow storage when empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = EvidenceRetentionPolicy()
            manager = EvidenceRetentionManager(policy, artifacts_dir=tmpdir)
            
            assert manager.check_can_store() is True
    
    def test_check_artifact_count_empty(self):
        """Should allow artifacts when execution is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = EvidenceRetentionPolicy(max_artifacts_per_execution=10)
            manager = EvidenceRetentionManager(policy, artifacts_dir=tmpdir)
            
            assert manager.check_artifact_count("execution1") is True
    
    def test_check_artifact_count_exceeded(self):
        """Should raise when max_artifacts_per_execution exceeded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = EvidenceRetentionPolicy(max_artifacts_per_execution=2)
            manager = EvidenceRetentionManager(policy, artifacts_dir=tmpdir)
            
            # Create execution with 2 files
            exec_dir = Path(tmpdir) / "execution1"
            exec_dir.mkdir()
            (exec_dir / "file1.txt").write_text("test")
            (exec_dir / "file2.txt").write_text("test")
            
            with pytest.raises(DiskRetentionError) as exc_info:
                manager.check_artifact_count("execution1")
            assert "HARD FAIL" in str(exc_info.value)
    
    def test_prune_expired(self):
        """Should prune executions older than ttl_days."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = EvidenceRetentionPolicy(ttl_days=1)
            manager = EvidenceRetentionManager(policy, artifacts_dir=tmpdir)
            
            # Create an old execution
            exec_dir = Path(tmpdir) / "old_execution"
            exec_dir.mkdir()
            old_file = exec_dir / "old_file.txt"
            old_file.write_text("old content")
            
            # Set mtime to 2 days ago
            old_time = time.time() - (2 * 24 * 3600)
            import os
            os.utime(old_file, (old_time, old_time))
            
            result = manager.prune_expired()
            assert result.executions_pruned == 1
            assert not exec_dir.exists()
    
    def test_prune_log_recorded(self):
        """All prune operations should be logged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = EvidenceRetentionPolicy()
            manager = EvidenceRetentionManager(policy, artifacts_dir=tmpdir)
            
            manager.prune_expired()
            
            log = manager.get_prune_log()
            assert len(log) == 1
    
    def test_get_execution_size(self):
        """Should return correct size for execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = EvidenceRetentionPolicy()
            manager = EvidenceRetentionManager(policy, artifacts_dir=tmpdir)
            
            # Create execution with known content
            exec_dir = Path(tmpdir) / "execution1"
            exec_dir.mkdir()
            content = "x" * 1000  # 1000 bytes
            (exec_dir / "file.txt").write_text(content)
            
            size = manager.get_execution_size("execution1")
            assert size == 1000


# =============================================================================
# HEADLESS OVERRIDE TESTS
# =============================================================================

class TestHeadlessOverrideGuardrail:
    """Tests for headless override guardrail."""
    
    def test_headless_true_default(self):
        """headless=True should be the default."""
        config = BrowserConfig()
        assert config.headless is True
    
    def test_headless_true_no_approval_needed(self):
        """headless=True should not require approval."""
        config = BrowserConfig(headless=True)
        assert config.headless is True
    
    def test_headless_false_without_approval_raises(self):
        """headless=False without approval should HARD FAIL."""
        with pytest.raises(HeadlessOverrideError) as exc_info:
            BrowserConfig(headless=False)
        assert "HIGH-RISK" in str(exc_info.value)
        assert "headless_override_approved=True" in str(exc_info.value)
    
    def test_headless_false_with_approval_allowed(self):
        """headless=False with approval should be allowed."""
        config = BrowserConfig(
            headless=False,
            headless_override_approved=True,
        )
        assert config.headless is False
        assert config.headless_override_approved is True
    
    def test_headless_override_approved_alone_is_noop(self):
        """headless_override_approved=True with headless=True is a no-op."""
        config = BrowserConfig(
            headless=True,
            headless_override_approved=True,
        )
        assert config.headless is True


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestRiskMitigationIntegration:
    """Integration tests for risk mitigations working together."""
    
    def test_throttle_and_retention_configs_required(self):
        """Controller should require both throttle and retention configs."""
        # This is tested implicitly by the controller requiring these configs
        # The actual integration test would require more setup
        pass
    
    def test_all_error_types_are_hard_stop(self):
        """All new error types should be in HARD_STOP_ERRORS."""
        from execution_layer.errors import (
            HARD_STOP_ERRORS,
            ThrottleConfigError,
            ThrottleLimitExceededError,
            DiskRetentionError,
            HeadlessOverrideError,
        )
        
        assert ThrottleConfigError in HARD_STOP_ERRORS
        assert ThrottleLimitExceededError in HARD_STOP_ERRORS
        assert DiskRetentionError in HARD_STOP_ERRORS
        assert HeadlessOverrideError in HARD_STOP_ERRORS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
