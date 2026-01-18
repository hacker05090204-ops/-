"""
Phase-4 Execution Layer Hardening Tests

Tests for hardening components:
- Manifest generation with SHA-256 hashes
- HTTPS enforcement
- Response schema validation
- Retry policy with exponential backoff
- Anti-detection awareness (OBSERVE ONLY)
- Request/response logging

OBSERVE ONLY — NO STEALTH, NO EVASION, NO BYPASS.

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
import tempfile
import pytest

from execution_layer.errors import (
    ConfigurationError,
    ResponseValidationError,
    RetryExhaustedError,
    HashChainVerificationError,
    AutomationDetectedError,
)
from execution_layer.manifest import ExecutionManifest, ManifestGenerator
from execution_layer.schemas import (
    MCPVerificationResponse,
    PipelineDraftResponse,
    ResponseValidator,
)
from execution_layer.retry import RetryPolicy, RetryExecutor
from execution_layer.request_logger import RequestLogger
from execution_layer.anti_detection import AntiDetectionObserver, AutomationDetectionSignal
from execution_layer.mcp_client import MCPClientConfig
from execution_layer.pipeline_client import BountyPipelineConfig
from execution_layer.types import (
    SafeAction,
    SafeActionType,
    EvidenceBundle,
    EvidenceArtifact,
    EvidenceType,
)


# ============================================================================
# HTTPS Enforcement Tests
# ============================================================================


class TestHTTPSEnforcement:
    """Test HTTPS enforcement for client configurations."""
    
    def test_mcp_client_rejects_http_url(self):
        """MCP client must reject non-HTTPS URLs."""
        with pytest.raises(ConfigurationError) as exc_info:
            MCPClientConfig(base_url="http://mcp.example.com")
        assert "requires HTTPS URL" in str(exc_info.value)

    def test_mcp_client_accepts_https_url(self):
        """MCP client must accept HTTPS URLs."""
        config = MCPClientConfig(base_url="https://mcp.example.com")
        assert config.base_url == "https://mcp.example.com"
    
    def test_pipeline_client_rejects_http_url(self):
        """Pipeline client must reject non-HTTPS URLs."""
        with pytest.raises(ConfigurationError) as exc_info:
            BountyPipelineConfig(base_url="http://pipeline.example.com")
        assert "requires HTTPS URL" in str(exc_info.value)
    
    def test_pipeline_client_accepts_https_url(self):
        """Pipeline client must accept HTTPS URLs."""
        config = BountyPipelineConfig(base_url="https://pipeline.example.com")
        assert config.base_url == "https://pipeline.example.com"
    
    def test_mcp_client_verify_ssl_default_true(self):
        """MCP client verify_ssl must default to True."""
        config = MCPClientConfig(base_url="https://mcp.example.com")
        assert config.verify_ssl is True
    
    def test_pipeline_client_verify_ssl_default_true(self):
        """Pipeline client verify_ssl must default to True."""
        config = BountyPipelineConfig(base_url="https://pipeline.example.com")
        assert config.verify_ssl is True


# ============================================================================
# Response Schema Validation Tests
# ============================================================================


class TestResponseSchemaValidation:
    """Test response schema validation."""
    
    def test_valid_mcp_response(self):
        """Valid MCP response must pass validation."""
        validator = ResponseValidator()
        data = {
            "verification_id": "ver_123",
            "finding_id": "find_456",
            "classification": "BUG",
            "invariant_violated": "INV_001",
            "proof_hash": "abc123",
            "verified_at": "2025-12-31T12:00:00+00:00",
        }
        result = validator.validate_mcp_response(data)
        assert result.verification_id == "ver_123"
        assert result.classification == "BUG"
    
    def test_mcp_response_missing_verification_id(self):
        """MCP response missing verification_id must fail."""
        validator = ResponseValidator()
        data = {
            "classification": "BUG",
            "verified_at": "2025-12-31T12:00:00+00:00",
        }
        with pytest.raises(ResponseValidationError):
            validator.validate_mcp_response(data)

    def test_mcp_response_invalid_classification(self):
        """MCP response with invalid classification must fail."""
        validator = ResponseValidator()
        data = {
            "verification_id": "ver_123",
            "classification": "INVALID",
            "verified_at": "2025-12-31T12:00:00+00:00",
        }
        with pytest.raises(ResponseValidationError):
            validator.validate_mcp_response(data)
    
    def test_valid_pipeline_response(self):
        """Valid Pipeline response must pass validation."""
        validator = ResponseValidator()
        data = {
            "draft_id": "draft_123",
            "status": "draft",
            "created_at": "2025-12-31T12:00:00+00:00",
        }
        result = validator.validate_pipeline_response(data)
        assert result.draft_id == "draft_123"
        assert result.status == "draft"
    
    def test_pipeline_response_missing_draft_id(self):
        """Pipeline response missing draft_id must fail."""
        validator = ResponseValidator()
        data = {
            "status": "draft",
            "created_at": "2025-12-31T12:00:00+00:00",
        }
        with pytest.raises(ResponseValidationError):
            validator.validate_pipeline_response(data)


# ============================================================================
# Retry Policy Tests
# ============================================================================


class TestRetryPolicy:
    """Test retry policy with exponential backoff."""
    
    def test_retry_policy_defaults(self):
        """Retry policy must have correct defaults."""
        policy = RetryPolicy()
        assert policy.max_retries == 3
        assert policy.base_delay_seconds == 1.0
        assert policy.exponential_base == 2.0
    
    def test_should_retry_5xx_errors(self):
        """Retry policy must retry 5xx errors."""
        policy = RetryPolicy()
        assert policy.should_retry_status(500) is True
        assert policy.should_retry_status(502) is True
        assert policy.should_retry_status(503) is True
        assert policy.should_retry_status(504) is True
    
    def test_should_not_retry_4xx_errors(self):
        """Retry policy must not retry 4xx errors (except 429)."""
        policy = RetryPolicy()
        assert policy.should_retry_status(400) is False
        assert policy.should_retry_status(401) is False
        assert policy.should_retry_status(403) is False
        assert policy.should_retry_status(404) is False
    
    def test_should_retry_429_rate_limit(self):
        """Retry policy must retry 429 rate limit."""
        policy = RetryPolicy()
        assert policy.should_retry_status(429) is True

    def test_retry_executor_success_first_attempt(self):
        """Retry executor must succeed on first attempt."""
        async def operation():
            return "success"
        
        executor = RetryExecutor()
        result = asyncio.run(executor.execute_with_retry(operation, "test_op"))
        assert result == "success"
        assert len(executor.get_attempts()) == 1
        assert executor.get_attempts()[0].success is True
    
    def test_retry_executor_exhausted(self):
        """Retry executor must raise RetryExhaustedError after all retries."""
        call_count = 0
        
        async def failing_operation():
            nonlocal call_count
            call_count += 1
            raise Exception("Always fails")
        
        policy = RetryPolicy(max_retries=2, base_delay_seconds=0.01)
        executor = RetryExecutor(policy)
        
        with pytest.raises(RetryExhaustedError) as exc_info:
            asyncio.run(executor.execute_with_retry(failing_operation, "test_op"))
        
        assert "HARD FAIL" in str(exc_info.value)
        assert call_count == 3  # Initial + 2 retries
    
    def test_exponential_backoff_calculation(self):
        """Retry executor must calculate exponential backoff correctly."""
        executor = RetryExecutor(RetryPolicy(base_delay_seconds=1.0, exponential_base=2.0))
        assert executor._calculate_delay(0) == 0.0
        assert executor._calculate_delay(1) == 1.0
        assert executor._calculate_delay(2) == 2.0
        assert executor._calculate_delay(3) == 4.0


# ============================================================================
# Manifest Generation Tests
# ============================================================================


class TestManifestGeneration:
    """Test execution manifest generation."""
    
    def _create_test_action(self, action_id: str = "action_1") -> SafeAction:
        return SafeAction(
            action_id=action_id,
            action_type=SafeActionType.NAVIGATE,
            target="https://example.com",
            parameters={},
            description="Test action",
        )
    
    def _create_test_evidence_bundle(self, execution_id: str = None) -> EvidenceBundle:
        import uuid
        if execution_id is None:
            execution_id = str(uuid.uuid4())
        bundle_id = str(uuid.uuid4())
        
        har_artifact = EvidenceArtifact.create(
            artifact_type=EvidenceType.HAR,
            content=b'{"log": {"version": "1.2", "creator": {"name": "test"}, "entries": []}}',
            file_path="test_artifacts/test.har",  # Relative path
        )
        bundle = EvidenceBundle(
            bundle_id=bundle_id,
            execution_id=execution_id,
            har_file=har_artifact,
        )
        bundle.finalize()
        return bundle

    def test_manifest_generation(self):
        """Manifest generator must create valid manifest."""
        generator = ManifestGenerator()
        action = self._create_test_action()
        bundle = self._create_test_evidence_bundle()
        
        manifest = generator.generate(
            execution_id=bundle.execution_id,
            evidence_bundle=bundle,
            actions=[action],
        )
        
        assert manifest.manifest_id
        assert manifest.execution_id == bundle.execution_id
        assert manifest.manifest_hash
        assert len(manifest.action_hashes) == 1
        assert manifest.evidence_bundle_hash == bundle.bundle_hash
    
    def test_manifest_hash_chain(self):
        """Manifest generator must create hash chain."""
        generator = ManifestGenerator()
        action = self._create_test_action()
        bundle1 = self._create_test_evidence_bundle()
        bundle2 = self._create_test_evidence_bundle()
        
        manifest1 = generator.generate(bundle1.execution_id, bundle1, [action])
        manifest2 = generator.generate(bundle2.execution_id, bundle2, [action])
        
        assert manifest1.previous_manifest_hash is None
        assert manifest2.previous_manifest_hash == manifest1.manifest_hash
    
    def test_manifest_verification_success(self):
        """Manifest verification must succeed for valid manifest."""
        generator = ManifestGenerator()
        action = self._create_test_action()
        bundle = self._create_test_evidence_bundle()
        
        manifest = generator.generate(bundle.execution_id, bundle, [action])
        assert generator.verify_chain(manifest, bundle) is True
    
    def test_manifest_verification_failure_hash_mismatch(self):
        """Manifest verification must fail on hash mismatch."""
        generator = ManifestGenerator()
        action = self._create_test_action()
        bundle = self._create_test_evidence_bundle()
        
        manifest = generator.generate(bundle.execution_id, bundle, [action])
        
        # Create a different bundle
        bundle2 = self._create_test_evidence_bundle()
        
        with pytest.raises(HashChainVerificationError):
            generator.verify_chain(manifest, bundle2)
    
    def test_manifest_save_to_file(self):
        """Manifest must be saved to JSON file."""
        generator = ManifestGenerator()
        action = self._create_test_action()
        bundle = self._create_test_evidence_bundle()
        
        manifest = generator.generate(bundle.execution_id, bundle, [action])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = generator.save_manifest(manifest, Path(tmpdir))
            assert output_path.exists()
            assert output_path.name == "execution_manifest.json"


# ============================================================================
# Request/Response Logging Tests
# ============================================================================


class TestRequestLogging:
    """Test request/response logging."""
    
    def test_log_request(self):
        """Request logger must log requests."""
        logger = RequestLogger()
        request_id = logger.log_request(
            endpoint="/api/v1/verify",
            method="POST",
            execution_id="exec_1",
        )
        
        assert request_id
        logs = logger.get_all_logs()
        assert len(logs) == 1
        assert logs[0].endpoint == "/api/v1/verify"
        assert logs[0].method == "POST"
    
    def test_log_response(self):
        """Request logger must log responses."""
        logger = RequestLogger()
        request_id = logger.log_request("/api/v1/verify", "POST")
        logger.log_response(
            request_id=request_id,
            status_code=200,
            response_time_ms=150.5,
            response_id="resp_123",
        )
        
        logs = logger.get_all_logs()
        assert len(logs) == 2
        response_log = logs[1]
        assert response_log.status_code == 200
        assert response_log.response_time_ms == 150.5
    
    def test_get_logs_for_execution(self):
        """Request logger must filter logs by execution_id."""
        logger = RequestLogger()
        
        # Log for exec_1
        req1 = logger.log_request("/api/v1/verify", "POST", "exec_1")
        logger.log_response(req1, 200, 100.0)
        
        # Log for exec_2
        req2 = logger.log_request("/api/v1/verify", "POST", "exec_2")
        logger.log_response(req2, 200, 150.0)
        
        exec1_logs = logger.get_logs_for_execution("exec_1")
        assert len(exec1_logs) == 2
        
        exec2_logs = logger.get_logs_for_execution("exec_2")
        assert len(exec2_logs) == 2


# ============================================================================
# Anti-Detection Awareness Tests
# ============================================================================


class TestAntiDetectionAwareness:
    """Test anti-detection awareness (OBSERVE ONLY)."""
    
    def test_detect_rate_limit(self):
        """Anti-detection must detect rate limiting."""
        observer = AntiDetectionObserver()
        signal = observer.detect_rate_limit(
            status_code=429,
            headers={"Retry-After": "60"},
            url="https://example.com",
        )
        
        assert signal is not None
        assert signal.signal_type == "rate_limit"
        assert "429" in signal.details

    def test_no_rate_limit_for_200(self):
        """Anti-detection must not detect rate limit for 200."""
        observer = AntiDetectionObserver()
        signal = observer.detect_rate_limit(
            status_code=200,
            url="https://example.com",
        )
        assert signal is None
    
    def test_should_stop_on_captcha(self):
        """Anti-detection must stop on CAPTCHA detection."""
        observer = AntiDetectionObserver()
        signal = AutomationDetectionSignal(
            signal_type="captcha",
            details="CAPTCHA detected",
            detected_at=datetime.now(timezone.utc),
            url="https://example.com",
        )
        assert observer.should_stop([signal]) is True
    
    def test_should_stop_on_rate_limit(self):
        """Anti-detection must stop on rate limit detection."""
        observer = AntiDetectionObserver()
        signal = AutomationDetectionSignal(
            signal_type="rate_limit",
            details="Rate limit detected",
            detected_at=datetime.now(timezone.utc),
            url="https://example.com",
        )
        assert observer.should_stop([signal]) is True
    
    def test_should_not_stop_on_webdriver(self):
        """Anti-detection must not stop on webdriver detection alone."""
        observer = AntiDetectionObserver()
        signal = AutomationDetectionSignal(
            signal_type="webdriver",
            details="navigator.webdriver is true",
            detected_at=datetime.now(timezone.utc),
            url="https://example.com",
        )
        assert observer.should_stop([signal]) is False
    
    def test_raise_if_should_stop(self):
        """Anti-detection must raise AutomationDetectedError when should stop."""
        observer = AntiDetectionObserver()
        signal = AutomationDetectionSignal(
            signal_type="captcha",
            details="CAPTCHA detected",
            detected_at=datetime.now(timezone.utc),
            url="https://example.com",
        )
        
        with pytest.raises(AutomationDetectedError) as exc_info:
            observer.raise_if_should_stop([signal])
        
        assert "NO STEALTH, NO EVASION, NO BYPASS" in str(exc_info.value)
    
    def test_get_signals(self):
        """Anti-detection must track all signals."""
        observer = AntiDetectionObserver()
        observer.detect_rate_limit(429, url="https://example.com")
        
        signals = observer.get_signals()
        assert len(signals) == 1
        assert signals[0].signal_type == "rate_limit"


# ============================================================================
# Error Classification Tests
# ============================================================================


class TestErrorClassification:
    """Test error classification for hardening errors."""
    
    def test_configuration_error_is_hard_stop(self):
        """ConfigurationError must be classified as HARD STOP."""
        from execution_layer.errors import is_hard_stop
        error = ConfigurationError("test")
        assert is_hard_stop(error) is True
    
    def test_response_validation_error_is_hard_stop(self):
        """ResponseValidationError must be classified as HARD STOP."""
        from execution_layer.errors import is_hard_stop
        error = ResponseValidationError("test")
        assert is_hard_stop(error) is True
    
    def test_retry_exhausted_error_is_hard_stop(self):
        """RetryExhaustedError must be classified as HARD STOP."""
        from execution_layer.errors import is_hard_stop
        error = RetryExhaustedError("test")
        assert is_hard_stop(error) is True
    
    def test_hash_chain_verification_error_is_hard_stop(self):
        """HashChainVerificationError must be classified as HARD STOP."""
        from execution_layer.errors import is_hard_stop
        error = HashChainVerificationError("test")
        assert is_hard_stop(error) is True
    
    def test_automation_detected_error_is_blocking(self):
        """AutomationDetectedError must be classified as BLOCKING."""
        from execution_layer.errors import is_blocking
        error = AutomationDetectedError("test")
        assert is_blocking(error) is True
