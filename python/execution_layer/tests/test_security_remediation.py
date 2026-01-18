"""
Security Remediation Tests for Phase-4 Execution Layer

These tests verify that security controls BLOCK malicious inputs.
A test PASSING means the security control REJECTED the attack.

RISK-X1: Path Traversal / Write-Anywhere Prevention
RISK-X2: Evidence Leakage Prevention (HAR Redaction)
RISK-X3: Single-Request Enforcement
RISK-X4: JS Layer Verification (Option B: Display-Only)

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

import pytest
import json
import uuid
import threading
from pathlib import Path
from typing import Any

from execution_layer.security import (
    GovernanceViolation,
    # RISK-X1
    validate_execution_id,
    validate_session_id,
    validate_artifact_path,
    validate_file_path_relative,
    # RISK-X2
    redact_har_content,
    scan_for_credentials,
    validate_har_is_redacted,
    CredentialScanResult,
    # RISK-X3
    SingleRequestEnforcer,
    RequestSlotContext,
    EnforcedHTTPClient,
    # RISK-X4
    JS_LAYER_STATUS,
    JS_LAYER_AUTHORITATIVE,
    validate_js_not_authoritative,
)


# =============================================================================
# RISK-X1: PATH TRAVERSAL / WRITE-ANYWHERE PREVENTION TESTS
# =============================================================================

class TestPathTraversalPrevention:
    """Tests for RISK-X1: Path Traversal Prevention."""
    
    # --- execution_id validation ---
    
    def test_valid_uuid4_execution_id_accepted(self):
        """Valid UUIDv4 should be accepted."""
        valid_id = str(uuid.uuid4())
        result = validate_execution_id(valid_id)
        assert result == valid_id
    
    def test_path_traversal_in_execution_id_blocked(self):
        """Path traversal attempt in execution_id MUST be blocked."""
        with pytest.raises(GovernanceViolation, match="dangerous path pattern"):
            validate_execution_id("../../../etc/passwd")
    
    def test_encoded_path_traversal_in_execution_id_blocked(self):
        """URL-encoded path traversal MUST be blocked."""
        # Note: The %2e pattern is caught by the dangerous path regex directly
        with pytest.raises(GovernanceViolation, match="dangerous.*pattern"):
            validate_execution_id("%2e%2e%2f%2e%2e%2fetc%2fpasswd")
    
    def test_double_encoded_traversal_blocked(self):
        """Double URL-encoded traversal MUST be blocked."""
        with pytest.raises(GovernanceViolation, match="dangerous path pattern"):
            validate_execution_id("%252e%252e%252f")
    
    def test_absolute_path_in_execution_id_blocked(self):
        """Absolute path in execution_id MUST be blocked."""
        with pytest.raises(GovernanceViolation, match="dangerous path pattern"):
            validate_execution_id("/etc/passwd")
    
    def test_windows_absolute_path_blocked(self):
        """Windows absolute path MUST be blocked."""
        with pytest.raises(GovernanceViolation, match="dangerous path pattern"):
            validate_execution_id("C:\\Windows\\System32")
    
    def test_null_byte_injection_blocked(self):
        """Null byte injection MUST be blocked."""
        with pytest.raises(GovernanceViolation, match="dangerous path pattern"):
            validate_execution_id("valid\x00.txt")
    
    def test_newline_injection_blocked(self):
        """Newline injection MUST be blocked."""
        with pytest.raises(GovernanceViolation, match="dangerous path pattern"):
            validate_execution_id("valid\nmalicious")
    
    def test_overlong_utf8_encoding_blocked(self):
        """Overlong UTF-8 encoding MUST be blocked."""
        with pytest.raises(GovernanceViolation, match="dangerous path pattern"):
            validate_execution_id("%c0%af%c0%af")
    
    def test_none_execution_id_blocked(self):
        """None execution_id MUST be blocked."""
        with pytest.raises(GovernanceViolation, match="cannot be None"):
            validate_execution_id(None)
    
    def test_empty_execution_id_blocked(self):
        """Empty execution_id MUST be blocked."""
        with pytest.raises(GovernanceViolation, match="cannot be empty"):
            validate_execution_id("")
    
    def test_non_string_execution_id_blocked(self):
        """Non-string execution_id MUST be blocked."""
        with pytest.raises(GovernanceViolation, match="must be string"):
            validate_execution_id(12345)
    
    def test_non_uuid_format_blocked(self):
        """Non-UUIDv4 format MUST be blocked."""
        with pytest.raises(GovernanceViolation, match="must be valid UUIDv4"):
            validate_execution_id("not-a-uuid")
    
    def test_uuid_v1_blocked(self):
        """UUID v1 (not v4) MUST be blocked."""
        # UUID v1 has version 1 in position 14
        uuid_v1 = "550e8400-e29b-11d4-a716-446655440000"
        with pytest.raises(GovernanceViolation, match="must be valid UUIDv4"):
            validate_execution_id(uuid_v1)
    
    # --- session_id validation ---
    
    def test_valid_uuid4_session_id_accepted(self):
        """Valid UUIDv4 session_id should be accepted."""
        valid_id = str(uuid.uuid4())
        result = validate_session_id(valid_id)
        assert result == valid_id
    
    def test_path_traversal_in_session_id_blocked(self):
        """Path traversal in session_id MUST be blocked."""
        with pytest.raises(GovernanceViolation, match="dangerous path pattern"):
            validate_session_id("../../../etc/passwd")
    
    # --- artifact_path validation ---
    
    def test_valid_artifact_path_accepted(self, tmp_path):
        """Valid path within artifacts root should be accepted."""
        artifacts_root = tmp_path / "artifacts"
        artifacts_root.mkdir()
        valid_path = artifacts_root / "test.har"
        
        result = validate_artifact_path(str(valid_path), artifacts_root)
        assert result == valid_path.resolve()
    
    def test_path_traversal_escape_blocked(self, tmp_path):
        """Path traversal escaping artifacts root MUST be blocked."""
        artifacts_root = tmp_path / "artifacts"
        artifacts_root.mkdir()
        
        with pytest.raises(GovernanceViolation, match="parent directory traversal"):
            validate_artifact_path("../../../etc/passwd", artifacts_root)
    
    def test_symlink_escape_blocked(self, tmp_path):
        """Symlink escaping artifacts root MUST be blocked."""
        artifacts_root = tmp_path / "artifacts"
        artifacts_root.mkdir()
        
        # Create symlink pointing outside
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()
        symlink = artifacts_root / "escape"
        
        try:
            symlink.symlink_to(outside_dir)
            with pytest.raises(GovernanceViolation, match="escapes artifacts root"):
                validate_artifact_path(str(symlink / "file.txt"), artifacts_root)
        except OSError:
            pytest.skip("Symlink creation not supported")
    
    def test_none_path_blocked(self, tmp_path):
        """None path MUST be blocked."""
        with pytest.raises(GovernanceViolation, match="cannot be None"):
            validate_artifact_path(None, tmp_path)
    
    # --- file_path_relative validation ---
    
    def test_valid_relative_path_accepted(self):
        """Valid relative path should be accepted."""
        result = validate_file_path_relative("subdir/file.txt")
        assert result == "subdir/file.txt"
    
    def test_none_file_path_returns_none(self):
        """None file_path should return None."""
        result = validate_file_path_relative(None)
        assert result is None
    
    def test_absolute_file_path_blocked(self):
        """Absolute file path MUST be blocked."""
        # Note: Absolute paths are caught by the dangerous path regex (^/)
        with pytest.raises(GovernanceViolation, match="dangerous pattern"):
            validate_file_path_relative("/etc/passwd")


# =============================================================================
# RISK-X2: EVIDENCE LEAKAGE PREVENTION TESTS
# =============================================================================

class TestEvidenceLeakagePrevention:
    """Tests for RISK-X2: Evidence Leakage Prevention."""
    
    def _create_har_with_auth_header(self) -> dict:
        """Create HAR with Authorization header."""
        return {
            "log": {
                "entries": [{
                    "request": {
                        "headers": [
                            {"name": "Authorization", "value": "Bearer secret-token-12345"},
                            {"name": "Content-Type", "value": "application/json"},
                        ],
                        "cookies": [],
                    },
                    "response": {
                        "headers": [],
                        "cookies": [],
                    },
                }]
            }
        }
    
    def _create_har_with_cookies(self) -> dict:
        """Create HAR with cookies."""
        return {
            "log": {
                "entries": [{
                    "request": {
                        "headers": [],
                        "cookies": [
                            {"name": "session", "value": "secret-session-id"},
                        ],
                    },
                    "response": {
                        "headers": [],
                        "cookies": [
                            {"name": "auth_token", "value": "secret-auth-token"},
                        ],
                    },
                }]
            }
        }
    
    def _create_har_with_password_in_body(self) -> dict:
        """Create HAR with password in request body."""
        return {
            "log": {
                "entries": [{
                    "request": {
                        "headers": [],
                        "cookies": [],
                        "postData": {
                            "text": '{"username": "admin", "password": "supersecret123"}',
                        },
                    },
                    "response": {
                        "headers": [],
                        "cookies": [],
                    },
                }]
            }
        }
    
    def test_authorization_header_redacted(self):
        """Authorization header MUST be redacted."""
        har = self._create_har_with_auth_header()
        redacted = redact_har_content(har)
        
        auth_header = redacted["log"]["entries"][0]["request"]["headers"][0]
        assert auth_header["value"] == "[REDACTED]"
    
    def test_cookies_redacted(self):
        """Cookie values MUST be redacted."""
        har = self._create_har_with_cookies()
        redacted = redact_har_content(har)
        
        request_cookie = redacted["log"]["entries"][0]["request"]["cookies"][0]
        response_cookie = redacted["log"]["entries"][0]["response"]["cookies"][0]
        
        assert request_cookie["value"] == "[REDACTED]"
        assert response_cookie["value"] == "[REDACTED]"
    
    def test_password_in_body_redacted(self):
        """Password in request body MUST be redacted."""
        har = self._create_har_with_password_in_body()
        redacted = redact_har_content(har)
        
        body = redacted["log"]["entries"][0]["request"]["postData"]["text"]
        assert "supersecret123" not in body
        assert "[REDACTED]" in body
    
    def test_unredacted_har_rejected_at_validation(self):
        """Unredacted HAR MUST be rejected by validate_har_is_redacted."""
        har = self._create_har_with_auth_header()
        har_bytes = json.dumps(har).encode('utf-8')
        
        with pytest.raises(GovernanceViolation, match="unredacted"):
            validate_har_is_redacted(har_bytes)
    
    def test_redacted_har_accepted(self):
        """Properly redacted HAR should be accepted."""
        har = self._create_har_with_auth_header()
        redacted = redact_har_content(har)
        har_bytes = json.dumps(redacted).encode('utf-8')
        
        # Should not raise
        validate_har_is_redacted(har_bytes)
    
    def test_jwt_token_detected(self):
        """JWT tokens MUST be detected by credential scanner."""
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        result = scan_for_credentials(jwt)
        
        assert result.has_credentials is True
        assert len(result.patterns_found) > 0
    
    def test_aws_access_key_detected(self):
        """AWS access keys MUST be detected."""
        content = "aws_access_key_id = AKIAIOSFODNN7EXAMPLE"
        result = scan_for_credentials(content)
        
        assert result.has_credentials is True
    
    def test_clean_content_passes(self):
        """Content without credentials should pass."""
        content = "This is just normal text without any secrets."
        result = scan_for_credentials(content)
        
        assert result.has_credentials is False
        assert len(result.patterns_found) == 0
    
    def test_non_dict_har_rejected(self):
        """Non-dictionary HAR content MUST be rejected."""
        with pytest.raises(GovernanceViolation, match="must be a dictionary"):
            redact_har_content("not a dict")
    
    def test_invalid_utf8_har_rejected(self):
        """Invalid UTF-8 HAR content MUST be rejected."""
        invalid_bytes = b'\xff\xfe invalid utf-8'
        
        with pytest.raises(GovernanceViolation, match="valid UTF-8"):
            validate_har_is_redacted(invalid_bytes)


# =============================================================================
# RISK-X3: SINGLE-REQUEST ENFORCEMENT TESTS
# =============================================================================

class TestSingleRequestEnforcement:
    """Tests for RISK-X3: Single-Request Enforcement."""
    
    def test_single_request_allowed(self):
        """Single request per confirmation should be allowed."""
        enforcer = SingleRequestEnforcer("confirmation-123")
        
        with enforcer.acquire_request_slot():
            pass  # Request would happen here
        
        assert enforcer.is_consumed is True
        assert enforcer.request_count == 1
    
    def test_second_request_blocked(self):
        """Second request on same confirmation MUST be blocked."""
        enforcer = SingleRequestEnforcer("confirmation-123")
        
        # First request succeeds
        with enforcer.acquire_request_slot():
            pass
        
        # Second request MUST fail
        with pytest.raises(GovernanceViolation, match="already consumed"):
            with enforcer.acquire_request_slot():
                pass
    
    def test_multi_request_replay_blocked(self):
        """Multiple request replay attempts MUST be blocked."""
        enforcer = SingleRequestEnforcer("confirmation-456")
        
        # First request
        with enforcer.acquire_request_slot():
            pass
        
        # Attempt 5 more requests - all must fail
        for i in range(5):
            with pytest.raises(GovernanceViolation, match="already consumed"):
                with enforcer.acquire_request_slot():
                    pass
        
        # Request count should still be 1
        assert enforcer.request_count == 1
    
    def test_empty_confirmation_id_blocked(self):
        """Empty confirmation_id MUST be blocked."""
        with pytest.raises(GovernanceViolation, match="requires confirmation_id"):
            SingleRequestEnforcer("")
    
    def test_none_confirmation_id_blocked(self):
        """None confirmation_id MUST be blocked."""
        with pytest.raises(GovernanceViolation, match="requires confirmation_id"):
            SingleRequestEnforcer(None)
    
    def test_thread_safety(self):
        """Enforcement MUST be thread-safe."""
        enforcer = SingleRequestEnforcer("thread-test-123")
        results = []
        errors = []
        
        def try_acquire():
            try:
                with enforcer.acquire_request_slot():
                    results.append("success")
            except GovernanceViolation:
                errors.append("blocked")
        
        # Start 10 threads simultaneously
        threads = [threading.Thread(target=try_acquire) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Exactly one should succeed
        assert len(results) == 1
        assert len(errors) == 9
        assert enforcer.request_count == 1
    
    def test_enforced_http_client_single_request(self):
        """EnforcedHTTPClient should allow only one request."""
        enforcer = SingleRequestEnforcer("http-test-123")
        client = EnforcedHTTPClient(enforcer)
        
        # Mock request function
        def mock_request(method, url, **kwargs):
            return {"status": 200}
        
        # First request succeeds
        result = client.execute_request("GET", "https://example.com", mock_request)
        assert result["status"] == 200
        assert client.request_made is True
        
        # Second request fails
        with pytest.raises(GovernanceViolation, match="already consumed"):
            client.execute_request("GET", "https://example.com", mock_request)
    
    def test_slot_not_released_on_exception(self):
        """Request slot MUST NOT be released even if request fails."""
        enforcer = SingleRequestEnforcer("exception-test")
        
        # Request that raises exception
        try:
            with enforcer.acquire_request_slot():
                raise ValueError("Request failed")
        except ValueError:
            pass
        
        # Slot should still be consumed
        assert enforcer.is_consumed is True
        
        # Second attempt must fail
        with pytest.raises(GovernanceViolation, match="already consumed"):
            with enforcer.acquire_request_slot():
                pass


# =============================================================================
# RISK-X4: JS LAYER VERIFICATION TESTS
# =============================================================================

class TestJSLayerVerification:
    """Tests for RISK-X4: JS Layer Status (Option B: Display-Only)."""
    
    def test_js_layer_marked_display_only(self):
        """JS layer MUST be marked as display-only."""
        assert JS_LAYER_STATUS == "DISPLAY_ONLY"
    
    def test_js_layer_not_authoritative(self):
        """JS layer MUST NOT be authoritative."""
        assert JS_LAYER_AUTHORITATIVE is False
    
    def test_validate_js_not_authoritative_passes(self):
        """Validation should pass when JS is not authoritative."""
        # Should not raise
        validate_js_not_authoritative()


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestSecurityIntegration:
    """Integration tests for security controls working together."""
    
    def test_evidence_bundle_rejects_unredacted_har(self):
        """EvidenceBundle construction MUST reject unredacted HAR."""
        from execution_layer.types import EvidenceBundle, EvidenceArtifact, EvidenceType
        
        # Create unredacted HAR
        har = {
            "log": {
                "entries": [{
                    "request": {
                        "headers": [
                            {"name": "Authorization", "value": "Bearer secret"},
                        ],
                        "cookies": [],
                    },
                    "response": {"headers": [], "cookies": []},
                }]
            }
        }
        har_bytes = json.dumps(har).encode('utf-8')
        
        # Create artifact with unredacted content
        har_artifact = EvidenceArtifact.create(
            artifact_type=EvidenceType.HAR,
            content=har_bytes,
        )
        
        # Bundle construction should fail
        with pytest.raises(GovernanceViolation, match="unredacted"):
            EvidenceBundle(
                bundle_id="test-bundle",
                execution_id=str(uuid.uuid4()),
                har_file=har_artifact,
            )
    
    def test_evidence_bundle_accepts_redacted_har(self):
        """EvidenceBundle construction should accept redacted HAR."""
        from execution_layer.types import EvidenceBundle, EvidenceArtifact, EvidenceType
        
        # Create and redact HAR
        har = {
            "log": {
                "entries": [{
                    "request": {
                        "headers": [
                            {"name": "Authorization", "value": "[REDACTED]"},
                            {"name": "Content-Type", "value": "application/json"},
                        ],
                        "cookies": [],
                    },
                    "response": {"headers": [], "cookies": []},
                }]
            }
        }
        har_bytes = json.dumps(har).encode('utf-8')
        
        har_artifact = EvidenceArtifact.create(
            artifact_type=EvidenceType.HAR,
            content=har_bytes,
        )
        
        # Should succeed
        bundle = EvidenceBundle(
            bundle_id="test-bundle",
            execution_id=str(uuid.uuid4()),
            har_file=har_artifact,
        )
        assert bundle.bundle_id == "test-bundle"
    
    def test_evidence_bundle_rejects_invalid_execution_id(self):
        """EvidenceBundle MUST reject invalid execution_id."""
        from execution_layer.types import EvidenceBundle
        
        with pytest.raises((GovernanceViolation, ValueError)):
            EvidenceBundle(
                bundle_id="test-bundle",
                execution_id="../../../etc/passwd",
            )
    
    def test_evidence_artifact_rejects_traversal_in_file_path(self):
        """EvidenceArtifact MUST reject path traversal in file_path."""
        from execution_layer.types import EvidenceArtifact, EvidenceType
        
        with pytest.raises(GovernanceViolation, match="Path traversal"):
            EvidenceArtifact(
                artifact_id="test",
                artifact_type=EvidenceType.SCREENSHOT,
                content_hash="abc123",
                captured_at=None,  # Will use default
                file_path="../../../etc/passwd",
            )
