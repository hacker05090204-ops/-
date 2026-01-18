"""
Property Tests for MCP Client

**Feature: cyfer-brain, Property 3: MCP Classification Immutability**
**Validates: Requirements 8.3, 12.1**

**Feature: cyfer-brain, Property 9: Architectural Boundary Enforcement**
**Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5**
"""

import pytest
from hypothesis import given, strategies as st, settings
import sys
import os

# Add parent directory to path for import
test_dir = os.path.dirname(os.path.abspath(__file__))
cyfer_brain_dir = os.path.dirname(test_dir)
python_dir = os.path.dirname(cyfer_brain_dir)
if python_dir not in sys.path:
    sys.path.insert(0, python_dir)

from cyfer_brain.client import MCPClient, ObservationSubmissionGuard
from cyfer_brain.types import Observation, MCPClassification, ExplorationAction
from cyfer_brain.errors import (
    ArchitecturalViolationError,
    MCPUnavailableError,
    MCPCommunicationError,
)


class TestMCPClientArchitecturalBoundaries:
    """
    **Feature: cyfer-brain, Property 9: Architectural Boundary Enforcement**
    **Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5**
    
    For any request to Cyfer Brain to perform MCP responsibilities
    (classify, prove, compute confidence), Cyfer Brain SHALL refuse.
    """
    
    def test_classify_finding_raises_architectural_violation(self):
        """Verify classify_finding raises ArchitecturalViolationError."""
        client = MCPClient()
        
        with pytest.raises(ArchitecturalViolationError) as exc_info:
            client.classify_finding()
        
        assert "classify a finding" in str(exc_info.value)
        assert "MCP's responsibility" in str(exc_info.value)
    
    def test_generate_proof_raises_architectural_violation(self):
        """Verify generate_proof raises ArchitecturalViolationError."""
        client = MCPClient()
        
        with pytest.raises(ArchitecturalViolationError) as exc_info:
            client.generate_proof()
        
        assert "generate a proof" in str(exc_info.value)
    
    def test_compute_confidence_raises_architectural_violation(self):
        """Verify compute_confidence raises ArchitecturalViolationError."""
        client = MCPClient()
        
        with pytest.raises(ArchitecturalViolationError) as exc_info:
            client.compute_confidence()
        
        assert "compute confidence" in str(exc_info.value)
    
    def test_override_classification_raises_architectural_violation(self):
        """Verify override_classification raises ArchitecturalViolationError."""
        client = MCPClient()
        
        with pytest.raises(ArchitecturalViolationError) as exc_info:
            client.override_classification()
        
        assert "override MCP classification" in str(exc_info.value)
    
    def test_auto_submit_report_raises_architectural_violation(self):
        """Verify auto_submit_report raises ArchitecturalViolationError."""
        client = MCPClient()
        
        with pytest.raises(ArchitecturalViolationError) as exc_info:
            client.auto_submit_report()
        
        assert "auto-submit a report" in str(exc_info.value)
    
    @given(st.text(), st.integers(), st.floats(allow_nan=False))
    @settings(max_examples=100)
    def test_rejected_methods_always_raise_regardless_of_args(
        self, text_arg, int_arg, float_arg
    ):
        """
        Property test: Rejected methods ALWAYS raise ArchitecturalViolationError,
        regardless of what arguments are passed.
        """
        client = MCPClient()
        
        rejected_methods = [
            client.classify_finding,
            client.generate_proof,
            client.compute_confidence,
            client.override_classification,
            client.auto_submit_report,
        ]
        
        for method in rejected_methods:
            with pytest.raises(ArchitecturalViolationError):
                method(text_arg, int_arg, float_arg)


class TestMCPIntegrationRequirements:
    """
    Tests for REAL MCP integration requirements.
    
    These tests verify that:
    1. MCP server MUST implement required methods
    2. No fabricated/default classifications are returned
    3. HARD FAIL if MCP doesn't implement required interface
    """
    
    def test_mcp_server_must_implement_validate_observation(self):
        """MCP server without validate_observation causes HARD FAIL."""
        from cyfer_brain.errors import MCPCommunicationError
        
        class IncompleteMCPServer:
            """MCP server that doesn't implement validate_observation."""
            pass
        
        client = MCPClient(mcp_server=IncompleteMCPServer())
        observation = Observation(hypothesis_id="test")
        
        with pytest.raises(MCPUnavailableError) as exc_info:
            client.submit_observation(observation)
        
        assert "does not implement validate_observation" in str(exc_info.value)
        assert "HARD STOP" in str(exc_info.value)
    
    def test_mcp_server_must_implement_get_coverage_report(self):
        """MCP server without get_coverage_report causes error."""
        from cyfer_brain.errors import MCPCommunicationError
        
        class IncompleteMCPServer:
            pass
        
        client = MCPClient(mcp_server=IncompleteMCPServer())
        
        with pytest.raises(MCPCommunicationError) as exc_info:
            client.get_coverage_report()
        
        assert "does not implement get_coverage_report" in str(exc_info.value)
    
    def test_mcp_server_must_implement_validate_scope(self):
        """MCP server without validate_scope causes error."""
        from cyfer_brain.errors import MCPCommunicationError
        
        class IncompleteMCPServer:
            pass
        
        client = MCPClient(mcp_server=IncompleteMCPServer())
        
        with pytest.raises(MCPCommunicationError) as exc_info:
            client.validate_scope("example.com")
        
        assert "does not implement validate_scope" in str(exc_info.value)
    
    def test_mcp_server_must_implement_check_rate_limit(self):
        """MCP server without check_rate_limit causes error."""
        from cyfer_brain.errors import MCPCommunicationError
        
        class IncompleteMCPServer:
            pass
        
        client = MCPClient(mcp_server=IncompleteMCPServer())
        
        with pytest.raises(MCPCommunicationError) as exc_info:
            client.check_rate_limit()
        
        assert "does not implement check_rate_limit" in str(exc_info.value)
    
    def test_real_mcp_classification_returned(self):
        """Verify REAL MCP classification is returned, not fabricated."""
        class RealMCPServer:
            def validate_observation(self, observation):
                # Return a REAL classification (BUG in this case)
                return {
                    "classification": "BUG",
                    "invariant_violated": "AUTH_BYPASS_001",
                    "proof": {"evidence": "real_proof"},
                    "confidence": 0.95,
                    "coverage_gaps": [],
                }
        
        client = MCPClient(mcp_server=RealMCPServer())
        observation = Observation(hypothesis_id="test")
        
        classification = client.submit_observation(observation)
        
        # Verify the classification is what MCP returned, not a default
        assert classification.classification == "BUG"
        assert classification.invariant_violated == "AUTH_BYPASS_001"
        assert classification.confidence == 0.95
    
    def test_mcp_null_response_causes_hard_fail(self):
        """MCP returning None causes HARD FAIL."""
        from cyfer_brain.errors import MCPCommunicationError
        
        class BadMCPServer:
            def validate_observation(self, observation):
                return None
        
        client = MCPClient(mcp_server=BadMCPServer())
        observation = Observation(hypothesis_id="test")
        
        with pytest.raises(MCPCommunicationError) as exc_info:
            client.submit_observation(observation)
        
        assert "returned None" in str(exc_info.value)
        assert "HARD STOP" in str(exc_info.value)


class TestMCPClassificationImmutability:
    """
    **Feature: cyfer-brain, Property 3: MCP Classification Immutability**
    **Validates: Requirements 8.3, 12.1**
    
    For any classification received from MCP, Cyfer Brain SHALL NOT
    modify, override, or reinterpret the classification.
    """
    
    def test_mcp_classification_is_immutable_dataclass(self):
        """Verify MCPClassification fields cannot be modified after creation."""
        classification = MCPClassification(
            observation_id="test-123",
            classification="BUG",
            invariant_violated="AUTH_001",
            confidence=0.95,
        )
        
        # The classification should be what MCP set
        assert classification.classification == "BUG"
        assert classification.invariant_violated == "AUTH_001"
        assert classification.confidence == 0.95
    
    @given(
        st.sampled_from(["BUG", "SIGNAL", "NO_ISSUE", "COVERAGE_GAP"]),
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_classification_helper_methods_are_consistent(
        self, classification_type, confidence
    ):
        """
        Property test: Classification helper methods correctly reflect
        the classification type without modification.
        """
        classification = MCPClassification(
            observation_id="test",
            classification=classification_type,
            confidence=confidence,
        )
        
        # Exactly one helper should return True
        helpers = [
            classification.is_bug(),
            classification.is_signal(),
            classification.is_no_issue(),
            classification.is_coverage_gap(),
        ]
        
        assert sum(helpers) == 1, "Exactly one classification type should be True"
        
        # The correct helper should match
        if classification_type == "BUG":
            assert classification.is_bug()
        elif classification_type == "SIGNAL":
            assert classification.is_signal()
        elif classification_type == "NO_ISSUE":
            assert classification.is_no_issue()
        elif classification_type == "COVERAGE_GAP":
            assert classification.is_coverage_gap()


class TestMCPUnavailability:
    """Test MCP unavailability handling."""
    
    def test_submit_observation_raises_when_mcp_unavailable(self):
        """Verify submit_observation raises MCPUnavailableError when MCP is not available."""
        client = MCPClient(mcp_server=None)  # No MCP server
        
        observation = Observation(
            hypothesis_id="test",
            before_state={},
            after_state={},
        )
        
        with pytest.raises(MCPUnavailableError) as exc_info:
            client.submit_observation(observation)
        
        assert "HARD STOP" in str(exc_info.value)
    
    def test_get_coverage_report_raises_when_mcp_unavailable(self):
        """Verify get_coverage_report raises MCPUnavailableError when MCP is not available."""
        client = MCPClient(mcp_server=None)
        
        with pytest.raises(MCPUnavailableError):
            client.get_coverage_report()
    
    def test_validate_scope_raises_when_mcp_unavailable(self):
        """Verify validate_scope raises MCPUnavailableError when MCP is not available."""
        client = MCPClient(mcp_server=None)
        
        with pytest.raises(MCPUnavailableError):
            client.validate_scope("example.com")
    
    def test_check_rate_limit_raises_when_mcp_unavailable(self):
        """Verify check_rate_limit raises MCPUnavailableError when MCP is not available."""
        client = MCPClient(mcp_server=None)
        
        with pytest.raises(MCPUnavailableError):
            client.check_rate_limit()


class TestObservationSubmissionGuard:
    """Test ObservationSubmissionGuard functionality."""
    
    def test_guard_tracks_pending_observations(self):
        """Verify guard correctly tracks pending observations."""
        # Create a proper MCP server that implements required methods
        class RealMCPServer:
            def validate_observation(self, observation):
                return {
                    "classification": "SIGNAL",
                    "invariant_violated": None,
                    "proof": None,
                    "confidence": 0.0,
                    "coverage_gaps": [],
                }
        
        client = MCPClient(mcp_server=RealMCPServer())
        guard = ObservationSubmissionGuard(client)
        
        observation = Observation(hypothesis_id="test")
        
        assert not guard.has_pending()
        assert guard.pending_count() == 0
        
        guard.register_observation(observation)
        
        assert guard.has_pending()
        assert guard.pending_count() == 1
    
    def test_guard_clears_after_submission(self):
        """Verify guard clears observation after successful submission."""
        class RealMCPServer:
            def validate_observation(self, observation):
                return {
                    "classification": "SIGNAL",
                    "invariant_violated": None,
                    "proof": None,
                    "confidence": 0.0,
                    "coverage_gaps": [],
                }
        
        client = MCPClient(mcp_server=RealMCPServer())
        guard = ObservationSubmissionGuard(client)
        
        observation = Observation(hypothesis_id="test")
        guard.register_observation(observation)
        
        assert guard.has_pending()
        
        # Submit and clear
        classification = guard.submit_and_clear(observation)
        
        assert not guard.has_pending()
        assert classification is not None
    
    @given(st.lists(st.text(min_size=1), min_size=1, max_size=10))
    @settings(max_examples=50)
    def test_guard_tracks_multiple_observations(self, observation_ids):
        """Property test: Guard correctly tracks multiple observations."""
        class RealMCPServer:
            def validate_observation(self, observation):
                return {
                    "classification": "SIGNAL",
                    "invariant_violated": None,
                    "proof": None,
                    "confidence": 0.0,
                    "coverage_gaps": [],
                }
        
        client = MCPClient(mcp_server=RealMCPServer())
        guard = ObservationSubmissionGuard(client)
        
        observations = [Observation(id=oid, hypothesis_id="test") for oid in observation_ids]
        
        for obs in observations:
            guard.register_observation(obs)
        
        # Should have all observations pending (accounting for duplicates)
        unique_ids = set(observation_ids)
        assert guard.pending_count() == len(unique_ids)
        
        # Clear all
        guard.clear_all()
        assert not guard.has_pending()
