"""
Phase-9 Scope Checker Tests

Tests for scope validation functionality.
"""

import pytest
from datetime import datetime

from browser_assistant.scope_check import ScopeChecker


class TestScopeChecker:
    """Test scope checker functionality."""
    
    def test_in_scope_domain(self, scope_checker):
        """Verify in-scope domain is detected."""
        warning = scope_checker.check_scope("https://app.example.com/page")
        
        assert warning.scope_status == "in_scope"
        assert warning.human_confirmation_required is True
        assert warning.does_not_block is True
    
    def test_in_scope_wildcard_domain(self, scope_checker):
        """Verify wildcard domain matching works."""
        warning = scope_checker.check_scope("https://sub.example.com/page")
        
        assert warning.scope_status == "in_scope"
    
    def test_in_scope_exact_domain(self, scope_checker):
        """Verify exact domain matching works."""
        warning = scope_checker.check_scope("https://test.local/page")
        
        assert warning.scope_status == "in_scope"
    
    def test_in_scope_ip_range(self, scope_checker):
        """Verify IP range matching works."""
        warning = scope_checker.check_scope("http://10.0.0.1/api")
        
        assert warning.scope_status == "in_scope"
    
    def test_out_of_scope_domain(self, scope_checker):
        """Verify out-of-scope domain is detected."""
        warning = scope_checker.check_scope("https://evil.com/page")
        
        assert warning.scope_status == "out_of_scope"
        assert warning.human_confirmation_required is True
        assert warning.does_not_block is True
    
    def test_excluded_path(self, scope_checker):
        """Verify excluded paths are detected."""
        warning = scope_checker.check_scope("https://app.example.com/admin/users")
        
        assert warning.scope_status == "excluded"
        assert warning.human_confirmation_required is True
    
    def test_ambiguous_scope(self, scope_checker):
        """Verify ambiguous scope is detected."""
        # Add a domain that could be ambiguous
        scope_checker.add_authorized_domain("example.org")
        
        warning = scope_checker.check_scope("https://example.org.evil.com/page")
        
        # Should be ambiguous or out of scope
        assert warning.scope_status in ("ambiguous", "out_of_scope")
    
    def test_unknown_scope_no_config(self):
        """Verify unknown scope when no config."""
        checker = ScopeChecker()
        warning = checker.check_scope("https://example.com/page")
        
        assert warning.scope_status == "unknown"
        assert warning.human_confirmation_required is True
    
    def test_warning_never_blocks(self, scope_checker):
        """Verify warnings never block."""
        # Even for out-of-scope
        warning = scope_checker.check_scope("https://evil.com/page")
        assert warning.does_not_block is True
        
        # Even for excluded
        warning = scope_checker.check_scope("https://app.example.com/admin/")
        assert warning.does_not_block is True
    
    def test_warning_is_advisory(self, scope_checker):
        """Verify warnings are advisory only."""
        warning = scope_checker.check_scope("https://app.example.com/page")
        
        assert warning.is_advisory_only is True
    
    def test_add_authorized_domain(self, scope_checker):
        """Verify domains can be added."""
        scope_checker.add_authorized_domain("newdomain.com")
        
        warning = scope_checker.check_scope("https://newdomain.com/page")
        assert warning.scope_status == "in_scope"
    
    def test_add_authorized_ip_range(self):
        """Verify IP ranges can be added."""
        checker = ScopeChecker()
        checker.add_authorized_ip_range("172.16.0.0/12")
        
        warning = checker.check_scope("http://172.16.0.1/api")
        assert warning.scope_status == "in_scope"
    
    def test_add_excluded_path(self, scope_checker):
        """Verify excluded paths can be added."""
        scope_checker.add_excluded_path("/secret/*")
        
        warning = scope_checker.check_scope("https://app.example.com/secret/data")
        assert warning.scope_status == "excluded"
    
    def test_get_scope_summary(self, scope_checker):
        """Verify scope summary generation."""
        summary = scope_checker.get_scope_summary()
        
        assert "example.com" in summary
        assert "10.0.0.0" in summary
        assert "/admin" in summary
    
    def test_authorization_reference(self, scope_checker):
        """Verify authorization reference is included."""
        warning = scope_checker.check_scope(
            "https://app.example.com/page",
            authorization_reference="AUTH-2025-001",
        )
        
        assert warning.authorization_reference == "AUTH-2025-001"


class TestScopeCheckerNoForbiddenMethods:
    """Verify checker has no forbidden methods."""
    
    def test_no_block_navigation(self, scope_checker):
        """Verify block_navigation method does not exist."""
        assert not hasattr(scope_checker, "block_navigation")
    
    def test_no_prevent_testing(self, scope_checker):
        """Verify prevent_testing method does not exist."""
        assert not hasattr(scope_checker, "prevent_testing")
    
    def test_no_enforce_scope(self, scope_checker):
        """Verify enforce_scope method does not exist."""
        assert not hasattr(scope_checker, "enforce_scope")
    
    def test_no_deny_access(self, scope_checker):
        """Verify deny_access method does not exist."""
        assert not hasattr(scope_checker, "deny_access")
    
    def test_no_is_authorized(self, scope_checker):
        """Verify is_authorized method does not exist."""
        assert not hasattr(scope_checker, "is_authorized")
    
    def test_no_require_authorization(self, scope_checker):
        """Verify require_authorization method does not exist."""
        assert not hasattr(scope_checker, "require_authorization")
    
    def test_no_validate_scope(self, scope_checker):
        """Verify validate_scope method does not exist."""
        assert not hasattr(scope_checker, "validate_scope")
