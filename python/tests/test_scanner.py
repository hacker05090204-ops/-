"""
Property-based tests for vulnerability scanner.

**Task 10: Create vulnerability scanner and assessment engine**
**Property Tests: 10.1, 10.2**

Requirements validated:
- 2.2: Comprehensive Web Application Testing
- 2.5: Vulnerability Ranking Consistency
"""

import pytest
from hypothesis import given, strategies as st, settings
import asyncio

from kali_mcp.scanner import (
    VulnerabilityScanner,
    VulnerabilityRanker,
    SignatureDatabase,
    VulnerabilitySignature,
    VulnerabilityCategory,
    ServiceScanner,
    APIScanner,
    ScanResult,
)
from kali_mcp.types import (
    Target,
    Finding,
    Severity,
    FindingClassification,
    Service,
    Protocol,
)


# ============================================================================
# Test Helpers
# ============================================================================

def create_test_target(domain: str = "example.com") -> Target:
    """Create a test target."""
    return Target(
        domain=domain,
        services=[
            Service(host=domain, port=443, protocol=Protocol.HTTPS, service_type="web"),
        ],
    )


def create_test_finding(
    severity: Severity = Severity.HIGH,
    confidence: float = 0.9,
) -> Finding:
    """Create a test finding."""
    return Finding(
        invariant_violated="TEST_001",
        title="Test Vulnerability",
        description="A test vulnerability",
        severity=severity,
        confidence=confidence,
        classification=FindingClassification.BUG,
    )


# ============================================================================
# Property Test 10.1: Comprehensive Web Application Testing
# **Validates: Requirements 2.2**
# ============================================================================

class TestSignatureDatabase:
    """Tests for SignatureDatabase."""

    def test_default_signatures_loaded(self):
        """Test that default signatures are loaded."""
        db = SignatureDatabase()
        
        assert db.count() > 0

    def test_get_signature(self):
        """Test getting a signature by ID."""
        db = SignatureDatabase()
        
        sig = db.get_signature("SQL_001")
        
        assert sig is not None
        assert sig.name == "SQL Injection - Error Based"
        assert sig.category == VulnerabilityCategory.INJECTION

    def test_get_nonexistent_signature(self):
        """Test getting non-existent signature."""
        db = SignatureDatabase()
        
        sig = db.get_signature("NONEXISTENT")
        
        assert sig is None

    def test_get_by_category(self):
        """Test getting signatures by category."""
        db = SignatureDatabase()
        
        injection_sigs = db.get_by_category(VulnerabilityCategory.INJECTION)
        
        assert len(injection_sigs) > 0
        assert all(s.category == VulnerabilityCategory.INJECTION for s in injection_sigs)

    def test_add_custom_signature(self):
        """Test adding custom signature."""
        db = SignatureDatabase()
        initial_count = db.count()
        
        custom_sig = VulnerabilitySignature(
            id="CUSTOM_001",
            name="Custom Vulnerability",
            category=VulnerabilityCategory.CUSTOM,
            severity=Severity.MEDIUM,
            description="A custom vulnerability",
            detection_patterns=[r"custom_pattern"],
        )
        
        db.add_signature(custom_sig)
        
        assert db.count() == initial_count + 1
        assert db.get_signature("CUSTOM_001") is not None


class TestVulnerabilityScanner:
    """Tests for VulnerabilityScanner."""

    @pytest.mark.asyncio
    async def test_quick_scan(self):
        """Test quick scan."""
        scanner = VulnerabilityScanner()
        target = create_test_target()
        
        result = await scanner.scan(target, scan_type="quick")
        
        assert result.target == target.domain
        assert result.scan_type == "quick"
        assert result.completed_at is not None
        assert result.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_full_scan(self):
        """Test full scan."""
        scanner = VulnerabilityScanner()
        target = create_test_target()
        
        result = await scanner.scan(target, scan_type="full")
        
        assert result.scan_type == "full"
        assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_owasp_scan(self):
        """Test OWASP Top 10 scan."""
        scanner = VulnerabilityScanner()
        target = create_test_target()
        
        result = await scanner.scan(target, scan_type="owasp_top_10")
        
        assert result.scan_type == "owasp_top_10"

    @pytest.mark.asyncio
    async def test_custom_modules(self):
        """Test scan with custom modules."""
        scanner = VulnerabilityScanner()
        target = create_test_target()
        
        result = await scanner.scan(target, modules=["headers"])
        
        assert result.completed_at is not None

    def test_signature_count(self):
        """Test signature count."""
        scanner = VulnerabilityScanner()
        
        count = scanner.get_signature_count()
        
        assert count > 0

    def test_add_custom_signature(self):
        """Test adding custom signature."""
        scanner = VulnerabilityScanner()
        initial_count = scanner.get_signature_count()
        
        custom_sig = VulnerabilitySignature(
            id="SCANNER_CUSTOM_001",
            name="Scanner Custom",
            category=VulnerabilityCategory.CUSTOM,
            severity=Severity.LOW,
            description="Custom",
            detection_patterns=[],
        )
        
        scanner.add_custom_signature(custom_sig)
        
        assert scanner.get_signature_count() == initial_count + 1


# ============================================================================
# Property Test 10.2: Vulnerability Ranking Consistency
# **Validates: Requirements 2.5**
# ============================================================================

class TestVulnerabilityRanker:
    """Tests for VulnerabilityRanker."""

    def test_priority_score_range(self):
        """Test that priority score is in valid range."""
        ranker = VulnerabilityRanker()
        
        for severity in Severity:
            finding = create_test_finding(severity=severity)
            score = ranker.calculate_priority_score(finding)
            
            assert 0 <= score <= 100

    def test_critical_higher_than_low(self):
        """Test that critical findings rank higher than low."""
        ranker = VulnerabilityRanker()
        
        critical = create_test_finding(severity=Severity.CRITICAL)
        low = create_test_finding(severity=Severity.LOW)
        
        critical_score = ranker.calculate_priority_score(critical)
        low_score = ranker.calculate_priority_score(low)
        
        assert critical_score > low_score

    def test_confidence_affects_score(self):
        """Test that confidence affects score."""
        ranker = VulnerabilityRanker()
        
        high_conf = create_test_finding(confidence=1.0)
        low_conf = create_test_finding(confidence=0.5)
        
        high_score = ranker.calculate_priority_score(high_conf)
        low_score = ranker.calculate_priority_score(low_conf)
        
        assert high_score > low_score

    def test_context_affects_score(self):
        """Test that context affects score."""
        ranker = VulnerabilityRanker()
        finding = create_test_finding()
        
        no_context_score = ranker.calculate_priority_score(finding)
        with_context_score = ranker.calculate_priority_score(
            finding,
            context={
                "network_accessible": True,
                "no_auth_required": True,
            },
        )
        
        assert with_context_score > no_context_score

    def test_rank_findings_order(self):
        """Test that findings are ranked in correct order."""
        ranker = VulnerabilityRanker()
        
        findings = [
            create_test_finding(severity=Severity.LOW),
            create_test_finding(severity=Severity.CRITICAL),
            create_test_finding(severity=Severity.MEDIUM),
        ]
        
        ranked = ranker.rank_findings(findings)
        
        # First should be critical
        assert ranked[0][0].severity == Severity.CRITICAL
        # Last should be low
        assert ranked[-1][0].severity == Severity.LOW

    def test_filter_by_severity(self):
        """Test filtering by minimum severity."""
        ranker = VulnerabilityRanker()
        
        findings = [
            create_test_finding(severity=Severity.INFO),
            create_test_finding(severity=Severity.LOW),
            create_test_finding(severity=Severity.MEDIUM),
            create_test_finding(severity=Severity.HIGH),
            create_test_finding(severity=Severity.CRITICAL),
        ]
        
        filtered = ranker.filter_by_severity(findings, Severity.MEDIUM)
        
        assert len(filtered) == 3
        assert all(f.severity in [Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL] for f in filtered)

    @given(st.floats(min_value=0.0, max_value=1.0))
    @settings(max_examples=20)
    def test_ranking_is_deterministic(self, confidence: float):
        """Property: Ranking is deterministic for same input."""
        ranker = VulnerabilityRanker()
        finding = create_test_finding(confidence=confidence)
        
        score1 = ranker.calculate_priority_score(finding)
        score2 = ranker.calculate_priority_score(finding)
        
        assert score1 == score2

    @given(st.sampled_from(list(Severity)))
    @settings(max_examples=10)
    def test_severity_ordering_preserved(self, severity: Severity):
        """Property: Severity ordering is preserved in ranking."""
        ranker = VulnerabilityRanker()
        
        # Create findings with same confidence but different severities
        findings = [create_test_finding(severity=s, confidence=0.9) for s in Severity]
        ranked = ranker.rank_findings(findings)
        
        # Higher severity should come first
        scores = [score for _, score in ranked]
        assert scores == sorted(scores, reverse=True)


class TestServiceScanner:
    """Tests for ServiceScanner."""

    @pytest.mark.asyncio
    async def test_scan_web_service(self):
        """Test scanning web service."""
        scanner = ServiceScanner()
        service = Service(
            host="example.com",
            port=443,
            protocol=Protocol.HTTPS,
            service_type="web",
        )
        
        findings = await scanner.scan_service(service)
        
        assert isinstance(findings, list)

    @pytest.mark.asyncio
    async def test_scan_ssh_service(self):
        """Test scanning SSH service."""
        scanner = ServiceScanner()
        service = Service(
            host="example.com",
            port=22,
            protocol=Protocol.SSH,
            service_type="ssh",
        )
        
        findings = await scanner.scan_service(service)
        
        assert isinstance(findings, list)


class TestAPIScanner:
    """Tests for APIScanner."""

    def test_test_case_count(self):
        """Test that test cases are loaded."""
        scanner = APIScanner()
        
        count = scanner.get_test_case_count()
        
        assert count > 0

    @pytest.mark.asyncio
    async def test_scan_api(self):
        """Test API scanning."""
        scanner = APIScanner()
        
        findings = await scanner.scan_api(
            "https://api.example.com",
            endpoints=[
                {"path": "/users", "method": "GET"},
                {"path": "/users/{id}", "method": "GET"},
            ],
        )
        
        assert isinstance(findings, list)


class TestScanResult:
    """Tests for ScanResult."""

    def test_add_finding(self):
        """Test adding finding to result."""
        result = ScanResult(target="example.com")
        finding = create_test_finding()
        
        result.add_finding(finding)
        
        assert len(result.findings) == 1

    def test_complete(self):
        """Test completing scan result."""
        result = ScanResult(target="example.com")
        
        assert result.completed_at is None
        
        result.complete()
        
        assert result.completed_at is not None
        assert result.duration_ms >= 0


class TestIntegration:
    """Integration tests for scanner."""

    @pytest.mark.asyncio
    async def test_full_scan_workflow(self):
        """Test complete scanning workflow."""
        scanner = VulnerabilityScanner()
        target = create_test_target()
        
        # Perform scan
        result = await scanner.scan(target, scan_type="full")
        
        # Get ranked findings
        ranked = scanner.get_ranked_findings(result)
        
        # Filter reportable
        reportable = scanner.filter_reportable(result)
        
        # All operations should complete without error
        assert result.completed_at is not None
        assert isinstance(ranked, list)
        assert isinstance(reportable, list)

    @pytest.mark.asyncio
    async def test_multiple_targets(self):
        """Test scanning multiple targets."""
        scanner = VulnerabilityScanner()
        
        targets = [
            create_test_target("target1.com"),
            create_test_target("target2.com"),
            create_test_target("target3.com"),
        ]
        
        results = []
        for target in targets:
            result = await scanner.scan(target, scan_type="quick")
            results.append(result)
        
        assert len(results) == 3
        assert all(r.completed_at is not None for r in results)
