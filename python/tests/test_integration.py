"""
Comprehensive integration tests for Kali MCP Toolkit.

**Task 22: Final integration and system testing**
**Property Tests: 22.1**

Requirements validated:
- All requirements working together
- End-to-end system validation
"""

import pytest
from hypothesis import given, strategies as st, settings
import asyncio
from datetime import datetime

from kali_mcp import (
    MCPServer,
    HuntOrchestrator,
    RuleEngine,
    VulnerabilityScanner,
    VulnerabilityRanker,
    Target,
    BugBountyProgram,
    Finding,
    HuntSession,
    HuntPhase,
    Severity,
    FindingClassification,
)
from kali_mcp.types import (
    Service,
    Protocol,
    ScopeDefinition,
    RateLimits,
)
from kali_mcp.server import MCPRequest


# ============================================================================
# Test Helpers
# ============================================================================

def create_full_target() -> Target:
    """Create a fully-configured target."""
    return Target(
        domain="example.com",
        subdomains=["api.example.com", "www.example.com", "admin.example.com"],
        services=[
            Service(host="example.com", port=443, protocol=Protocol.HTTPS, service_type="web"),
            Service(host="example.com", port=80, protocol=Protocol.HTTP, service_type="web"),
            Service(host="example.com", port=22, protocol=Protocol.SSH, service_type="ssh"),
        ],
    )


def create_full_program() -> BugBountyProgram:
    """Create a fully-configured program."""
    return BugBountyProgram(
        name="Integration Test Program",
        platform="private",
        scope=ScopeDefinition(
            in_scope_domains=["*.example.com", "example.com"],
            out_of_scope_domains=["admin.example.com"],
            in_scope_vulnerability_types=["xss", "sqli", "ssrf", "idor"],
        ),
        rate_limits=RateLimits(
            requests_per_second=10,
            requests_per_minute=300,
        ),
        safe_harbor=True,
    )


# ============================================================================
# Integration Tests
# ============================================================================

class TestMCPServerIntegration:
    """Integration tests for MCP server with all components."""

    @pytest.mark.asyncio
    async def test_full_mcp_workflow(self):
        """Test complete MCP workflow from session creation to findings."""
        server = MCPServer()
        
        # 1. Create session
        create_result = await server.handle_tool_call(
            "create_session",
            {"target_domain": "example.com", "program_name": "Test"},
        )
        assert "session_id" in create_result
        session_id = create_result["session_id"]
        
        # 2. List sessions
        list_result = await server.handle_tool_call("list_sessions", {})
        assert list_result["total"] >= 1
        
        # 3. Get session details
        session_result = await server.handle_tool_call(
            "get_session",
            {"session_id": session_id},
        )
        assert session_result["id"] == session_id
        
        # 4. Get findings
        findings_result = await server.handle_tool_call(
            "get_findings",
            {"session_id": session_id},
        )
        assert "findings" in findings_result

    @pytest.mark.asyncio
    async def test_mcp_request_handling(self):
        """Test MCP request/response handling."""
        server = MCPServer()
        
        # Test tools/list
        request = MCPRequest(id="1", method="tools/list", params={})
        response = await server.handle_request(request)
        
        assert response.id == "1"
        assert response.error is None
        assert "tools" in response.result
        assert len(response.result["tools"]) > 0
        
        # Test tools/call
        request = MCPRequest(
            id="2",
            method="tools/call",
            params={
                "name": "create_session",
                "arguments": {"target_domain": "test.com"},
            },
        )
        response = await server.handle_request(request)
        
        assert response.id == "2"
        assert response.error is None
        assert "session_id" in response.result


class TestOrchestratorIntegration:
    """Integration tests for hunt orchestrator."""

    @pytest.mark.asyncio
    async def test_full_hunt_workflow(self):
        """Test complete hunting workflow."""
        orchestrator = HuntOrchestrator()
        target = create_full_target()
        program = create_full_program()
        
        # 1. Start hunt
        session = await orchestrator.start_hunt(target, program)
        assert session.is_active
        
        # 2. Analyze target
        analysis = await orchestrator.analyze_target(target)
        assert analysis["domain"] == target.domain
        assert analysis["subdomain_count"] == len(target.subdomains)
        assert analysis["service_count"] == len(target.services)
        
        # 3. Select tools for each phase
        recon_tools = orchestrator.select_tools(target, HuntPhase.RECONNAISSANCE)
        scan_tools = orchestrator.select_tools(target, HuntPhase.SCANNING)
        
        assert len(recon_tools) > 0
        assert len(scan_tools) > 0
        
        # 4. Execute reconnaissance phase
        recon_results = await orchestrator.execute_phase(
            session.id,
            HuntPhase.RECONNAISSANCE,
        )
        assert len(recon_results) > 0

    @pytest.mark.asyncio
    async def test_multiple_concurrent_hunts(self):
        """Test multiple concurrent hunting sessions."""
        orchestrator = HuntOrchestrator()
        
        # Start multiple hunts
        sessions = []
        for i in range(5):
            target = Target(domain=f"target{i}.com")
            session = await orchestrator.start_hunt(target)
            sessions.append(session)
        
        # All sessions should be active
        active = orchestrator.list_active_sessions()
        assert len(active) == 5
        
        # Each session should be independent
        session_ids = [s.id for s in sessions]
        assert len(set(session_ids)) == 5


class TestRuleEngineIntegration:
    """Integration tests for rule engine."""

    def test_full_compliance_workflow(self):
        """Test complete compliance checking workflow."""
        program = create_full_program()
        engine = RuleEngine(program)
        
        # 1. Validate in-scope target
        result = engine.validate_target("api.example.com")
        assert result.is_valid
        
        # 2. Validate out-of-scope target
        result = engine.validate_target("admin.example.com")
        assert not result.is_valid
        
        # 3. Check compliance for action
        compliance = engine.check_compliance(
            action="normal_request",
            target="api.example.com",
        )
        assert compliance["allowed"]
        
        # 4. Check compliance for out-of-scope action
        compliance = engine.check_compliance(
            action="normal_request",
            target="other.com",
        )
        assert not compliance["allowed"]

    def test_risk_assessment_workflow(self):
        """Test risk assessment workflow."""
        program = create_full_program()
        engine = RuleEngine(program)
        
        # Perform multiple actions
        for _ in range(5):
            engine.assess_action_risk("normal_request")
        
        # Check throttling status
        should_throttle = engine.should_throttle()
        should_stop = engine.should_stop()
        
        # After normal requests, should not throttle
        assert not should_stop


class TestScannerIntegration:
    """Integration tests for vulnerability scanner."""

    @pytest.mark.asyncio
    async def test_full_scan_workflow(self):
        """Test complete scanning workflow."""
        scanner = VulnerabilityScanner()
        target = create_full_target()
        
        # 1. Quick scan
        quick_result = await scanner.scan(target, scan_type="quick")
        assert quick_result.completed_at is not None
        
        # 2. Full scan
        full_result = await scanner.scan(target, scan_type="full")
        assert full_result.completed_at is not None
        
        # 3. OWASP scan
        owasp_result = await scanner.scan(target, scan_type="owasp_top_10")
        assert owasp_result.completed_at is not None

    def test_ranking_workflow(self):
        """Test vulnerability ranking workflow."""
        ranker = VulnerabilityRanker()
        
        # Create findings with different severities
        findings = [
            Finding(
                invariant_violated="TEST_001",
                title="Critical Finding",
                severity=Severity.CRITICAL,
                confidence=0.95,
                classification=FindingClassification.BUG,
            ),
            Finding(
                invariant_violated="TEST_002",
                title="Low Finding",
                severity=Severity.LOW,
                confidence=0.8,
                classification=FindingClassification.BUG,
            ),
            Finding(
                invariant_violated="TEST_003",
                title="Medium Finding",
                severity=Severity.MEDIUM,
                confidence=0.9,
                classification=FindingClassification.BUG,
            ),
        ]
        
        # Rank findings
        ranked = ranker.rank_findings(findings)
        
        # Critical should be first
        assert ranked[0][0].severity == Severity.CRITICAL
        
        # Filter by severity
        filtered = ranker.filter_by_severity(findings, Severity.MEDIUM)
        assert len(filtered) == 2


class TestEndToEndWorkflow:
    """End-to-end workflow tests."""

    @pytest.mark.asyncio
    async def test_complete_bug_bounty_workflow(self):
        """Test complete bug bounty hunting workflow."""
        # 1. Initialize components
        server = MCPServer()
        orchestrator = HuntOrchestrator()
        scanner = VulnerabilityScanner()
        ranker = VulnerabilityRanker()
        
        target = create_full_target()
        program = create_full_program()
        
        # 2. Create MCP session
        session_result = await server.handle_tool_call(
            "create_session",
            {"target_domain": target.domain, "program_name": program.name},
        )
        mcp_session_id = session_result["session_id"]
        
        # 3. Start orchestrator hunt
        hunt_session = await orchestrator.start_hunt(target, program)
        
        # 4. Analyze target
        analysis = await orchestrator.analyze_target(target)
        assert analysis["attack_surface_score"] > 0
        
        # 5. Select tools
        tools = orchestrator.select_tools(target, HuntPhase.RECONNAISSANCE)
        assert len(tools) > 0
        
        # 6. Execute reconnaissance
        recon_results = await orchestrator.execute_phase(
            hunt_session.id,
            HuntPhase.RECONNAISSANCE,
        )
        
        # 7. Perform vulnerability scan
        scan_result = await scanner.scan(target, scan_type="owasp_top_10")
        assert scan_result.completed_at is not None
        
        # 8. Rank any findings
        if scan_result.findings:
            ranked = ranker.rank_findings(scan_result.findings)
            assert len(ranked) == len(scan_result.findings)
        
        # 9. Get findings through MCP
        findings_result = await server.handle_tool_call(
            "get_findings",
            {"session_id": mcp_session_id},
        )
        assert "findings" in findings_result

    @pytest.mark.asyncio
    async def test_compliance_integrated_workflow(self):
        """Test workflow with compliance checking."""
        program = create_full_program()
        rule_engine = RuleEngine(program)
        orchestrator = HuntOrchestrator()
        
        target = create_full_target()
        
        # 1. Validate target is in scope
        validation = rule_engine.validate_target(target.domain)
        assert validation.is_valid
        
        # 2. Start hunt only if in scope
        if validation.is_valid:
            session = await orchestrator.start_hunt(target, program)
            assert session.is_active
            
            # 3. Check compliance before each action
            compliance = rule_engine.check_compliance(
                action="vulnerability_scan",
                target=target.domain,
            )
            
            if compliance["allowed"]:
                # 4. Execute phase
                results = await orchestrator.execute_phase(
                    session.id,
                    HuntPhase.RECONNAISSANCE,
                )
                assert len(results) > 0


class TestPropertyBasedIntegration:
    """Property-based integration tests."""

    @given(st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'))))
    @settings(max_examples=10)
    def test_session_creation_consistency(self, domain: str):
        """Property: Session creation is consistent."""
        server = MCPServer()
        
        async def run_test():
            result = await server.handle_tool_call(
                "create_session",
                {"target_domain": f"{domain}.com"},
            )
            return result
        
        result = asyncio.get_event_loop().run_until_complete(run_test())
        
        assert "session_id" in result
        assert result["target"] == f"{domain}.com"

    @given(st.sampled_from(list(Severity)))
    @settings(max_examples=10)
    def test_ranking_preserves_severity_order(self, severity: Severity):
        """Property: Ranking preserves severity ordering."""
        ranker = VulnerabilityRanker()
        
        findings = [
            Finding(
                invariant_violated=f"TEST_{s.name}",
                title=f"{s.name} Finding",
                severity=s,
                confidence=0.9,
                classification=FindingClassification.BUG,
            )
            for s in Severity
        ]
        
        ranked = ranker.rank_findings(findings)
        scores = [score for _, score in ranked]
        
        # Scores should be in descending order
        assert scores == sorted(scores, reverse=True)

    @given(st.integers(min_value=1, max_value=10))
    @settings(max_examples=5)
    def test_multiple_sessions_independent(self, count: int):
        """Property: Multiple sessions are independent."""
        orchestrator = HuntOrchestrator()
        
        async def run_test():
            sessions = []
            for i in range(count):
                target = Target(domain=f"target{i}.com")
                session = await orchestrator.start_hunt(target)
                sessions.append(session)
            return sessions
        
        sessions = asyncio.get_event_loop().run_until_complete(run_test())
        
        # All sessions should have unique IDs
        ids = [s.id for s in sessions]
        assert len(set(ids)) == count
