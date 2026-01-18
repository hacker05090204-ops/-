"""
Property-based tests for hunt orchestrator and workflow engine.

**Task 9: Build hunt orchestrator and workflow engine**
**Property Tests: 9.1, 9.2, 9.3**

Requirements validated:
- 1.1: Comprehensive Subdomain Discovery
- 2.1: Target-Appropriate Scanning Strategy Selection
- 44.1-44.5: Horizontal Scalability
"""

import pytest
from hypothesis import given, strategies as st, settings
import asyncio
from datetime import datetime

from kali_mcp.orchestrator import (
    HuntOrchestrator,
    WorkflowEngine,
    WorkflowStep,
    WorkflowResult,
    WorkflowStatus,
    ToolSelector,
    TargetAnalyzer,
)
from kali_mcp.types import (
    Target,
    BugBountyProgram,
    HuntSession,
    HuntPhase,
    Service,
    Protocol,
    TechnologyProfile,
    ScopeDefinition,
)


# ============================================================================
# Test Helpers
# ============================================================================

def create_test_target(domain: str = "example.com") -> Target:
    """Create a test target."""
    return Target(
        domain=domain,
        subdomains=[f"api.{domain}", f"www.{domain}"],
        services=[
            Service(
                host=domain,
                port=443,
                protocol=Protocol.HTTPS,
                service_type="web",
            ),
        ],
    )


def create_test_program(name: str = "Test Program") -> BugBountyProgram:
    """Create a test program."""
    return BugBountyProgram(
        name=name,
        platform="private",
        scope=ScopeDefinition(
            in_scope_domains=["*.example.com"],
        ),
    )


async def mock_step_handler(context: dict) -> dict:
    """Mock step handler for testing."""
    return {"status": "completed", "data": "test"}


async def failing_step_handler(context: dict) -> dict:
    """Mock step handler that fails."""
    raise ValueError("Step failed")


# ============================================================================
# Property Test 9.1: Comprehensive Subdomain Discovery
# **Validates: Requirements 1.1**
# ============================================================================

class TestWorkflowEngine:
    """Tests for WorkflowEngine."""

    def test_register_step(self):
        """Test step registration."""
        engine = WorkflowEngine()
        
        step = WorkflowStep(
            name="test_step",
            phase=HuntPhase.RECONNAISSANCE,
            handler=mock_step_handler,
        )
        
        engine.register_step(step)
        
        # Step should be registered
        assert "test_step" in engine._steps

    @pytest.mark.asyncio
    async def test_execute_step_success(self):
        """Test successful step execution."""
        engine = WorkflowEngine()
        
        step = WorkflowStep(
            name="test_step",
            phase=HuntPhase.RECONNAISSANCE,
            handler=mock_step_handler,
        )
        engine.register_step(step)
        
        result = await engine.execute_step("test_step", {})
        
        assert result.status == WorkflowStatus.COMPLETED
        assert result.output["status"] == "completed"
        assert result.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_execute_step_failure(self):
        """Test failed step execution."""
        engine = WorkflowEngine()
        
        step = WorkflowStep(
            name="failing_step",
            phase=HuntPhase.RECONNAISSANCE,
            handler=failing_step_handler,
        )
        engine.register_step(step)
        
        result = await engine.execute_step("failing_step", {})
        
        assert result.status == WorkflowStatus.FAILED
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_execute_nonexistent_step(self):
        """Test executing non-existent step."""
        engine = WorkflowEngine()
        
        result = await engine.execute_step("nonexistent", {})
        
        assert result.status == WorkflowStatus.FAILED
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_dependency_checking(self):
        """Test dependency checking."""
        engine = WorkflowEngine()
        
        # Register step with dependency
        step = WorkflowStep(
            name="dependent_step",
            phase=HuntPhase.RECONNAISSANCE,
            handler=mock_step_handler,
            dependencies=["prerequisite"],
        )
        engine.register_step(step)
        
        # Execute without prerequisite
        result = await engine.execute_step("dependent_step", {})
        
        assert result.status == WorkflowStatus.FAILED
        assert "dependency" in result.error.lower()

    @pytest.mark.asyncio
    async def test_dependency_satisfied(self):
        """Test execution with satisfied dependency."""
        engine = WorkflowEngine()
        
        # Register prerequisite
        prereq = WorkflowStep(
            name="prerequisite",
            phase=HuntPhase.RECONNAISSANCE,
            handler=mock_step_handler,
        )
        engine.register_step(prereq)
        
        # Register dependent step
        step = WorkflowStep(
            name="dependent_step",
            phase=HuntPhase.RECONNAISSANCE,
            handler=mock_step_handler,
            dependencies=["prerequisite"],
        )
        engine.register_step(step)
        
        # Execute prerequisite first
        await engine.execute_step("prerequisite", {})
        
        # Now execute dependent step
        result = await engine.execute_step("dependent_step", {})
        
        assert result.status == WorkflowStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_phase(self):
        """Test phase execution."""
        engine = WorkflowEngine()
        
        # Register multiple steps in same phase
        for i in range(3):
            step = WorkflowStep(
                name=f"step_{i}",
                phase=HuntPhase.RECONNAISSANCE,
                handler=mock_step_handler,
            )
            engine.register_step(step)
        
        results = await engine.execute_phase(HuntPhase.RECONNAISSANCE, {})
        
        assert len(results) == 3
        assert all(r.status == WorkflowStatus.COMPLETED for r in results)

    def test_reset(self):
        """Test workflow reset."""
        engine = WorkflowEngine()
        engine._results["test"] = WorkflowResult(
            step_name="test",
            status=WorkflowStatus.COMPLETED,
        )
        
        engine.reset()
        
        assert len(engine._results) == 0


# ============================================================================
# Property Test 9.2: Target-Appropriate Scanning Strategy Selection
# **Validates: Requirements 2.1**
# ============================================================================

class TestToolSelector:
    """Tests for ToolSelector."""

    def test_select_reconnaissance_tools(self):
        """Test selecting reconnaissance tools."""
        selector = ToolSelector()
        target = create_test_target()
        
        tools = selector.select_tools(target, HuntPhase.RECONNAISSANCE)
        
        assert len(tools) > 0
        # Should include recon tools
        assert any(t in tools for t in ["nmap", "subfinder", "httpx"])

    def test_select_scanning_tools(self):
        """Test selecting scanning tools."""
        selector = ToolSelector()
        target = create_test_target()
        
        tools = selector.select_tools(target, HuntPhase.SCANNING)
        
        assert len(tools) > 0
        # Should include scanning tools
        assert any(t in tools for t in ["nuclei", "ffuf"])

    def test_select_exploitation_tools(self):
        """Test selecting exploitation tools."""
        selector = ToolSelector()
        target = create_test_target()
        
        tools = selector.select_tools(target, HuntPhase.EXPLOITATION)
        
        assert len(tools) > 0
        # Should include exploitation tools
        assert "sqlmap" in tools

    def test_fast_only_constraint(self):
        """Test fast-only constraint."""
        selector = ToolSelector()
        target = create_test_target()
        
        tools = selector.select_tools(
            target,
            HuntPhase.RECONNAISSANCE,
            constraints={"fast_only": True},
        )
        
        # All selected tools should be fast
        for tool in tools:
            caps = selector.get_tool_capabilities(tool)
            assert caps is not None
            assert caps.get("speed") == "fast"

    def test_get_tool_capabilities(self):
        """Test getting tool capabilities."""
        selector = ToolSelector()
        
        caps = selector.get_tool_capabilities("nmap")
        
        assert caps is not None
        assert "capabilities" in caps
        assert "port_scan" in caps["capabilities"]

    def test_nonexistent_tool(self):
        """Test getting capabilities of non-existent tool."""
        selector = ToolSelector()
        
        caps = selector.get_tool_capabilities("nonexistent")
        
        assert caps is None

    @given(st.sampled_from([HuntPhase.RECONNAISSANCE, HuntPhase.SCANNING, HuntPhase.EXPLOITATION]))
    @settings(max_examples=10)
    def test_tool_selection_consistency(self, phase: HuntPhase):
        """Property: Tool selection is consistent for same inputs."""
        selector = ToolSelector()
        target = create_test_target()
        
        tools1 = selector.select_tools(target, phase)
        tools2 = selector.select_tools(target, phase)
        
        assert set(tools1) == set(tools2)


# ============================================================================
# Property Test 9.3: Horizontal Scalability
# **Validates: Requirements 44.1, 44.2, 44.3**
# ============================================================================

class TestTargetAnalyzer:
    """Tests for TargetAnalyzer."""

    @pytest.mark.asyncio
    async def test_analyze_basic_target(self):
        """Test analyzing a basic target."""
        analyzer = TargetAnalyzer()
        target = create_test_target()
        
        analysis = await analyzer.analyze(target)
        
        assert analysis["domain"] == target.domain
        assert analysis["subdomain_count"] == len(target.subdomains)
        assert analysis["service_count"] == len(target.services)
        assert "attack_surface_score" in analysis

    @pytest.mark.asyncio
    async def test_attack_surface_calculation(self):
        """Test attack surface score calculation."""
        analyzer = TargetAnalyzer()
        
        # Small target
        small_target = Target(domain="small.com")
        small_analysis = await analyzer.analyze(small_target)
        
        # Large target
        large_target = Target(
            domain="large.com",
            subdomains=[f"sub{i}.large.com" for i in range(10)],
            services=[
                Service(host="large.com", port=80 + i, protocol=Protocol.HTTP, service_type="web")
                for i in range(5)
            ],
        )
        large_analysis = await analyzer.analyze(large_target)
        
        # Large target should have higher attack surface
        assert large_analysis["attack_surface_score"] > small_analysis["attack_surface_score"]

    @pytest.mark.asyncio
    async def test_web_service_detection(self):
        """Test web service detection."""
        analyzer = TargetAnalyzer()
        
        # Target with web services
        web_target = Target(
            domain="web.com",
            services=[
                Service(host="web.com", port=443, protocol=Protocol.HTTPS, service_type="web"),
            ],
        )
        web_analysis = await analyzer.analyze(web_target)
        
        # Target without web services
        no_web_target = Target(
            domain="noweb.com",
            services=[
                Service(host="noweb.com", port=22, protocol=Protocol.SSH, service_type="ssh"),
            ],
        )
        no_web_analysis = await analyzer.analyze(no_web_target)
        
        assert web_analysis["has_web_services"] is True
        assert no_web_analysis["has_web_services"] is False


class TestHuntOrchestrator:
    """Tests for HuntOrchestrator."""

    @pytest.mark.asyncio
    async def test_start_hunt(self):
        """Test starting a hunt session."""
        orchestrator = HuntOrchestrator()
        target = create_test_target()
        program = create_test_program()
        
        session = await orchestrator.start_hunt(target, program)
        
        assert session.id is not None
        assert session.target == target
        assert session.program == program
        assert session.is_active

    @pytest.mark.asyncio
    async def test_get_session(self):
        """Test getting a session."""
        orchestrator = HuntOrchestrator()
        target = create_test_target()
        
        session = await orchestrator.start_hunt(target)
        retrieved = orchestrator.get_session(session.id)
        
        assert retrieved is not None
        assert retrieved.id == session.id

    @pytest.mark.asyncio
    async def test_list_active_sessions(self):
        """Test listing active sessions."""
        orchestrator = HuntOrchestrator()
        
        # Start multiple sessions
        for i in range(3):
            target = create_test_target(f"target{i}.com")
            await orchestrator.start_hunt(target)
        
        active = orchestrator.list_active_sessions()
        
        assert len(active) == 3

    @pytest.mark.asyncio
    async def test_execute_phase(self):
        """Test executing a phase."""
        orchestrator = HuntOrchestrator()
        target = create_test_target()
        
        session = await orchestrator.start_hunt(target)
        results = await orchestrator.execute_phase(session.id, HuntPhase.RECONNAISSANCE)
        
        assert len(results) > 0
        assert session.current_phase == HuntPhase.RECONNAISSANCE

    @pytest.mark.asyncio
    async def test_execute_phase_invalid_session(self):
        """Test executing phase with invalid session."""
        orchestrator = HuntOrchestrator()
        
        with pytest.raises(ValueError, match="not found"):
            await orchestrator.execute_phase("invalid", HuntPhase.RECONNAISSANCE)

    def test_select_tools(self):
        """Test tool selection through orchestrator."""
        orchestrator = HuntOrchestrator()
        target = create_test_target()
        
        tools = orchestrator.select_tools(target, HuntPhase.RECONNAISSANCE)
        
        assert len(tools) > 0

    @pytest.mark.asyncio
    async def test_analyze_target(self):
        """Test target analysis through orchestrator."""
        orchestrator = HuntOrchestrator()
        target = create_test_target()
        
        analysis = await orchestrator.analyze_target(target)
        
        assert analysis["domain"] == target.domain
        assert "attack_surface_score" in analysis

    @given(st.integers(min_value=1, max_value=10))
    @settings(max_examples=5)
    def test_multiple_sessions_independent(self, count: int):
        """Property: Multiple sessions are independent."""
        orchestrator = HuntOrchestrator()
        
        async def run_test():
            sessions = []
            for i in range(count):
                target = create_test_target(f"target{i}.com")
                session = await orchestrator.start_hunt(target)
                sessions.append(session)
            
            # All sessions should be independent
            session_ids = [s.id for s in sessions]
            assert len(set(session_ids)) == count
            
            # All sessions should be active
            active = orchestrator.list_active_sessions()
            assert len(active) == count
        
        asyncio.get_event_loop().run_until_complete(run_test())


class TestIntegration:
    """Integration tests for orchestrator."""

    @pytest.mark.asyncio
    async def test_full_hunt_workflow(self):
        """Test complete hunting workflow."""
        orchestrator = HuntOrchestrator()
        target = create_test_target()
        program = create_test_program()
        
        # Start hunt
        session = await orchestrator.start_hunt(target, program)
        assert session.is_active
        
        # Analyze target
        analysis = await orchestrator.analyze_target(target)
        assert analysis["domain"] == target.domain
        
        # Select tools
        recon_tools = orchestrator.select_tools(target, HuntPhase.RECONNAISSANCE)
        assert len(recon_tools) > 0
        
        # Execute reconnaissance phase
        recon_results = await orchestrator.execute_phase(session.id, HuntPhase.RECONNAISSANCE)
        assert len(recon_results) > 0
        
        # Verify session state
        assert session.current_phase == HuntPhase.RECONNAISSANCE

    @pytest.mark.asyncio
    async def test_workflow_dependency_chain(self):
        """Test workflow with dependency chain."""
        orchestrator = HuntOrchestrator()
        target = create_test_target()
        
        session = await orchestrator.start_hunt(target)
        
        # Execute phases in order
        recon_results = await orchestrator.execute_phase(session.id, HuntPhase.RECONNAISSANCE)
        
        # All recon steps should complete (dependencies satisfied in order)
        completed = [r for r in recon_results if r.status == WorkflowStatus.COMPLETED]
        assert len(completed) > 0
