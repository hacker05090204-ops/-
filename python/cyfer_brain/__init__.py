"""
Cyfer Brain - Exploration and Hypothesis Generation Engine (Phase-2)

ARCHITECTURAL CONSTRAINT:
    Cyfer Brain is strictly separated from MCP (Phase-1 Truth Engine).
    - Cyfer Brain explores and proposes hypotheses
    - MCP judges and proves findings
    - Cyfer Brain NEVER classifies, computes confidence, or declares bugs
    - All observations MUST be submitted to MCP for classification

This module provides:
    - Hypothesis generation from target observations
    - State space exploration
    - Tool orchestration (treating outputs as untrusted signals)
    - Feedback reaction based on MCP classifications
    - Exploration boundary management
    - Strategy selection from fixed catalog
    - Parallel exploration with isolated threads
    - Retry management with parameter variations
"""

from .types import (
    Hypothesis,
    HypothesisStatus,
    Observation,
    ExplorationAction,
    ActionType,
    ActionResult,
    MCPClassification,
    ExplorationStats,
    ExplorationBoundary,
    ExplorationSummary,
    BoundaryStatus,
    RateLimitStatus,
    ScopeValidation,
    ToolOutput,
)
from .errors import (
    CyferBrainError,
    ExplorationError,
    BoundaryExceededError,
    MCPCommunicationError,
    MCPUnavailableError,
    ArchitecturalViolationError,
)
from .client import MCPClient, ObservationSubmissionGuard
from .hypothesis import HypothesisGenerator, Target
from .feedback import FeedbackReactor, ExplorationAdjustment
from .boundary import BoundaryManager, GlobalExplorationBudget
from .orchestrator import ToolOrchestrator, ToolDefinition, TOOL_CATALOG
from .explorer import StateExplorer, StateTransition, AuthBoundary, FinancialState, WorkflowState
from .strategy import StrategyEngine, Strategy, StrategyType, STRATEGY_CATALOG
from .parallel import ParallelExplorationManager, SubmissionCoordinator, ThreadState
from .retry import RetryManager, RetryAttempt, FailurePattern
from .brain import CyferBrain, ExplorationSession

__version__ = "0.1.0"
__all__ = [
    # Types
    "Hypothesis",
    "HypothesisStatus",
    "Observation",
    "ExplorationAction",
    "ActionType",
    "ActionResult",
    "MCPClassification",
    "ExplorationStats",
    "ExplorationBoundary",
    "ExplorationSummary",
    "BoundaryStatus",
    "RateLimitStatus",
    "ScopeValidation",
    "ToolOutput",
    # Errors
    "CyferBrainError",
    "ExplorationError",
    "BoundaryExceededError",
    "MCPCommunicationError",
    "MCPUnavailableError",
    "ArchitecturalViolationError",
    # Client
    "MCPClient",
    "ObservationSubmissionGuard",
    # Hypothesis
    "HypothesisGenerator",
    "Target",
    # Feedback
    "FeedbackReactor",
    "ExplorationAdjustment",
    # Boundary
    "BoundaryManager",
    "GlobalExplorationBudget",
    # Orchestrator
    "ToolOrchestrator",
    "ToolDefinition",
    "TOOL_CATALOG",
    # Explorer
    "StateExplorer",
    "StateTransition",
    "AuthBoundary",
    "FinancialState",
    "WorkflowState",
    # Strategy
    "StrategyEngine",
    "Strategy",
    "StrategyType",
    "STRATEGY_CATALOG",
    # Parallel
    "ParallelExplorationManager",
    "SubmissionCoordinator",
    "ThreadState",
    # Retry
    "RetryManager",
    "RetryAttempt",
    "FailurePattern",
    # Brain
    "CyferBrain",
    "ExplorationSession",
]
