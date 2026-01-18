"""Tests for Rule Engine."""

import pytest
from hypothesis import given, strategies as st, assume

from kali_mcp.rule_engine import (
    RuleEngine,
    PolicyParser,
    ScopeValidator,
    RiskAssessor,
    ComplianceMonitor,
    RiskLevel,
    ValidationResult,
)
from kali_mcp.types import (
    BugBountyProgram,
    ScopeDefinition,
    RateLimits,
)


class TestPolicyParser:
    """Tests for PolicyParser."""

    def test_parse_basic_program(self):
        """Test parsing a basic program."""
        program = BugBountyProgram(
            name="Test",
            platform="hackerone",
            scope=ScopeDefinition(
                in_scope_domains=["*.example.com"],
                out_of_scope_domains=["admin.example.com"],
            ),
        )
        
        parser = PolicyParser()
        parsed = parser.parse(program)
        
        assert "scope" in parsed
        assert "rate_limits" in parsed
        assert parsed["safe_harbor"] is True


class TestScopeValidator:
    """Tests for ScopeValidator."""

    def test_validate_in_scope_domain(self):
        """Test validating in-scope domains."""
        program = BugBountyProgram(
            name="Test",
            platform="private",
            scope=ScopeDefinition(
                in_scope_domains=["*.example.com", "example.com"],
            ),
        )
        
        validator = ScopeValidator(program)
        
        result = validator.validate_target("api.example.com")
        assert result.is_valid is True
        
        result = validator.validate_target("example.com")
        assert result.is_valid is True

    def test_validate_out_of_scope_domain(self):
        """Test validating out-of-scope domains."""
        program = BugBountyProgram(
            name="Test",
            platform="private",
            scope=ScopeDefinition(
                in_scope_domains=["*.example.com"],
                out_of_scope_domains=["admin.example.com"],
            ),
        )
        
        validator = ScopeValidator(program)
        
        # Explicitly out of scope
        result = validator.validate_target("admin.example.com")
        assert result.is_valid is False
        
        # Not in scope at all
        result = validator.validate_target("other.com")
        assert result.is_valid is False

    @given(st.text(alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='-'), min_size=1, max_size=20))
    def test_scope_validation_consistency(self, subdomain: str):
        """Property: Scope validation is consistent for same input."""
        # **Feature: kali-mcp-toolkit, Property 6: Scope Validation Consistency**
        assume(subdomain.isalnum() or '-' in subdomain)
        
        program = BugBountyProgram(
            name="Test",
            platform="private",
            scope=ScopeDefinition(
                in_scope_domains=["*.example.com"],
            ),
        )
        
        validator = ScopeValidator(program)
        domain = f"{subdomain}.example.com"
        
        # Validate twice - should get same result
        result1 = validator.validate_target(domain)
        result2 = validator.validate_target(domain)
        
        assert result1.is_valid == result2.is_valid


class TestRiskAssessor:
    """Tests for RiskAssessor."""

    def test_assess_low_risk_action(self):
        """Test assessing low risk action."""
        assessor = RiskAssessor()
        
        risk = assessor.assess_action("normal_request")
        assert risk.level in [RiskLevel.LOW, RiskLevel.MEDIUM]
        assert risk.should_stop is False

    def test_assess_high_risk_action(self):
        """Test assessing high risk action."""
        assessor = RiskAssessor()
        
        # Simulate multiple high-risk actions
        for _ in range(10):
            assessor.assess_action("exploitation_attempt")
        
        risk = assessor.assess_action("exploitation_attempt")
        assert risk.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]

    def test_risk_history_affects_score(self):
        """Test that risk history affects score."""
        assessor = RiskAssessor()
        
        initial_score = assessor.get_ban_risk_score()
        
        # Add some risky actions
        assessor.assess_action("aggressive_scan")
        assessor.assess_action("rate_limit_hit")
        
        new_score = assessor.get_ban_risk_score()
        assert new_score > initial_score

    def test_clear_history(self):
        """Test clearing risk history."""
        assessor = RiskAssessor()
        
        assessor.assess_action("aggressive_scan")
        assert assessor.get_ban_risk_score() > 0
        
        assessor.clear_history()
        assert assessor.get_ban_risk_score() == 0


class TestComplianceMonitor:
    """Tests for ComplianceMonitor."""

    def test_check_compliant_action(self):
        """Test checking a compliant action."""
        program = BugBountyProgram(
            name="Test",
            platform="private",
            scope=ScopeDefinition(
                in_scope_domains=["*.example.com"],
            ),
        )
        
        monitor = ComplianceMonitor(program)
        
        result = monitor.check_action(
            action="normal_request",
            target="api.example.com",
        )
        
        assert result["allowed"] is True
        assert len(result["violations"]) == 0

    def test_check_out_of_scope_action(self):
        """Test checking an out-of-scope action."""
        program = BugBountyProgram(
            name="Test",
            platform="private",
            scope=ScopeDefinition(
                in_scope_domains=["*.example.com"],
            ),
        )
        
        monitor = ComplianceMonitor(program)
        
        result = monitor.check_action(
            action="normal_request",
            target="other.com",
        )
        
        assert result["allowed"] is False
        assert len(result["violations"]) > 0

    def test_compliance_report(self):
        """Test generating compliance report."""
        program = BugBountyProgram(
            name="Test",
            platform="private",
            scope=ScopeDefinition(
                in_scope_domains=["*.example.com"],
            ),
        )
        
        monitor = ComplianceMonitor(program)
        
        # Generate some violations
        monitor.check_action("normal_request", "other.com")
        
        report = monitor.get_compliance_report()
        
        assert report["program"] == "Test"
        assert report["total_violations"] >= 1


class TestRuleEngine:
    """Tests for RuleEngine."""

    def test_engine_without_program(self):
        """Test engine behavior without program configured."""
        engine = RuleEngine()
        
        result = engine.validate_target("example.com")
        assert result.is_valid is False
        assert "No program configured" in result.reason

    def test_engine_with_program(self):
        """Test engine with program configured."""
        program = BugBountyProgram(
            name="Test",
            platform="private",
            scope=ScopeDefinition(
                in_scope_domains=["*.example.com"],
            ),
        )
        
        engine = RuleEngine(program)
        
        result = engine.validate_target("api.example.com")
        assert result.is_valid is True

    def test_set_program(self):
        """Test setting program after creation."""
        engine = RuleEngine()
        
        program = BugBountyProgram(
            name="Test",
            platform="private",
            scope=ScopeDefinition(
                in_scope_domains=["*.example.com"],
            ),
        )
        
        engine.set_program(program)
        
        result = engine.validate_target("api.example.com")
        assert result.is_valid is True

    @given(st.booleans())
    def test_policy_violation_blocking(self, is_in_scope: bool):
        """Property: Out-of-scope actions are always blocked."""
        # **Feature: kali-mcp-toolkit, Property 7: Policy Violation Prevention**
        program = BugBountyProgram(
            name="Test",
            platform="private",
            scope=ScopeDefinition(
                in_scope_domains=["*.example.com"],
            ),
        )
        
        engine = RuleEngine(program)
        
        if is_in_scope:
            target = "api.example.com"
        else:
            target = "other.com"
        
        result = engine.check_compliance("normal_request", target)
        
        if is_in_scope:
            assert result["allowed"] is True
        else:
            assert result["allowed"] is False
            assert len(result["violations"]) > 0