"""
State Explorer - Explores target state space for hypothesis testing

ARCHITECTURAL CONSTRAINTS:
    1. State exploration generates OBSERVATIONS, not findings
    2. All state transitions MUST be submitted to MCP
    3. Explorer does NOT classify state changes
    4. State changes are UNTRUSTED until MCP validates
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set, Callable
from datetime import datetime, timezone
from enum import Enum, auto

from .types import (
    Hypothesis,
    Observation,
    ExplorationAction,
    ActionType,
    ActionResult,
    MCPClassification,
)
from .client import MCPClient
from .errors import ExplorationError, ArchitecturalViolationError

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class StateType(Enum):
    """Types of state being explored."""
    AUTHENTICATION = auto()
    AUTHORIZATION = auto()
    FINANCIAL = auto()
    WORKFLOW = auto()
    SESSION = auto()
    DATA = auto()


@dataclass
class StateTransition:
    """A state transition to explore.
    
    NOTE: This is an OBSERVATION, not a finding.
    MCP will determine if this transition violates any invariants.
    """
    id: str = ""
    state_type: StateType = StateType.DATA
    from_state: Dict[str, Any] = field(default_factory=dict)
    to_state: Dict[str, Any] = field(default_factory=dict)
    action: ExplorationAction = field(default_factory=ExplorationAction)
    timestamp: datetime = field(default_factory=_utc_now)
    # NOTE: No "is_violation" field - that's MCP's determination


@dataclass
class AuthBoundary:
    """Authentication/authorization boundary to explore."""
    name: str
    roles: List[str] = field(default_factory=list)
    permissions: Dict[str, List[str]] = field(default_factory=dict)
    endpoints: List[str] = field(default_factory=list)


@dataclass
class FinancialState:
    """Financial state to explore."""
    account_id: str = ""
    balance: float = 0.0
    currency: str = "USD"
    pending_transactions: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class WorkflowState:
    """Workflow state to explore."""
    workflow_id: str = ""
    current_step: int = 0
    total_steps: int = 0
    completed_steps: List[int] = field(default_factory=list)
    required_order: bool = True


class StateExplorer:
    """Explores target state space for hypothesis testing.
    
    ARCHITECTURAL CONSTRAINTS:
        - Generates OBSERVATIONS, not findings
        - All transitions submitted to MCP for classification
        - Does NOT classify state changes
        - State changes are UNTRUSTED until MCP validates
    """
    
    def __init__(self, mcp_client: MCPClient):
        """Initialize state explorer.
        
        Args:
            mcp_client: Client for submitting observations to MCP
        """
        self._mcp_client = mcp_client
        self._explored_states: Set[str] = set()
        self._transitions: List[StateTransition] = []
    
    def enumerate_transitions(
        self,
        initial_state: Dict[str, Any],
        action_generator: Callable[[], List[ExplorationAction]]
    ) -> List[StateTransition]:
        """Enumerate possible state transitions from initial state.
        
        NOTE: This generates transitions to EXPLORE, not findings.
        Each transition will be submitted to MCP for classification.
        
        Args:
            initial_state: Starting state
            action_generator: Function that generates possible actions
            
        Returns:
            List of state transitions to explore
        """
        transitions = []
        actions = action_generator()
        
        for action in actions:
            transition = StateTransition(
                id=f"trans-{len(transitions)}",
                from_state=initial_state.copy(),
                action=action,
                # to_state will be filled after action execution
            )
            transitions.append(transition)
        
        logger.info(f"Enumerated {len(transitions)} transitions to explore")
        return transitions
    
    def explore_auth_boundaries(
        self,
        boundaries: List[AuthBoundary],
        hypothesis: Hypothesis
    ) -> List[Observation]:
        """Explore authentication/authorization boundaries.
        
        Generates observations for cross-role access attempts.
        MCP will determine if any invariants are violated.
        
        Args:
            boundaries: Auth boundaries to explore
            hypothesis: The hypothesis being tested
            
        Returns:
            List of observations to submit to MCP
        """
        observations = []
        
        for boundary in boundaries:
            for role in boundary.roles:
                for endpoint in boundary.endpoints:
                    # Generate cross-role access observation
                    for other_role in boundary.roles:
                        if other_role != role:
                            obs = self._create_auth_observation(
                                hypothesis=hypothesis,
                                acting_role=role,
                                target_role=other_role,
                                endpoint=endpoint,
                                boundary=boundary,
                            )
                            observations.append(obs)
        
        logger.info(f"Generated {len(observations)} auth boundary observations")
        return observations
    
    def _create_auth_observation(
        self,
        hypothesis: Hypothesis,
        acting_role: str,
        target_role: str,
        endpoint: str,
        boundary: AuthBoundary
    ) -> Observation:
        """Create observation for auth boundary test."""
        before_state = {
            "acting_role": acting_role,
            "target_role": target_role,
            "endpoint": endpoint,
            "boundary": boundary.name,
        }
        
        action = ExplorationAction(
            action_type=ActionType.AUTHENTICATION,
            target=endpoint,
            parameters={
                "acting_as": acting_role,
                "accessing_as": target_role,
            },
        )
        
        # after_state will be filled after action execution
        return Observation(
            hypothesis_id=hypothesis.id,
            before_state=before_state,
            action=action,
            after_state={},  # To be filled
        )
    
    def explore_financial_states(
        self,
        accounts: List[FinancialState],
        hypothesis: Hypothesis
    ) -> List[Observation]:
        """Explore financial state transitions.
        
        Generates observations for balance manipulation attempts.
        MCP will determine if monetary invariants are violated.
        
        Args:
            accounts: Financial states to explore
            hypothesis: The hypothesis being tested
            
        Returns:
            List of observations to submit to MCP
        """
        observations = []
        
        for account in accounts:
            # Explore balance manipulation
            obs = self._create_financial_observation(
                hypothesis=hypothesis,
                account=account,
                operation="balance_check",
            )
            observations.append(obs)
            
            # Explore double-spend scenarios
            if account.pending_transactions:
                obs = self._create_financial_observation(
                    hypothesis=hypothesis,
                    account=account,
                    operation="double_spend_check",
                )
                observations.append(obs)
        
        logger.info(f"Generated {len(observations)} financial state observations")
        return observations
    
    def _create_financial_observation(
        self,
        hypothesis: Hypothesis,
        account: FinancialState,
        operation: str
    ) -> Observation:
        """Create observation for financial state test."""
        before_state = {
            "account_id": account.account_id,
            "balance": account.balance,
            "currency": account.currency,
            "pending_count": len(account.pending_transactions),
        }
        
        action = ExplorationAction(
            action_type=ActionType.STATE_MUTATION,
            target=f"account:{account.account_id}",
            parameters={"operation": operation},
        )
        
        return Observation(
            hypothesis_id=hypothesis.id,
            before_state=before_state,
            action=action,
            after_state={},  # To be filled
        )
    
    def explore_workflow_states(
        self,
        workflows: List[WorkflowState],
        hypothesis: Hypothesis
    ) -> List[Observation]:
        """Explore workflow state transitions.
        
        Generates observations for workflow step manipulation.
        MCP will determine if workflow invariants are violated.
        
        Args:
            workflows: Workflow states to explore
            hypothesis: The hypothesis being tested
            
        Returns:
            List of observations to submit to MCP
        """
        observations = []
        
        for workflow in workflows:
            # Explore step skipping
            if workflow.required_order and workflow.current_step < workflow.total_steps:
                obs = self._create_workflow_observation(
                    hypothesis=hypothesis,
                    workflow=workflow,
                    operation="skip_step",
                    target_step=workflow.current_step + 2,  # Skip one step
                )
                observations.append(obs)
            
            # Explore step replay
            if workflow.completed_steps:
                obs = self._create_workflow_observation(
                    hypothesis=hypothesis,
                    workflow=workflow,
                    operation="replay_step",
                    target_step=workflow.completed_steps[0],
                )
                observations.append(obs)
        
        logger.info(f"Generated {len(observations)} workflow state observations")
        return observations
    
    def _create_workflow_observation(
        self,
        hypothesis: Hypothesis,
        workflow: WorkflowState,
        operation: str,
        target_step: int
    ) -> Observation:
        """Create observation for workflow state test."""
        before_state = {
            "workflow_id": workflow.workflow_id,
            "current_step": workflow.current_step,
            "total_steps": workflow.total_steps,
            "completed_steps": workflow.completed_steps.copy(),
        }
        
        action = ExplorationAction(
            action_type=ActionType.WORKFLOW_STEP,
            target=f"workflow:{workflow.workflow_id}",
            parameters={
                "operation": operation,
                "target_step": target_step,
            },
        )
        
        return Observation(
            hypothesis_id=hypothesis.id,
            before_state=before_state,
            action=action,
            after_state={},  # To be filled
        )
    
    def submit_observations(
        self,
        observations: List[Observation]
    ) -> List[MCPClassification]:
        """Submit all observations to MCP for classification.
        
        CRITICAL: This is the ONLY way state changes are classified.
        Explorer submits; MCP judges.
        
        Args:
            observations: Observations to submit
            
        Returns:
            List of MCP classifications
        """
        classifications = []
        
        for obs in observations:
            classification = self._mcp_client.submit_observation(obs)
            classifications.append(classification)
            logger.debug(
                f"Observation {obs.id} classified as {classification.classification}"
            )
        
        return classifications
    
    def record_transition(self, transition: StateTransition) -> None:
        """Record a state transition for tracking."""
        state_key = f"{transition.from_state}->{transition.to_state}"
        self._explored_states.add(state_key)
        self._transitions.append(transition)
    
    def get_explored_count(self) -> int:
        """Get count of explored state transitions."""
        return len(self._explored_states)
    
    def get_transitions(self) -> List[StateTransition]:
        """Get all recorded transitions."""
        return self._transitions.copy()
    
    # =========================================================================
    # EXPLICITLY REJECTED METHODS
    # =========================================================================
    
    def classify_transition(self, *args, **kwargs):
        """REJECTED: Classification is MCP's responsibility.
        
        Raises:
            ArchitecturalViolationError: Always
        """
        raise ArchitecturalViolationError(
            "classify a state transition",
            "Submit observations to MCP via submit_observations() instead."
        )
    
    def detect_vulnerability(self, *args, **kwargs):
        """REJECTED: Vulnerability detection is MCP's responsibility.
        
        Raises:
            ArchitecturalViolationError: Always
        """
        raise ArchitecturalViolationError(
            "detect a vulnerability",
            "State changes are UNTRUSTED. Only MCP can determine violations."
        )
