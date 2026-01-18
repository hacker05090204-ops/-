"""
Phase-4.2 Track B: PayloadGuard Pre-Integration Tests

Tests for PayloadGuard - egress request firewall.
Tests written BEFORE implementation per governance requirements.

Constraints verified:
- HTTPS only enforcement
- Method allow-list enforcement
- Header allow-list enforcement
- No payload mutation
- No header spoofing
- No retry logic
- Fail-closed on violation
- Auditable failures
"""

import pytest


class TestPayloadGuardHTTPS:
    """Tests for HTTPS-only enforcement."""

    def test_allows_https_url(self):
        """PayloadGuard must allow HTTPS URLs."""
        from execution_layer.payloadguard import PayloadGuard, RequestSpec
        guard = PayloadGuard()
        spec = RequestSpec(
            url='https://example.com/api',
            method='GET',
            headers={}
        )
        result = guard.check(spec)
        assert result.allowed is True

    def test_blocks_http_url(self):
        """PayloadGuard must block HTTP URLs."""
        from execution_layer.payloadguard import PayloadGuard, RequestSpec
        guard = PayloadGuard()
        spec = RequestSpec(
            url='http://example.com/api',
            method='GET',
            headers={}
        )
        result = guard.check(spec)
        assert result.allowed is False
        assert 'https' in result.reason.lower()

    def test_blocks_ftp_url(self):
        """PayloadGuard must block FTP URLs."""
        from execution_layer.payloadguard import PayloadGuard, RequestSpec
        guard = PayloadGuard()
        spec = RequestSpec(
            url='ftp://example.com/file',
            method='GET',
            headers={}
        )
        result = guard.check(spec)
        assert result.allowed is False

    def test_blocks_file_url(self):
        """PayloadGuard must block file:// URLs."""
        from execution_layer.payloadguard import PayloadGuard, RequestSpec
        guard = PayloadGuard()
        spec = RequestSpec(
            url='file:///etc/passwd',
            method='GET',
            headers={}
        )
        result = guard.check(spec)
        assert result.allowed is False


class TestPayloadGuardMethods:
    """Tests for HTTP method allow-list."""

    def test_allows_get_method(self):
        """PayloadGuard must allow GET method."""
        from execution_layer.payloadguard import PayloadGuard, RequestSpec
        guard = PayloadGuard()
        spec = RequestSpec(
            url='https://example.com/api',
            method='GET',
            headers={}
        )
        result = guard.check(spec)
        assert result.allowed is True

    def test_allows_post_method(self):
        """PayloadGuard must allow POST method."""
        from execution_layer.payloadguard import PayloadGuard, RequestSpec
        guard = PayloadGuard()
        spec = RequestSpec(
            url='https://example.com/api',
            method='POST',
            headers={}
        )
        result = guard.check(spec)
        assert result.allowed is True

    def test_allows_head_method(self):
        """PayloadGuard must allow HEAD method."""
        from execution_layer.payloadguard import PayloadGuard, RequestSpec
        guard = PayloadGuard()
        spec = RequestSpec(
            url='https://example.com/api',
            method='HEAD',
            headers={}
        )
        result = guard.check(spec)
        assert result.allowed is True

    def test_blocks_delete_method(self):
        """PayloadGuard must block DELETE method by default."""
        from execution_layer.payloadguard import PayloadGuard, RequestSpec
        guard = PayloadGuard()
        spec = RequestSpec(
            url='https://example.com/api',
            method='DELETE',
            headers={}
        )
        result = guard.check(spec)
        assert result.allowed is False
        assert 'method' in result.reason.lower()

    def test_blocks_put_method(self):
        """PayloadGuard must block PUT method by default."""
        from execution_layer.payloadguard import PayloadGuard, RequestSpec
        guard = PayloadGuard()
        spec = RequestSpec(
            url='https://example.com/api',
            method='PUT',
            headers={}
        )
        result = guard.check(spec)
        assert result.allowed is False

    def test_blocks_patch_method(self):
        """PayloadGuard must block PATCH method by default."""
        from execution_layer.payloadguard import PayloadGuard, RequestSpec
        guard = PayloadGuard()
        spec = RequestSpec(
            url='https://example.com/api',
            method='PATCH',
            headers={}
        )
        result = guard.check(spec)
        assert result.allowed is False


class TestPayloadGuardHeaders:
    """Tests for header allow-list enforcement."""

    def test_allows_standard_headers(self):
        """PayloadGuard must allow standard headers."""
        from execution_layer.payloadguard import PayloadGuard, RequestSpec
        guard = PayloadGuard()
        spec = RequestSpec(
            url='https://example.com/api',
            method='GET',
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'TestAgent/1.0'
            }
        )
        result = guard.check(spec)
        assert result.allowed is True

    def test_blocks_host_header_override(self):
        """PayloadGuard must block Host header override attempts."""
        from execution_layer.payloadguard import PayloadGuard, RequestSpec
        guard = PayloadGuard()
        spec = RequestSpec(
            url='https://example.com/api',
            method='GET',
            headers={
                'Host': 'malicious.com'
            }
        )
        result = guard.check(spec)
        assert result.allowed is False
        assert 'header' in result.reason.lower()

    def test_blocks_x_forwarded_for_spoofing(self):
        """PayloadGuard must block X-Forwarded-For spoofing."""
        from execution_layer.payloadguard import PayloadGuard, RequestSpec
        guard = PayloadGuard()
        spec = RequestSpec(
            url='https://example.com/api',
            method='GET',
            headers={
                'X-Forwarded-For': '127.0.0.1'
            }
        )
        result = guard.check(spec)
        assert result.allowed is False

    def test_blocks_x_real_ip_spoofing(self):
        """PayloadGuard must block X-Real-IP spoofing."""
        from execution_layer.payloadguard import PayloadGuard, RequestSpec
        guard = PayloadGuard()
        spec = RequestSpec(
            url='https://example.com/api',
            method='GET',
            headers={
                'X-Real-IP': '10.0.0.1'
            }
        )
        result = guard.check(spec)
        assert result.allowed is False


class TestPayloadGuardNoMutation:
    """Tests ensuring PayloadGuard does not mutate payloads."""

    def test_does_not_modify_url(self):
        """PayloadGuard must not modify the URL."""
        from execution_layer.payloadguard import PayloadGuard, RequestSpec
        guard = PayloadGuard()
        original_url = 'https://example.com/api?param=value'
        spec = RequestSpec(
            url=original_url,
            method='GET',
            headers={}
        )
        guard.check(spec)
        assert spec.url == original_url

    def test_does_not_modify_headers(self):
        """PayloadGuard must not modify headers."""
        from execution_layer.payloadguard import PayloadGuard, RequestSpec
        guard = PayloadGuard()
        original_headers = {'Content-Type': 'application/json'}
        spec = RequestSpec(
            url='https://example.com/api',
            method='GET',
            headers=original_headers.copy()
        )
        guard.check(spec)
        assert spec.headers == original_headers

    def test_does_not_modify_method(self):
        """PayloadGuard must not modify the method."""
        from execution_layer.payloadguard import PayloadGuard, RequestSpec
        guard = PayloadGuard()
        spec = RequestSpec(
            url='https://example.com/api',
            method='POST',
            headers={}
        )
        guard.check(spec)
        assert spec.method == 'POST'


class TestPayloadGuardNoRetry:
    """Tests ensuring PayloadGuard has no retry logic."""

    def test_no_retry_method(self):
        """PayloadGuard must not have retry methods."""
        from execution_layer.payloadguard import PayloadGuard
        guard = PayloadGuard()
        assert not hasattr(guard, 'retry')
        assert not hasattr(guard, 'should_retry')
        assert not hasattr(guard, 'retry_count')
        assert not hasattr(guard, 'max_retries')

    def test_check_returns_immediately(self):
        """PayloadGuard check must return immediately without retry."""
        import time
        from execution_layer.payloadguard import PayloadGuard, RequestSpec
        guard = PayloadGuard()
        spec = RequestSpec(
            url='http://blocked.com',  # Will be blocked
            method='GET',
            headers={}
        )
        start = time.perf_counter()
        guard.check(spec)
        elapsed = time.perf_counter() - start
        # Should complete in under 10ms (no retry delays)
        assert elapsed < 0.01


class TestPayloadGuardFailClosed:
    """Tests for fail-closed behavior."""

    def test_empty_url_blocked(self):
        """PayloadGuard must block empty URLs."""
        from execution_layer.payloadguard import PayloadGuard, RequestSpec
        guard = PayloadGuard()
        spec = RequestSpec(
            url='',
            method='GET',
            headers={}
        )
        result = guard.check(spec)
        assert result.allowed is False

    def test_malformed_url_blocked(self):
        """PayloadGuard must block malformed URLs."""
        from execution_layer.payloadguard import PayloadGuard, RequestSpec
        guard = PayloadGuard()
        spec = RequestSpec(
            url='not-a-valid-url',
            method='GET',
            headers={}
        )
        result = guard.check(spec)
        assert result.allowed is False

    def test_empty_method_blocked(self):
        """PayloadGuard must block empty methods."""
        from execution_layer.payloadguard import PayloadGuard, RequestSpec
        guard = PayloadGuard()
        spec = RequestSpec(
            url='https://example.com',
            method='',
            headers={}
        )
        result = guard.check(spec)
        assert result.allowed is False


class TestPayloadGuardAuditability:
    """Tests for audit trail support."""

    def test_check_result_has_reason(self):
        """Check result must include reason for audit."""
        from execution_layer.payloadguard import PayloadGuard, RequestSpec
        guard = PayloadGuard()
        spec = RequestSpec(
            url='http://blocked.com',
            method='GET',
            headers={}
        )
        result = guard.check(spec)
        assert result.reason is not None
        assert len(result.reason) > 0

    def test_check_result_has_timestamp(self):
        """Check result must include timestamp for audit."""
        from execution_layer.payloadguard import PayloadGuard, RequestSpec
        guard = PayloadGuard()
        spec = RequestSpec(
            url='https://example.com',
            method='GET',
            headers={}
        )
        result = guard.check(spec)
        assert result.timestamp is not None

    def test_check_result_to_dict(self):
        """Check result must be serializable to dict."""
        from execution_layer.payloadguard import PayloadGuard, RequestSpec
        guard = PayloadGuard()
        spec = RequestSpec(
            url='https://example.com',
            method='GET',
            headers={}
        )
        result = guard.check(spec)
        audit_dict = result.to_dict()
        assert 'allowed' in audit_dict
        assert 'reason' in audit_dict
        assert 'timestamp' in audit_dict

    def test_blocked_request_logged(self):
        """Blocked requests must be auditable."""
        from execution_layer.payloadguard import PayloadGuard, RequestSpec
        guard = PayloadGuard()
        spec = RequestSpec(
            url='http://blocked.com',
            method='DELETE',
            headers={'Host': 'evil.com'}
        )
        result = guard.check(spec)
        assert result.allowed is False
        # All violations should be captured
        assert len(result.violations) > 0
