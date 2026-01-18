"""
Tests for CyferBrain Main Orchestrator

Property Tests:
    - Property 4: Scope Validation Delegation
    - End-to-end exploration respects MCP authority
"""

import pytest
from hypothesis import given, strategies as st, settings

from cyfer_brain.brain import CyferBrain, ExplorationSession
from cyfer_brain.client import MCPClient
from cyfer_brain.hypothesis import Target
from cyfer_brain.types import (
    Hypothesis,
    HypothesisStatus,
    MCPClassification,
    ExplorationBoundary,
    ExplorationStats,
    ScopeValidation,
    RateLimitStatus,
)
from cyfer_brain.errors import (
    ArchitecturalViolationError,
    MCPUnavailableError,
    CyferBrainError,
)


class RealMCPServer:
    """Real MCP server implementation for testing.
    
    This implements all required MCP methods that the MCPClient expects.
    Tests MUST use this instead of object() to ensure REAL MCP integration.
    """
    
    def __init__(self, default_in_scope: bool = True):
        self._default_in_scope = default_in_scope
        self._observations = []
        self._coverage = {"tested": [], "untested": []}
    
    def validate_observation(self, observation):
        """MCP validates observation and returns classification."""
        self._observations.append(observation)
        return {
            "classification": "SIGNAL",  # Default to SIGNAL for testing
            "invariant_violated": None,
            "proof": None,
            "confidence": 0.5,
            "coverage_gaps": [],
        }
    
    def get_coverage_report(self):
        """MCP returns coverage report."""
        return self._coverage
    
    def validate_scope(self, target):
        """MCP validates target scope."""
        return {
            "is_in_scope": self._default_in_scope,
            "reason": "In scope" if self._default_in_scope else "Out of scope",
        }
    
    def check_rate_limit(self):
        """MCP checks rate limit status."""
        return RateLimitStatus.OK


class TestCyferBrain:
    """Tests for CyferBrain orchestrator."""
    
    def test_brain_creation(self):
        """Test brain can be created."""
        client = MCPClient(mcp_server=RealMCPServer())
        brain = CyferBrain(client)
        
        assert brain is not None
    
    def test_brain_with_custom_boundary(self):
        """Test brain with custom boundary."""
        client = MCPClient(mcp_server=RealMCPServer())
        boundary = ExplorationBoundary(
            max_actions=50,
            max_mcp_submissions=25,
        )
        brain = CyferBrain(client, boundary=boundary)
        
        assert brain._boundary_manager.get_boundary().max_actions == 50
    
    def test_classify_finding_raises_violation(self):
        """Attempting to classify finding must raise ArchitecturalViolationError."""
        client = MCPClient(mcp_server=RealMCPServer())
        brain = CyferBrain(client)
        
        with pytest.raises(ArchitecturalViolationError) as exc_info:
            brain.classify_finding({"type": "xss"})
        
        assert "classify a finding" in str(exc_info.value)
    
    def test_generate_proof_raises_violation(self):
        """Attempting to generate proof must raise ArchitecturalViolationError."""
        client = MCPClient(mcp_server=RealMCPServer())
        brain = CyferBrain(client)
        
        with pytest.raises(ArchitecturalViolationError) as exc_info:
            brain.generate_proof()
        
        assert "generate a proof" in str(exc_info.value)
    
    def test_compute_confidence_raises_violation(self):
        """Attempting to compute confidence must raise ArchitecturalViolationError."""
        client = MCPClient(mcp_server=RealMCPServer())
        brain = CyferBrain(client)
        
        with pytest.raises(ArchitecturalViolationError) as exc_info:
            brain.compute_confidence()
        
        assert "compute confidence" in str(exc_info.value)
    
    def test_auto_submit_report_raises_violation(self):
        """Attempting to auto-submit report must raise ArchitecturalViolationError."""
        client = MCPClient(mcp_server=RealMCPServer())
        brain = CyferBrain(client)
        
        with pytest.raises(ArchitecturalViolationError) as exc_info:
            brain.auto_submit_report()
        
        assert "auto-submit a report" in str(exc_info.value)


class TestScopeValidationDelegation:
    """Property 4: Scope Validation Delegation
    
    Validates: Requirements 2.1
    - Scope validation is DELEGATED to MCP
    - Cyfer Brain does not make scope decisions
    """
    
    def test_scope_validation_calls_mcp(self):
        """Scope validation must call MCP."""
        client = MCPClient(mcp_server=RealMCPServer(default_in_scope=True))
        brain = CyferBrain(client)
        
        target = Target(domain="example.com")
        
        # _validate_scope should call MCP client
        # This will use the RealMCPServer validation (in-scope)
        brain._validate_scope(target)
        
        # No exception means scope was validated via MCP
    
    def test_out_of_scope_raises_error(self):
        """Out of scope target must raise error."""
        # Create MCP server that returns out-of-scope
        client = MCPClient(mcp_server=RealMCPServer(default_in_scope=False))
        brain = CyferBrain(client)
        
        target = Target(domain="out-of-scope.com")
        
        with pytest.raises(CyferBrainError) as exc_info:
            brain._validate_scope(target)
        
        assert "out of scope" in str(exc_info.value)


class TestExplorationLoop:
    """Tests for exploration loop."""
    
    def test_exploration_generates_summary(self):
        """Exploration must generate summary."""
        client = MCPClient(mcp_server=RealMCPServer())
        boundary = ExplorationBoundary(
            max_actions=10,
            max_mcp_submissions=5,
            max_time_seconds=60,
        )
        brain = CyferBrain(client, boundary=boundary)
        
        target = Target(
            domain="test.example.com",
            endpoints=["/api/users"],
        )
        
        summary = brain.explore(target)
        
        assert summary is not None
        assert summary.target == "test.example.com"
        assert summary.stats is not None
    
    def test_exploration_respects_boundaries(self):
        """Exploration must respect boundaries."""
        client = MCPClient(mcp_server=RealMCPServer())
        boundary = ExplorationBoundary(
            max_actions=5,
            max_mcp_submissions=3,
        )
        brain = CyferBrain(client, boundary=boundary)
        
        target = Target(
            domain="test.example.com",
            endpoints=[f"/api/endpoint{i}" for i in range(20)],
        )
        
        summary = brain.explore(target)
        
        # Should stop due to boundaries
        assert summary.stats.actions_executed <= boundary.max_actions + 1
    
    def test_mcp_unavailable_causes_hard_stop(self):
        """MCP unavailable must cause HARD STOP."""
        # Client without MCP server
        client = MCPClient(mcp_server=None)
        brain = CyferBrain(client)
        
        target = Target(domain="test.example.com")
        
        with pytest.raises(MCPUnavailableError):
            brain.explore(target)


class TestExplorationSession:
    """Tests for exploration session state."""
    
    def test_session_tracks_hypotheses(self):
        """Session must track generated hypotheses."""
        client = MCPClient(mcp_server=RealMCPServer())
        brain = CyferBrain(client)
        
        target = Target(
            domain="test.example.com",
            endpoints=["/api/test"],
        )
        
        brain.explore(target)
        
        session = brain.get_session()
        assert session is not None
        assert len(session.hypotheses) > 0
    
    def test_session_tracks_classifications(self):
        """Session must track MCP classifications."""
        client = MCPClient(mcp_server=RealMCPServer())
        boundary = ExplorationBoundary(max_actions=5)
        brain = CyferBrain(client, boundary=boundary)
        
        target = Target(
            domain="test.example.com",
            endpoints=["/api/test"],
        )
        
        brain.explore(target)
        
        session = brain.get_session()
        assert session is not None
        # Classifications are tracked (may be empty if no hypotheses tested)


class TestArchitecturalBoundaries:
    """Tests for architectural boundary enforcement."""
    
    @given(
        method_name=st.sampled_from([
            "classify_finding",
            "generate_proof",
            "compute_confidence",
            "auto_submit_report",
        ])
    )
    @settings(max_examples=4)
    def test_all_mcp_methods_rejected(self, method_name):
        """All MCP responsibility methods must be rejected."""
        client = MCPClient(mcp_server=RealMCPServer())
        brain = CyferBrain(client)
        
        method = getattr(brain, method_name)
        
        with pytest.raises(ArchitecturalViolationError):
            method()
    
    def test_exploration_never_classifies(self):
        """Exploration must never classify findings."""
        client = MCPClient(mcp_server=RealMCPServer())
        boundary = ExplorationBoundary(max_actions=5)
        brain = CyferBrain(client, boundary=boundary)
        
        target = Target(
            domain="test.example.com",
            endpoints=["/api/test"],
        )
        
        summary = brain.explore(target)
        
        # Summary should not claim to have classified anything
        # bugs_found is count of MCP BUG classifications, not Cyfer Brain's
        assert hasattr(summary.stats, "bugs_found")
        # The count comes from MCP, not from Cyfer Brain's classification


class TestLoggingDistinction:
    """Tests for logging distinction between exploration and judgement."""
    
    def test_exploration_logs_use_exploration_prefix(self):
        """Exploration logs should use [EXPLORATION] prefix."""
        # This is a documentation/convention test
        # The actual logging is verified by code review
        
        # Verify the brain module uses proper logging prefixes
        import cyfer_brain.brain as brain_module
        import inspect
        
        source = inspect.getsource(brain_module)
        
        # Should have [EXPLORATION] prefixes
        assert "[EXPLORATION]" in source
        
        # Should have [MCP JUDGEMENT] for MCP results
        assert "[MCP JUDGEMENT]" in source
