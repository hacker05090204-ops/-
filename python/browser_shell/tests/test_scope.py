# PHASE-13 GOVERNANCE COMPLIANCE
# Tests for TASK-3.1, 3.2, 3.3: Scope Enforcement
# Requirement: 2.1, 2.2, 2.3 (Scope Enforcement)
#
# MANDATORY DECLARATION:
# Phase-13 must not alter execution authority, human control,
# governance friction, audit invariants, or legal accountability.

"""Tests for scope enforcement - governance-enforcing tests."""

import pytest
import tempfile


# =============================================================================
# TASK-3.1: Scope Definition Parser Tests
# =============================================================================

class TestScopeAcceptsExplicitTargets:
    """Verify explicit domain list accepted."""

    def test_single_domain_accepted(self):
        """Single explicit domain must be accepted."""
        from browser_shell.scope import ScopeParser, ScopeParseResult
        
        parser = ScopeParser()
        result = parser.parse("example.com")
        
        assert result.valid is True
        assert "example.com" in result.targets

    def test_multiple_domains_accepted(self):
        """Multiple explicit domains must be accepted."""
        from browser_shell.scope import ScopeParser
        
        parser = ScopeParser()
        result = parser.parse("example.com,test.com,api.example.com")
        
        assert result.valid is True
        assert len(result.targets) == 3
        assert "example.com" in result.targets
        assert "test.com" in result.targets
        assert "api.example.com" in result.targets


class TestScopeRejectsWildcards:
    """Verify *.example.com rejected."""

    def test_asterisk_wildcard_rejected(self):
        """Asterisk wildcard must be rejected."""
        from browser_shell.scope import ScopeParser
        
        parser = ScopeParser()
        result = parser.parse("*.example.com")
        
        assert result.valid is False
        assert "wildcard" in result.error_message.lower()

    def test_question_wildcard_rejected(self):
        """Question mark wildcard must be rejected."""
        from browser_shell.scope import ScopeParser
        
        parser = ScopeParser()
        result = parser.parse("example?.com")
        
        assert result.valid is False
        assert "wildcard" in result.error_message.lower()


class TestScopeRejectsRegex:
    """Verify regex patterns rejected."""

    def test_regex_pattern_rejected(self):
        """Regex patterns must be rejected."""
        from browser_shell.scope import ScopeParser
        
        parser = ScopeParser()
        
        # Common regex patterns
        patterns = [
            "example\\.com",
            "[a-z]+.com",
            "example.com|test.com",
            "^example.com$",
            "example.com.*",
        ]
        
        for pattern in patterns:
            result = parser.parse(pattern)
            assert result.valid is False, f"Pattern {pattern} should be rejected"


class TestScopeRejectsInheritance:
    """Verify 'includes subdomains' rejected."""

    def test_includes_subdomains_rejected(self):
        """'includes subdomains' marker must be rejected."""
        from browser_shell.scope import ScopeParser
        
        parser = ScopeParser()
        result = parser.parse("example.com includes subdomains")
        
        assert result.valid is False
        assert "subdomain" in result.error_message.lower() or "inherit" in result.error_message.lower()

    def test_all_subdomains_rejected(self):
        """'all subdomains' marker must be rejected."""
        from browser_shell.scope import ScopeParser
        
        parser = ScopeParser()
        result = parser.parse("example.com all subdomains")
        
        assert result.valid is False


class TestScopeRequiresHumanConfirmation:
    """Verify confirmation step required."""

    def test_scope_validator_requires_confirmation(self):
        """Scope activation requires human confirmation."""
        from browser_shell.scope import ScopeValidator
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            validator = ScopeValidator(storage=storage, hash_chain=chain)
            
            result = validator.activate_scope(
                scope_definition="example.com",
                session_id="session-001",
                human_confirmed=False,  # Not confirmed!
            )
            
            assert result.success is False
            assert "confirm" in result.error_message.lower()


# =============================================================================
# TASK-3.2: Scope Validation Gateway Tests
# =============================================================================

class TestAllRequestsValidated:
    """Verify no request bypasses validation."""

    def test_validate_in_scope_request(self):
        """In-scope request must pass validation."""
        from browser_shell.scope import ScopeValidator
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            validator = ScopeValidator(storage=storage, hash_chain=chain)
            
            validator.activate_scope(
                scope_definition="example.com",
                session_id="session-001",
                human_confirmed=True,
            )
            
            result = validator.validate_request(
                target="example.com",
                session_id="session-001",
            )
            
            assert result.allowed is True

    def test_validate_out_of_scope_request(self):
        """Out-of-scope request must fail validation."""
        from browser_shell.scope import ScopeValidator
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            validator = ScopeValidator(storage=storage, hash_chain=chain)
            
            validator.activate_scope(
                scope_definition="example.com",
                session_id="session-001",
                human_confirmed=True,
            )
            
            result = validator.validate_request(
                target="malicious.com",
                session_id="session-001",
            )
            
            assert result.allowed is False
            assert result.blocked is True


class TestOutOfScopeBlocked:
    """Verify unauthorized targets blocked."""

    def test_blocked_request_has_reason(self):
        """Blocked request must have reason."""
        from browser_shell.scope import ScopeValidator
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            validator = ScopeValidator(storage=storage, hash_chain=chain)
            
            validator.activate_scope(
                scope_definition="example.com",
                session_id="session-001",
                human_confirmed=True,
            )
            
            result = validator.validate_request(
                target="evil.com",
                session_id="session-001",
            )
            
            assert result.blocked is True
            assert "scope" in result.block_reason.lower()


class TestNoBypassMechanism:
    """Static analysis confirms no bypass path."""

    def test_no_bypass_method(self):
        """ScopeValidator must not have bypass method."""
        from browser_shell.scope import ScopeValidator
        
        methods = [m for m in dir(ScopeValidator) if 'bypass' in m.lower()]
        assert methods == [], f"Forbidden bypass methods found: {methods}"

    def test_no_skip_method(self):
        """ScopeValidator must not have skip method."""
        from browser_shell.scope import ScopeValidator
        
        methods = [m for m in dir(ScopeValidator) if 'skip' in m.lower()]
        assert methods == [], f"Forbidden skip methods found: {methods}"

    def test_no_override_method(self):
        """ScopeValidator must not have override method."""
        from browser_shell.scope import ScopeValidator
        
        methods = [m for m in dir(ScopeValidator) if 'override' in m.lower()]
        assert methods == [], f"Forbidden override methods found: {methods}"


class TestValidationAudited:
    """Verify all validations logged."""

    def test_scope_validation_logged(self):
        """Scope validation must be logged to audit trail."""
        from browser_shell.scope import ScopeValidator
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            validator = ScopeValidator(storage=storage, hash_chain=chain)
            
            validator.activate_scope(
                scope_definition="example.com",
                session_id="session-001",
                human_confirmed=True,
            )
            
            validator.validate_request(
                target="example.com",
                session_id="session-001",
            )
            
            entries = storage.read_all()
            action_types = [e.action_type for e in entries]
            
            assert "SCOPE_DEFINED" in action_types or "SCOPE_VALIDATED" in action_types


class TestBlockedRequestsAudited:
    """Verify blocked requests logged with context."""

    def test_blocked_request_logged(self):
        """Blocked request must be logged to audit trail."""
        from browser_shell.scope import ScopeValidator
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            validator = ScopeValidator(storage=storage, hash_chain=chain)
            
            validator.activate_scope(
                scope_definition="example.com",
                session_id="session-001",
                human_confirmed=True,
            )
            
            validator.validate_request(
                target="evil.com",
                session_id="session-001",
            )
            
            entries = storage.read_all()
            action_types = [e.action_type for e in entries]
            
            assert "SCOPE_VIOLATION" in action_types or "SCOPE_BLOCKED" in action_types


# =============================================================================
# TASK-3.3: Scope Immutability Tests
# =============================================================================

class TestScopeImmutableInSession:
    """Verify scope cannot be modified."""

    def test_scope_modification_rejected(self):
        """Scope modification within session must be rejected."""
        from browser_shell.scope import ScopeValidator
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            validator = ScopeValidator(storage=storage, hash_chain=chain)
            
            # Activate initial scope
            validator.activate_scope(
                scope_definition="example.com",
                session_id="session-001",
                human_confirmed=True,
            )
            
            # Attempt to modify scope in same session
            result = validator.activate_scope(
                scope_definition="other.com",
                session_id="session-001",  # Same session!
                human_confirmed=True,
            )
            
            assert result.success is False
            assert "immutable" in result.error_message.lower() or "already" in result.error_message.lower()


class TestScopeChangeRequiresTermination:
    """Verify session must end for scope change."""

    def test_different_session_can_have_different_scope(self):
        """Different session can have different scope."""
        from browser_shell.scope import ScopeValidator
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            validator = ScopeValidator(storage=storage, hash_chain=chain)
            
            # First session
            result1 = validator.activate_scope(
                scope_definition="example.com",
                session_id="session-001",
                human_confirmed=True,
            )
            assert result1.success is True
            
            # Different session can have different scope
            result2 = validator.activate_scope(
                scope_definition="other.com",
                session_id="session-002",  # Different session
                human_confirmed=True,
            )
            assert result2.success is True


class TestNoStateTransferOnReset:
    """Verify no data leaks across reset."""

    def test_scope_reset_clears_state(self):
        """Scope reset must clear all state."""
        from browser_shell.scope import ScopeValidator
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            validator = ScopeValidator(storage=storage, hash_chain=chain)
            
            # Activate scope
            validator.activate_scope(
                scope_definition="example.com",
                session_id="session-001",
                human_confirmed=True,
            )
            
            # Deactivate scope
            validator.deactivate_scope(session_id="session-001")
            
            # Validate request should fail (no active scope)
            result = validator.validate_request(
                target="example.com",
                session_id="session-001",
            )
            
            assert result.allowed is False


class TestNoAutomationInScope:
    """Verify no automation methods in scope module."""

    def test_no_auto_methods(self):
        """No auto_* methods allowed."""
        from browser_shell.scope import ScopeValidator
        
        methods = [m for m in dir(ScopeValidator) if m.startswith('auto')]
        assert methods == [], f"Forbidden auto methods found: {methods}"

    def test_no_expand_methods(self):
        """No expand_* methods allowed (no scope expansion)."""
        from browser_shell.scope import ScopeValidator
        
        methods = [m for m in dir(ScopeValidator) if m.startswith('expand')]
        assert methods == [], f"Forbidden expand methods found: {methods}"

    def test_no_learn_methods(self):
        """No learn_* methods allowed."""
        from browser_shell.scope import ScopeValidator
        
        methods = [m for m in dir(ScopeValidator) if m.startswith('learn')]
        assert methods == [], f"Forbidden learn methods found: {methods}"
