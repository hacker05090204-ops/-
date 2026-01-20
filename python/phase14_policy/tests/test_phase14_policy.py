"""PHASE 14 TESTS"""
import pytest

class TestPolicyRules:
    def test_human_must_authorize_is_blocking(self):
        from phase14_policy import RULE_HUMAN_MUST_AUTHORIZE
        assert RULE_HUMAN_MUST_AUTHORIZE.is_blocking is True

    def test_no_automated_exploit_is_blocking(self):
        from phase14_policy import RULE_NO_AUTOMATED_EXPLOIT
        assert RULE_NO_AUTOMATED_EXPLOIT.is_blocking is True

class TestCheckPolicyCompliance:
    def test_no_violations_when_compliant(self):
        from phase14_policy import check_policy_compliance
        violations = check_policy_compliance(has_human_approval=True, has_audit=True)
        assert len(violations) == 0

    def test_violations_when_no_approval(self):
        from phase14_policy import check_policy_compliance
        violations = check_policy_compliance(has_human_approval=False, has_audit=True)
        assert len(violations) == 1

    def test_violations_when_no_audit(self):
        from phase14_policy import check_policy_compliance
        violations = check_policy_compliance(has_human_approval=True, has_audit=False)
        assert len(violations) == 1

    def test_multiple_violations(self):
        from phase14_policy import check_policy_compliance
        violations = check_policy_compliance(has_human_approval=False, has_audit=False)
        assert len(violations) == 2

class TestIsActionBlocked:
    def test_blocked_when_violations(self):
        from phase14_policy import check_policy_compliance, is_action_blocked
        violations = check_policy_compliance(has_human_approval=False, has_audit=True)
        assert is_action_blocked(violations) is True

    def test_not_blocked_when_no_violations(self):
        from phase14_policy import is_action_blocked
        assert is_action_blocked([]) is False
