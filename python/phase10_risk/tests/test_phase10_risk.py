"""PHASE 10 TESTS — NO SEVERITY VERIFICATION"""
import pytest

class TestRiskCategory:
    def test_exists(self):
        from phase10_risk import RiskCategory
        assert hasattr(RiskCategory, 'INJECTION')

class TestRiskDescriptor:
    def test_no_severity_field(self):
        """CRITICAL: RiskDescriptor must NOT have severity."""
        from phase10_risk import RiskDescriptor
        fields = [f for f in RiskDescriptor.__dataclass_fields__.keys()]
        assert 'severity' not in fields
        assert 'score' not in fields
        assert 'priority' not in fields
        assert 'rank' not in fields

class TestCreateRiskDescriptor:
    def test_creates_descriptor(self):
        from phase10_risk import create_risk_descriptor, RiskCategory
        risk = create_risk_descriptor("r-001", RiskCategory.INJECTION, "SQL Injection", "Login Form")
        assert risk.category == RiskCategory.INJECTION

    def test_validates_description(self):
        from phase10_risk import create_risk_descriptor, RiskCategory
        with pytest.raises(ValueError):
            create_risk_descriptor("r-001", RiskCategory.INJECTION, "", "component")

class TestNoScoringInModule:
    def test_no_scoring_no_severity(self):
        from phase10_risk import risk
        public = [a for a in dir(risk) if not a.startswith('_')]
        for attr in public:
            assert 'score' not in attr.lower(), f"FORBIDDEN: score in {attr}"
            assert 'severity' not in attr.lower(), f"FORBIDDEN: severity in {attr}"
            assert 'rank' not in attr.lower(), f"FORBIDDEN: rank in {attr}"
            assert 'priority' not in attr.lower(), f"FORBIDDEN: priority in {attr}"
