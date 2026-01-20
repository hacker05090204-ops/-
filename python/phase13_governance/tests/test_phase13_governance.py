"""PHASE 13 TESTS"""
import pytest

class TestGovernanceStatus:
    def test_exists(self):
        from phase13_governance import GovernanceStatus
        assert hasattr(GovernanceStatus, 'COMPLIANT')

class TestPolicies:
    def test_human_authority_is_mandatory(self):
        from phase13_governance import POLICY_HUMAN_AUTHORITY
        assert POLICY_HUMAN_AUTHORITY.is_mandatory is True

    def test_audit_trail_is_mandatory(self):
        from phase13_governance import POLICY_AUDIT_TRAIL
        assert POLICY_AUDIT_TRAIL.is_mandatory is True

class TestCreateGovernanceRecord:
    def test_creates_record(self):
        from phase13_governance import create_governance_record, GovernanceStatus
        record = create_governance_record("Test action", "actor-001", GovernanceStatus.COMPLIANT, "Approved")
        assert record.status == GovernanceStatus.COMPLIANT

    def test_validates_description(self):
        from phase13_governance import create_governance_record, GovernanceStatus
        with pytest.raises(ValueError):
            create_governance_record("", "actor-001", GovernanceStatus.COMPLIANT, "")

class TestIsGovernanceCompliant:
    def test_compliant(self):
        from phase13_governance import create_governance_record, GovernanceStatus, is_governance_compliant
        record = create_governance_record("Test", "actor", GovernanceStatus.COMPLIANT, "OK")
        assert is_governance_compliant(record) is True

    def test_non_compliant(self):
        from phase13_governance import create_governance_record, GovernanceStatus, is_governance_compliant
        record = create_governance_record("Test", "actor", GovernanceStatus.NON_COMPLIANT, "Issue")
        assert is_governance_compliant(record) is False
