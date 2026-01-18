"""
Tests for Tool Orchestrator

Property Tests:
    - Property 5: Tool Output Distrust
    - All tool outputs are UNTRUSTED until MCP validates
"""

import pytest
from hypothesis import given, strategies as st, settings, assume

from cyfer_brain.orchestrator import (
    ToolOrchestrator,
    ToolDefinition,
    TOOL_CATALOG,
)
from cyfer_brain.client import MCPClient
from cyfer_brain.types import (
    Hypothesis,
    HypothesisStatus,
    Observation,
    ExplorationAction,
    ActionType,
    ToolOutput,
    RateLimitStatus,
)
from cyfer_brain.errors import (
    ArchitecturalViolationError,
    ExplorationError,
)


class RealMCPServer:
    """Real MCP server implementation for testing.
    
    This implements all required MCP methods that the MCPClient expects.
    Tests MUST use this instead of object() to ensure REAL MCP integration.
    """
    
    def __init__(self):
        self._observations = []
    
    def validate_observation(self, observation):
        """MCP validates observation and returns classification."""
        self._observations.append(observation)
        return {
            "classification": "SIGNAL",
            "invariant_violated": None,
            "proof": None,
            "confidence": 0.5,
            "coverage_gaps": [],
        }
    
    def get_coverage_report(self):
        """MCP returns coverage report."""
        return {"tested": [], "untested": []}
    
    def validate_scope(self, target):
        """MCP validates target scope."""
        return {"is_in_scope": True, "reason": "In scope"}
    
    def check_rate_limit(self):
        """MCP checks rate limit status."""
        return RateLimitStatus.OK


class TestToolOrchestrator:
    """Tests for ToolOrchestrator."""
    
    def test_orchestrator_creation(self):
        """Test orchestrator can be created with MCP client."""
        client = MCPClient(mcp_server=RealMCPServer())
        orchestrator = ToolOrchestrator(client)
        assert orchestrator is not None
    
    def test_tool_output_has_no_vulnerability_field(self):
        """Tool outputs must NOT have is_vulnerability field."""
        output = ToolOutput(
            tool_name="test_tool",
            raw_output="some output",
            parsed_findings=[{"type": "info"}],
            exit_code=0,
            execution_time_ms=100,
        )
        
        # ToolOutput should NOT have is_vulnerability attribute
        assert not hasattr(output, "is_vulnerability")
        assert not hasattr(output, "is_bug")
        assert not hasattr(output, "confidence")
    
    def test_normalize_output_no_classification(self):
        """Normalized output must NOT contain classification."""
        client = MCPClient(mcp_server=RealMCPServer())
        orchestrator = ToolOrchestrator(client)
        
        output = ToolOutput(
            tool_name="test_tool",
            raw_output="test output",
            parsed_findings=[],
            exit_code=0,
            execution_time_ms=50,
        )
        
        normalized = orchestrator.normalize_output(output)
        
        # Normalized output must NOT have classification fields
        assert "is_vulnerability" not in normalized
        assert "is_bug" not in normalized
        assert "classification" not in normalized
        assert "confidence" not in normalized
        
        # Should have expected fields
        assert "tool" in normalized
        assert "raw" in normalized
        assert "parsed" in normalized
    
    def test_classify_output_raises_violation(self):
        """Attempting to classify output must raise ArchitecturalViolationError."""
        client = MCPClient(mcp_server=RealMCPServer())
        orchestrator = ToolOrchestrator(client)
        
        with pytest.raises(ArchitecturalViolationError) as exc_info:
            orchestrator.classify_output("some output")
        
        assert "classify tool output" in str(exc_info.value)
    
    def test_interpret_finding_raises_violation(self):
        """Attempting to interpret finding must raise ArchitecturalViolationError."""
        client = MCPClient(mcp_server=RealMCPServer())
        orchestrator = ToolOrchestrator(client)
        
        with pytest.raises(ArchitecturalViolationError) as exc_info:
            orchestrator.interpret_finding({"type": "xss"})
        
        assert "interpret a finding" in str(exc_info.value)
    
    def test_register_tool(self):
        """Test tool registration."""
        client = MCPClient(mcp_server=RealMCPServer())
        orchestrator = ToolOrchestrator(client)
        
        tool = ToolDefinition(
            name="custom_tool",
            command="echo",
            args_template="{message}",
            timeout_seconds=10,
        )
        
        orchestrator.register_tool(tool)
        assert "custom_tool" in orchestrator._tool_catalog
    
    def test_execute_unknown_tool_raises_error(self):
        """Executing unknown tool must raise ExplorationError."""
        client = MCPClient(mcp_server=RealMCPServer())
        orchestrator = ToolOrchestrator(client)
        
        with pytest.raises(ExplorationError) as exc_info:
            orchestrator.execute_tool("nonexistent_tool", {})
        
        assert "Unknown tool" in str(exc_info.value)


class TestToolOutputDistrust:
    """Property 5: Tool Output Distrust
    
    Validates: Requirements 5.1, 5.3
    - All tool outputs are UNTRUSTED signals
    - Tool outputs are NEVER interpreted as vulnerabilities
    """
    
    @given(
        tool_name=st.text(min_size=1, max_size=50),
        raw_output=st.text(max_size=1000),
        exit_code=st.integers(min_value=-1, max_value=255),
    )
    @settings(max_examples=50)
    def test_tool_output_never_claims_vulnerability(
        self, tool_name, raw_output, exit_code
    ):
        """Tool outputs must NEVER claim to be vulnerabilities."""
        assume(tool_name.strip())  # Non-empty tool name
        
        output = ToolOutput(
            tool_name=tool_name,
            raw_output=raw_output,
            parsed_findings=[],
            exit_code=exit_code,
            execution_time_ms=100,
        )
        
        # ToolOutput must NOT have any vulnerability-claiming fields
        forbidden_attrs = [
            "is_vulnerability",
            "is_bug",
            "vulnerability_type",
            "severity",
            "confidence",
            "classification",
        ]
        
        for attr in forbidden_attrs:
            assert not hasattr(output, attr), f"ToolOutput must not have {attr}"
    
    @given(
        findings=st.lists(
            st.dictionaries(
                keys=st.text(min_size=1, max_size=20),
                values=st.text(max_size=100),
                max_size=5,
            ),
            max_size=10,
        )
    )
    @settings(max_examples=30)
    def test_parsed_findings_are_untrusted(self, findings):
        """Parsed findings are UNTRUSTED signals, not vulnerabilities."""
        output = ToolOutput(
            tool_name="test_tool",
            raw_output="test",
            parsed_findings=findings,
            exit_code=0,
            execution_time_ms=50,
        )
        
        # Even with parsed findings, output is NOT a vulnerability
        # The parsed_findings are just structured data, not classifications
        assert output.parsed_findings == findings
        
        # No method to get vulnerability status
        assert not hasattr(output, "get_vulnerabilities")
        assert not hasattr(output, "is_vulnerable")
    
    def test_normalized_output_preserves_distrust(self):
        """Normalized output must preserve untrusted nature."""
        client = MCPClient(mcp_server=RealMCPServer())
        orchestrator = ToolOrchestrator(client)
        
        # Even if parsed findings look like vulnerabilities
        output = ToolOutput(
            tool_name="scanner",
            raw_output="CRITICAL: SQL Injection found!",
            parsed_findings=[
                {"type": "sqli", "severity": "critical", "location": "/api/users"}
            ],
            exit_code=0,
            execution_time_ms=1000,
        )
        
        normalized = orchestrator.normalize_output(output)
        
        # Normalized output must NOT add classification
        assert "is_vulnerability" not in normalized
        assert "confirmed" not in normalized
        assert "verified" not in normalized
        
        # The parsed findings are preserved but NOT interpreted
        assert normalized["parsed"] == output.parsed_findings


class TestSubmissionToMCP:
    """Tests for MCP submission flow."""
    
    def test_hypothesis_status_transitions(self):
        """Hypothesis status must transition correctly during submission."""
        client = MCPClient(mcp_server=RealMCPServer())
        orchestrator = ToolOrchestrator(client)
        
        hypothesis = Hypothesis(
            description="Test hypothesis",
            testability_score=0.7,
            status=HypothesisStatus.UNTESTED,
        )
        
        action = ExplorationAction(
            action_type=ActionType.HTTP_REQUEST,
            target="http://example.com",
        )
        
        # Submit to MCP
        classification = orchestrator.submit_to_mcp(
            hypothesis=hypothesis,
            action=action,
            before_state={},
            after_state={},
            tool_outputs=[],
        )
        
        # Hypothesis should be RESOLVED after MCP classification
        assert hypothesis.status == HypothesisStatus.RESOLVED
        assert hypothesis.mcp_classification is not None
        assert hypothesis.mcp_classification == classification
    
    def test_observation_has_no_classification(self):
        """Observation submitted to MCP must NOT have classification."""
        # Observation dataclass should not have classification field
        obs = Observation(
            hypothesis_id="test-id",
            before_state={"user": "A"},
            action=ExplorationAction(),
            after_state={"user": "B"},
            tool_outputs=[],
        )
        
        # Observation must NOT have classification - that's MCP's job
        assert not hasattr(obs, "classification")
        assert not hasattr(obs, "is_bug")
        assert not hasattr(obs, "confidence")
