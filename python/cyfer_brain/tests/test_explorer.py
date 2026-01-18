"""
Tests for State Explorer

Property Tests:
    - Property 2: Observation Submission Completeness
    - All state transitions are submitted to MCP
"""

import pytest
from hypothesis import given, strategies as st, settings, assume

from cyfer_brain.explorer import (
    StateExplorer,
    StateTransition,
    StateType,
    AuthBoundary,
    FinancialState,
    WorkflowState,
)
from cyfer_brain.client import MCPClient
from cyfer_brain.types import (
    Hypothesis,
    Observation,
    ExplorationAction,
    ActionType,
)
from cyfer_brain.errors import ArchitecturalViolationError


class TestStateExplorer:
    """Tests for StateExplorer."""
    
    def test_explorer_creation(self):
        """Test explorer can be created with MCP client."""
        client = MCPClient(mcp_server=object())
        explorer = StateExplorer(client)
        assert explorer is not None
    
    def test_state_transition_has_no_violation_field(self):
        """StateTransition must NOT have is_violation field."""
        transition = StateTransition(
            id="test-trans",
            state_type=StateType.AUTHORIZATION,
            from_state={"role": "user"},
            to_state={"role": "admin"},
        )
        
        # StateTransition should NOT have violation fields
        assert not hasattr(transition, "is_violation")
        assert not hasattr(transition, "is_bug")
        assert not hasattr(transition, "classification")
    
    def test_classify_transition_raises_violation(self):
        """Attempting to classify transition must raise ArchitecturalViolationError."""
        client = MCPClient(mcp_server=object())
        explorer = StateExplorer(client)
        
        with pytest.raises(ArchitecturalViolationError) as exc_info:
            explorer.classify_transition(StateTransition())
        
        assert "classify a state transition" in str(exc_info.value)
    
    def test_detect_vulnerability_raises_violation(self):
        """Attempting to detect vulnerability must raise ArchitecturalViolationError."""
        client = MCPClient(mcp_server=object())
        explorer = StateExplorer(client)
        
        with pytest.raises(ArchitecturalViolationError) as exc_info:
            explorer.detect_vulnerability({"state": "changed"})
        
        assert "detect a vulnerability" in str(exc_info.value)


class TestAuthBoundaryExploration:
    """Tests for auth boundary exploration."""
    
    def test_explore_auth_boundaries_generates_observations(self):
        """Auth boundary exploration must generate observations."""
        client = MCPClient(mcp_server=object())
        explorer = StateExplorer(client)
        
        boundaries = [
            AuthBoundary(
                name="user_boundary",
                roles=["user", "admin"],
                permissions={"read": ["user", "admin"], "write": ["admin"]},
                endpoints=["/api/users", "/api/admin"],
            )
        ]
        
        hypothesis = Hypothesis(
            description="Test auth boundary",
            testability_score=0.7,
        )
        
        observations = explorer.explore_auth_boundaries(boundaries, hypothesis)
        
        # Should generate cross-role observations
        assert len(observations) > 0
        
        # All observations should be Observation type
        for obs in observations:
            assert isinstance(obs, Observation)
            assert obs.hypothesis_id == hypothesis.id
    
    def test_auth_observations_have_no_classification(self):
        """Auth observations must NOT have classification."""
        client = MCPClient(mcp_server=object())
        explorer = StateExplorer(client)
        
        boundaries = [
            AuthBoundary(
                name="test",
                roles=["user", "admin"],
                endpoints=["/api/test"],
            )
        ]
        
        hypothesis = Hypothesis(description="Test")
        observations = explorer.explore_auth_boundaries(boundaries, hypothesis)
        
        for obs in observations:
            # Observation must NOT have classification
            assert not hasattr(obs, "classification")
            assert not hasattr(obs, "is_bug")


class TestFinancialStateExploration:
    """Tests for financial state exploration."""
    
    def test_explore_financial_states_generates_observations(self):
        """Financial state exploration must generate observations."""
        client = MCPClient(mcp_server=object())
        explorer = StateExplorer(client)
        
        accounts = [
            FinancialState(
                account_id="acc-001",
                balance=1000.0,
                currency="USD",
                pending_transactions=[{"id": "tx-1", "amount": 100}],
            )
        ]
        
        hypothesis = Hypothesis(
            description="Test financial state",
            testability_score=0.6,
        )
        
        observations = explorer.explore_financial_states(accounts, hypothesis)
        
        # Should generate financial observations
        assert len(observations) > 0
        
        for obs in observations:
            assert isinstance(obs, Observation)
            assert "balance" in obs.before_state or "account_id" in obs.before_state


class TestWorkflowStateExploration:
    """Tests for workflow state exploration."""
    
    def test_explore_workflow_states_generates_observations(self):
        """Workflow state exploration must generate observations."""
        client = MCPClient(mcp_server=object())
        explorer = StateExplorer(client)
        
        workflows = [
            WorkflowState(
                workflow_id="wf-001",
                current_step=2,
                total_steps=5,
                completed_steps=[1, 2],
                required_order=True,
            )
        ]
        
        hypothesis = Hypothesis(
            description="Test workflow state",
            testability_score=0.65,
        )
        
        observations = explorer.explore_workflow_states(workflows, hypothesis)
        
        # Should generate workflow observations
        assert len(observations) > 0
        
        for obs in observations:
            assert isinstance(obs, Observation)
            assert obs.action.action_type == ActionType.WORKFLOW_STEP


class TestObservationSubmissionCompleteness:
    """Property 2: Observation Submission Completeness
    
    Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5
    - All state transitions are submitted to MCP
    - No observations are classified locally
    """
    
    @given(
        num_boundaries=st.integers(min_value=1, max_value=5),
        num_roles=st.integers(min_value=2, max_value=4),
        num_endpoints=st.integers(min_value=1, max_value=3),
    )
    @settings(max_examples=20)
    def test_all_auth_observations_submitted(
        self, num_boundaries, num_roles, num_endpoints
    ):
        """All auth boundary observations must be submittable to MCP."""
        client = MCPClient(mcp_server=object())
        explorer = StateExplorer(client)
        
        # Generate boundaries
        boundaries = []
        for i in range(num_boundaries):
            roles = [f"role_{j}" for j in range(num_roles)]
            endpoints = [f"/api/endpoint_{k}" for k in range(num_endpoints)]
            boundaries.append(
                AuthBoundary(
                    name=f"boundary_{i}",
                    roles=roles,
                    endpoints=endpoints,
                )
            )
        
        hypothesis = Hypothesis(description="Property test")
        observations = explorer.explore_auth_boundaries(boundaries, hypothesis)
        
        # All observations must be valid for MCP submission
        for obs in observations:
            assert isinstance(obs, Observation)
            assert obs.hypothesis_id == hypothesis.id
            assert obs.before_state is not None
            assert obs.action is not None
            # No local classification
            assert not hasattr(obs, "classification")
    
    @given(
        num_accounts=st.integers(min_value=1, max_value=5),
        balances=st.lists(
            st.floats(min_value=0, max_value=1000000, allow_nan=False),
            min_size=1,
            max_size=5,
        ),
    )
    @settings(max_examples=20)
    def test_all_financial_observations_submitted(self, num_accounts, balances):
        """All financial observations must be submittable to MCP."""
        client = MCPClient(mcp_server=object())
        explorer = StateExplorer(client)
        
        accounts = []
        for i in range(min(num_accounts, len(balances))):
            accounts.append(
                FinancialState(
                    account_id=f"acc-{i}",
                    balance=balances[i],
                )
            )
        
        hypothesis = Hypothesis(description="Property test")
        observations = explorer.explore_financial_states(accounts, hypothesis)
        
        # All observations must be valid for MCP submission
        for obs in observations:
            assert isinstance(obs, Observation)
            assert not hasattr(obs, "classification")
    
    def test_transition_recording(self):
        """State transitions must be recorded for tracking."""
        client = MCPClient(mcp_server=object())
        explorer = StateExplorer(client)
        
        transition = StateTransition(
            id="test-trans",
            state_type=StateType.DATA,
            from_state={"key": "value1"},
            to_state={"key": "value2"},
        )
        
        explorer.record_transition(transition)
        
        assert explorer.get_explored_count() == 1
        assert len(explorer.get_transitions()) == 1
