"""Tests for type definitions."""

import pytest
from hypothesis import given, strategies as st
from datetime import datetime

from kali_mcp.types import (
    Target,
    BugBountyProgram,
    Finding,
    HuntSession,
    Severity,
    FindingClassification,
    ScopeDefinition,
    Service,
    Protocol,
    TechnologyProfile,
)


class TestSeverity:
    """Tests for Severity enum."""

    def test_cvss_ranges(self):
        """Test CVSS ranges for each severity level."""
        assert Severity.INFO.cvss_range() == (0.0, 0.0)
        assert Severity.LOW.cvss_range() == (0.1, 3.9)
        assert Severity.MEDIUM.cvss_range() == (4.0, 6.9)
        assert Severity.HIGH.cvss_range() == (7.0, 8.9)
        assert Severity.CRITICAL.cvss_range() == (9.0, 10.0)


class TestTarget:
    """Tests for Target dataclass."""

    def test_target_creation(self):
        """Test basic target creation."""
        target = Target(domain="example.com")
        assert target.domain == "example.com"
        assert target.subdomains == []
        assert target.services == []

    def test_target_with_services(self):
        """Test target with services."""
        service = Service(
            host="example.com",
            port=443,
            protocol=Protocol.HTTPS,
            service_type="web",
        )
        target = Target(domain="example.com", services=[service])
        assert len(target.services) == 1
        assert target.services[0].port == 443

    def test_target_to_dict(self):
        """Test target serialization."""
        target = Target(domain="example.com", subdomains=["api.example.com"])
        data = target.to_dict()
        assert data["domain"] == "example.com"
        assert "api.example.com" in data["subdomains"]


class TestBugBountyProgram:
    """Tests for BugBountyProgram dataclass."""

    def test_program_creation(self):
        """Test basic program creation."""
        program = BugBountyProgram(name="Test Program", platform="hackerone")
        assert program.name == "Test Program"
        assert program.safe_harbor is True

    def test_scope_validation(self):
        """Test scope validation."""
        scope = ScopeDefinition(
            in_scope_domains=["*.example.com", "example.com"],
            out_of_scope_domains=["admin.example.com"],
        )
        program = BugBountyProgram(name="Test", platform="private", scope=scope)
        
        # In scope
        assert program.is_in_scope("example.com") is True
        assert program.is_in_scope("api.example.com") is True
        
        # Out of scope
        assert program.is_in_scope("admin.example.com") is False
        assert program.is_in_scope("other.com") is False

    @given(st.text(min_size=1, max_size=50))
    def test_program_name_property(self, name: str):
        """Property: Program name is preserved."""
        # **Feature: kali-mcp-toolkit, Property 5: Program Policy Parsing**
        program = BugBountyProgram(name=name, platform="test")
        assert program.name == name


class TestFinding:
    """Tests for Finding dataclass."""

    def test_finding_creation(self):
        """Test basic finding creation."""
        finding = Finding(
            invariant_violated="AUTH_001",
            title="Test Finding",
            severity=Severity.HIGH,
            confidence=0.9,
            classification=FindingClassification.BUG,
        )
        assert finding.is_bug() is True
        assert finding.severity == Severity.HIGH

    def test_finding_reportable(self):
        """Test reportable finding criteria."""
        # Reportable finding
        finding = Finding(
            invariant_violated="AUTH_001",
            confidence=0.9,
            classification=FindingClassification.BUG,
        )
        assert finding.is_reportable() is True
        
        # Not reportable - low confidence
        finding_low = Finding(
            invariant_violated="AUTH_001",
            confidence=0.5,
            classification=FindingClassification.BUG,
        )
        assert finding_low.is_reportable() is False
        
        # Not reportable - signal classification
        finding_signal = Finding(
            invariant_violated="AUTH_001",
            confidence=0.9,
            classification=FindingClassification.SIGNAL,
        )
        assert finding_signal.is_reportable() is False

    @given(st.floats(min_value=0.0, max_value=1.0))
    def test_confidence_bounds(self, confidence: float):
        """Property: Confidence affects reportability correctly."""
        # **Feature: kali-mcp-toolkit, Property 24: Formal Bug Definition Validation**
        finding = Finding(
            invariant_violated="TEST_001",
            confidence=confidence,
            classification=FindingClassification.BUG,
        )
        if confidence >= 0.8:
            assert finding.is_reportable() is True
        else:
            assert finding.is_reportable() is False


class TestHuntSession:
    """Tests for HuntSession dataclass."""

    def test_session_creation(self):
        """Test basic session creation."""
        target = Target(domain="example.com")
        session = HuntSession(target=target)
        assert session.is_active is True
        assert len(session.findings) == 0

    def test_add_finding(self):
        """Test adding findings to session."""
        session = HuntSession()
        finding = Finding(
            invariant_violated="AUTH_001",
            classification=FindingClassification.BUG,
        )
        session.add_finding(finding)
        assert len(session.findings) == 1

    def test_get_bugs(self):
        """Test filtering bugs from findings."""
        session = HuntSession()
        
        # Add bug
        session.add_finding(Finding(
            invariant_violated="AUTH_001",
            classification=FindingClassification.BUG,
        ))
        
        # Add signal
        session.add_finding(Finding(
            invariant_violated="AUTH_002",
            classification=FindingClassification.SIGNAL,
        ))
        
        bugs = session.get_bugs()
        assert len(bugs) == 1
        assert bugs[0].classification == FindingClassification.BUG

    def test_session_completion(self):
        """Test session completion."""
        session = HuntSession()
        assert session.is_active is True
        assert session.completed_at is None
        
        session.complete()
        
        assert session.is_active is False
        assert session.completed_at is not None

    @given(st.lists(st.sampled_from([FindingClassification.BUG, FindingClassification.SIGNAL]), min_size=0, max_size=20))
    def test_bug_count_property(self, classifications: list):
        """Property: Bug count equals findings with BUG classification."""
        # **Feature: kali-mcp-toolkit, Property 26: Signal Classification Accuracy**
        session = HuntSession()
        
        for i, classification in enumerate(classifications):
            session.add_finding(Finding(
                invariant_violated=f"TEST_{i}",
                classification=classification,
            ))
        
        expected_bugs = sum(1 for c in classifications if c == FindingClassification.BUG)
        assert len(session.get_bugs()) == expected_bugs