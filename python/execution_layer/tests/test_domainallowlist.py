"""
Phase-4.2 Track C: Domain Allow-List Pre-Integration Tests

Tests for Domain Allow-List - boundary enforcement for outbound requests.
Tests written BEFORE implementation per governance requirements.

Constraints verified:
- Exact match rules
- Suffix match rules (*.example.com)
- Reject IP literals
- Reject redirect escapes
- Integrates ONLY with PayloadGuard
- Fail-closed on violation
- Auditable decisions
"""

import pytest


class TestDomainAllowListExactMatch:
    """Tests for exact domain matching."""

    def test_allows_exact_match_domain(self):
        """Domain allow-list must allow exact match domains."""
        from execution_layer.domainallowlist import DomainAllowList
        allow_list = DomainAllowList(allowed_domains=['example.com'])
        result = allow_list.check('example.com')
        assert result.allowed is True

    def test_blocks_non_matching_domain(self):
        """Domain allow-list must block non-matching domains."""
        from execution_layer.domainallowlist import DomainAllowList
        allow_list = DomainAllowList(allowed_domains=['example.com'])
        result = allow_list.check('malicious.com')
        assert result.allowed is False

    def test_exact_match_is_case_insensitive(self):
        """Domain matching must be case-insensitive."""
        from execution_layer.domainallowlist import DomainAllowList
        allow_list = DomainAllowList(allowed_domains=['Example.COM'])
        result = allow_list.check('example.com')
        assert result.allowed is True

    def test_blocks_subdomain_without_wildcard(self):
        """Exact match must not allow subdomains."""
        from execution_layer.domainallowlist import DomainAllowList
        allow_list = DomainAllowList(allowed_domains=['example.com'])
        result = allow_list.check('sub.example.com')
        assert result.allowed is False


class TestDomainAllowListSuffixMatch:
    """Tests for suffix/wildcard domain matching."""

    def test_allows_wildcard_subdomain(self):
        """Wildcard must allow subdomains."""
        from execution_layer.domainallowlist import DomainAllowList
        allow_list = DomainAllowList(allowed_domains=['*.example.com'])
        result = allow_list.check('api.example.com')
        assert result.allowed is True

    def test_wildcard_allows_deep_subdomain(self):
        """Wildcard must allow deep subdomains."""
        from execution_layer.domainallowlist import DomainAllowList
        allow_list = DomainAllowList(allowed_domains=['*.example.com'])
        result = allow_list.check('deep.sub.example.com')
        assert result.allowed is True

    def test_wildcard_does_not_match_base_domain(self):
        """Wildcard *.example.com must NOT match example.com itself."""
        from execution_layer.domainallowlist import DomainAllowList
        allow_list = DomainAllowList(allowed_domains=['*.example.com'])
        result = allow_list.check('example.com')
        assert result.allowed is False

    def test_wildcard_blocks_different_domain(self):
        """Wildcard must not match different domains."""
        from execution_layer.domainallowlist import DomainAllowList
        allow_list = DomainAllowList(allowed_domains=['*.example.com'])
        result = allow_list.check('api.malicious.com')
        assert result.allowed is False


class TestDomainAllowListIPLiterals:
    """Tests for IP literal rejection."""

    def test_blocks_ipv4_literal(self):
        """Domain allow-list must block IPv4 literals."""
        from execution_layer.domainallowlist import DomainAllowList
        allow_list = DomainAllowList(allowed_domains=['example.com'])
        result = allow_list.check('192.168.1.1')
        assert result.allowed is False
        assert 'ip' in result.reason.lower()

    def test_blocks_ipv6_literal(self):
        """Domain allow-list must block IPv6 literals."""
        from execution_layer.domainallowlist import DomainAllowList
        allow_list = DomainAllowList(allowed_domains=['example.com'])
        result = allow_list.check('[::1]')
        assert result.allowed is False

    def test_blocks_localhost(self):
        """Domain allow-list must block localhost."""
        from execution_layer.domainallowlist import DomainAllowList
        allow_list = DomainAllowList(allowed_domains=['example.com'])
        result = allow_list.check('localhost')
        assert result.allowed is False

    def test_blocks_127_0_0_1(self):
        """Domain allow-list must block 127.0.0.1."""
        from execution_layer.domainallowlist import DomainAllowList
        allow_list = DomainAllowList(allowed_domains=['example.com'])
        result = allow_list.check('127.0.0.1')
        assert result.allowed is False

    def test_blocks_internal_ip_ranges(self):
        """Domain allow-list must block internal IP ranges."""
        from execution_layer.domainallowlist import DomainAllowList
        allow_list = DomainAllowList(allowed_domains=['example.com'])
        
        internal_ips = ['10.0.0.1', '172.16.0.1', '192.168.0.1']
        for ip in internal_ips:
            result = allow_list.check(ip)
            assert result.allowed is False, f"Should block {ip}"


class TestDomainAllowListRedirectEscapes:
    """Tests for redirect escape prevention."""

    def test_blocks_at_sign_escape(self):
        """Domain allow-list must block @ sign URL escapes."""
        from execution_layer.domainallowlist import DomainAllowList
        allow_list = DomainAllowList(allowed_domains=['example.com'])
        # Attacker tries: https://example.com@malicious.com
        result = allow_list.check('example.com@malicious.com')
        assert result.allowed is False

    def test_blocks_backslash_escape(self):
        """Domain allow-list must block backslash escapes."""
        from execution_layer.domainallowlist import DomainAllowList
        allow_list = DomainAllowList(allowed_domains=['example.com'])
        result = allow_list.check('example.com\\@malicious.com')
        assert result.allowed is False

    def test_blocks_encoded_characters(self):
        """Domain allow-list must block URL-encoded escape attempts."""
        from execution_layer.domainallowlist import DomainAllowList
        allow_list = DomainAllowList(allowed_domains=['example.com'])
        result = allow_list.check('example.com%40malicious.com')
        assert result.allowed is False

    def test_blocks_null_byte_injection(self):
        """Domain allow-list must block null byte injection."""
        from execution_layer.domainallowlist import DomainAllowList
        allow_list = DomainAllowList(allowed_domains=['example.com'])
        result = allow_list.check('example.com\x00malicious.com')
        assert result.allowed is False


class TestDomainAllowListFailClosed:
    """Tests for fail-closed behavior."""

    def test_empty_domain_blocked(self):
        """Empty domain must be blocked."""
        from execution_layer.domainallowlist import DomainAllowList
        allow_list = DomainAllowList(allowed_domains=['example.com'])
        result = allow_list.check('')
        assert result.allowed is False

    def test_none_domain_blocked(self):
        """None domain must be blocked."""
        from execution_layer.domainallowlist import DomainAllowList
        allow_list = DomainAllowList(allowed_domains=['example.com'])
        result = allow_list.check(None)
        assert result.allowed is False

    def test_empty_allow_list_blocks_all(self):
        """Empty allow-list must block all domains."""
        from execution_layer.domainallowlist import DomainAllowList
        allow_list = DomainAllowList(allowed_domains=[])
        result = allow_list.check('example.com')
        assert result.allowed is False


class TestDomainAllowListAuditability:
    """Tests for audit trail support."""

    def test_check_result_has_reason(self):
        """Check result must include reason for audit."""
        from execution_layer.domainallowlist import DomainAllowList
        allow_list = DomainAllowList(allowed_domains=['example.com'])
        result = allow_list.check('malicious.com')
        assert result.reason is not None
        assert len(result.reason) > 0

    def test_check_result_has_timestamp(self):
        """Check result must include timestamp for audit."""
        from execution_layer.domainallowlist import DomainAllowList
        allow_list = DomainAllowList(allowed_domains=['example.com'])
        result = allow_list.check('example.com')
        assert result.timestamp is not None

    def test_check_result_to_dict(self):
        """Check result must be serializable to dict."""
        from execution_layer.domainallowlist import DomainAllowList
        allow_list = DomainAllowList(allowed_domains=['example.com'])
        result = allow_list.check('example.com')
        audit_dict = result.to_dict()
        assert 'allowed' in audit_dict
        assert 'reason' in audit_dict
        assert 'domain' in audit_dict
        assert 'timestamp' in audit_dict


class TestDomainAllowListNoMutation:
    """Tests ensuring Domain Allow-List does not mutate inputs."""

    def test_does_not_modify_domain(self):
        """Domain allow-list must not modify the domain string."""
        from execution_layer.domainallowlist import DomainAllowList
        allow_list = DomainAllowList(allowed_domains=['example.com'])
        original_domain = 'test.example.com'
        domain_copy = original_domain
        allow_list.check(domain_copy)
        assert domain_copy == original_domain

    def test_does_not_modify_allow_list(self):
        """Domain allow-list must not modify the allowed domains."""
        from execution_layer.domainallowlist import DomainAllowList
        original_list = ['example.com', 'test.com']
        allow_list = DomainAllowList(allowed_domains=original_list.copy())
        allow_list.check('malicious.com')
        # Original list should be unchanged
        assert original_list == ['example.com', 'test.com']


class TestDomainAllowListNoRetry:
    """Tests ensuring Domain Allow-List has no retry logic."""

    def test_no_retry_method(self):
        """Domain allow-list must not have retry methods."""
        from execution_layer.domainallowlist import DomainAllowList
        allow_list = DomainAllowList(allowed_domains=['example.com'])
        assert not hasattr(allow_list, 'retry')
        assert not hasattr(allow_list, 'should_retry')
        assert not hasattr(allow_list, 'retry_count')

    def test_check_returns_immediately(self):
        """Domain allow-list check must return immediately."""
        import time
        from execution_layer.domainallowlist import DomainAllowList
        allow_list = DomainAllowList(allowed_domains=['example.com'])
        
        start = time.perf_counter()
        for _ in range(1000):
            allow_list.check('malicious.com')
        elapsed = time.perf_counter() - start
        
        # 1000 checks should complete in under 100ms
        assert elapsed < 0.1


class TestDomainAllowListExtractFromURL:
    """Tests for extracting domain from full URLs."""

    def test_extracts_domain_from_https_url(self):
        """Must correctly extract domain from HTTPS URL."""
        from execution_layer.domainallowlist import DomainAllowList
        allow_list = DomainAllowList(allowed_domains=['example.com'])
        result = allow_list.check_url('https://example.com/path')
        assert result.allowed is True

    def test_extracts_domain_from_url_with_port(self):
        """Must correctly extract domain from URL with port."""
        from execution_layer.domainallowlist import DomainAllowList
        allow_list = DomainAllowList(allowed_domains=['example.com'])
        result = allow_list.check_url('https://example.com:8443/path')
        assert result.allowed is True

    def test_blocks_url_with_disallowed_domain(self):
        """Must block URL with disallowed domain."""
        from execution_layer.domainallowlist import DomainAllowList
        allow_list = DomainAllowList(allowed_domains=['example.com'])
        result = allow_list.check_url('https://malicious.com/path')
        assert result.allowed is False

