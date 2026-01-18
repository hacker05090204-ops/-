"""
CyferBrain - Main Orchestrator for Exploration Engine

ARCHITECTURAL CONSTRAINTS:
    1. Cyfer Brain EXPLORES, MCP JUDGES
    2. All observations MUST be submitted to MCP
    3. Cyfer Brain NEVER classifies findings
    4. Scope validation is DELEGATED to MCP
    5. Logging distinguishes exploration from judgement
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timezone

from .types import (
    Hypothesis,
    HypothesisStatus,
    Observation,
    ExplorationAction,
    ActionType,
    MCPClassification,
    ExplorationStats,
    ExplorationSummary,
    ExplorationBoundary,
    ScopeValidation,
)
from .client import MCPClient
from .hypothesis import HypothesisGenerator, Target
from .feedback import FeedbackReactor, ExplorationAdjustment
from .boundary import BoundaryManager
from .orchestrator import ToolOrchestrator
from .explorer import StateExplorer
from .strategy import StrategyEngine, STRATEGY_CATALOG
from .parallel import ParallelExplorationManager
from .retry import RetryManager
from .errors import (
    CyferBrainError,
    MCPUnavailableError,
    ArchitecturalViolationError,
    BoundaryExceededError,
)

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


@dataclass
class ExplorationSession:
    """State for an exploration session."""
    session_id: str = ""
    target: Optional[Target] = None
    stats: ExplorationStats = field(default_factory=ExplorationStats)
    hypotheses: List[Hypothesis] = field(default_factory=list)
    classifications: List[MCPClassification] = field(default_factory=list)
    started_at: datetime = field(default_factory=_utc_now)
    completed_at: Optional[datetime] = None
    stopped_reason: str = ""


class CyferBrain:
    """Main orchestrator for Cyfer Brain exploration engine.
    
    ARCHITECTURAL CONSTRAINTS:
        - Cyfer Brain EXPLORES, MCP JUDGES
        - All observations MUST be submitted to MCP
        - Cyfer Brain NEVER classifies findings
        - Scope validation is DELEGATED to MCP
        - Logging distinguishes exploration from judgement
        
    Exploration Loop:
        1. Generate hypotheses from target
        2. Execute hypothesis (tool execution, state exploration)
        3. Submit observation to MCP
        4. React to MCP classification
        5. Repeat until boundaries reached or stop-loss triggered
    """
    
    def __init__(
        self,
        mcp_client: MCPClient,
        boundary: Optional[ExplorationBoundary] = None,
        max_parallel_workers: int = 4
    ):
        """Initialize CyferBrain.
        
        Args:
            mcp_client: Client for MCP communication
            boundary: Exploration boundaries
            max_parallel_workers: Maximum parallel exploration threads
        """
        self._mcp_client = mcp_client
        self._boundary_manager = BoundaryManager(boundary)
        
        # Initialize components
        self._hypothesis_generator = HypothesisGenerator()
        self._feedback_reactor = FeedbackReactor()
        self._tool_orchestrator = ToolOrchestrator(mcp_client)
        self._state_explorer = StateExplorer(mcp_client)
        self._strategy_engine = StrategyEngine()
        self._parallel_manager = ParallelExplorationManager(
            mcp_client, self._boundary_manager, max_parallel_workers
        )
        self._retry_manager = RetryManager()
        
        # Session state
        self._session: Optional[ExplorationSession] = None
    
    def explore(
        self,
        target: Target,
        parallel: bool = False
    ) -> ExplorationSummary:
        """Execute exploration loop for a target.
        
        CRITICAL: This method EXPLORES. MCP JUDGES.
        All observations are submitted to MCP for classification.
        
        Args:
            target: Target to explore
            parallel: Whether to use parallel exploration
            
        Returns:
            ExplorationSummary of what was explored
            
        Raises:
            MCPUnavailableError: If MCP is unavailable (HARD STOP)
            ArchitecturalViolationError: If architectural boundary violated
        """
        # Initialize session
        self._session = ExplorationSession(
            session_id=f"session-{_utc_now().isoformat()}",
            target=target,
        )
        
        logger.info(f"[EXPLORATION] Starting exploration of {target.domain}")
        
        try:
            # Step 1: Validate scope (DELEGATED to MCP)
            self._validate_scope(target)
            
            # Step 2: Select initial strategy
            strategy = self._strategy_engine.generate_strategy({
                "has_financial_features": target.has_financial_features,
                "has_workflow_features": target.has_workflow_features,
                "has_authentication": target.authentication_type is not None,
            })
            logger.info(f"[EXPLORATION] Selected strategy: {strategy.name}")
            
            # Step 3: Generate hypotheses
            hypotheses = self._hypothesis_generator.generate_from_recon(target)
            hypotheses = self._strategy_engine.prioritize_hypotheses(hypotheses)
            self._session.hypotheses = hypotheses
            self._session.stats.hypotheses_generated = len(hypotheses)
            
            logger.info(f"[EXPLORATION] Generated {len(hypotheses)} hypotheses")
            
            # Step 4: Execute exploration loop
            if parallel:
                self._explore_parallel(hypotheses)
            else:
                self._explore_sequential(hypotheses)
            
            # Step 5: Generate summary
            self._session.completed_at = _utc_now()
            self._session.stats.time_elapsed_seconds = (
                self._session.completed_at - self._session.started_at
            ).total_seconds()
            
            return self._generate_summary()
            
        except MCPUnavailableError:
            logger.error("[HARD STOP] MCP unavailable - cannot continue")
            self._session.stopped_reason = "MCP unavailable (HARD STOP)"
            raise
            
        except BoundaryExceededError as e:
            logger.info(f"[EXPLORATION] Boundary reached: {e}")
            self._session.stopped_reason = str(e)
            return self._generate_summary()
            
        except ArchitecturalViolationError:
            logger.error("[HARD STOP] Architectural violation detected")
            raise
    
    def _validate_scope(self, target: Target) -> None:
        """Validate target is in scope.
        
        DELEGATES to MCP Rule Engine - Cyfer Brain does not make scope decisions.
        """
        logger.info(f"[EXPLORATION] Validating scope for {target.domain}")
        
        validation = self._mcp_client.validate_scope(target.domain)
        
        if not validation.is_in_scope:
            raise CyferBrainError(
                f"Target {target.domain} is out of scope: {validation.reason}"
            )
        
        if validation.warnings:
            for warning in validation.warnings:
                logger.warning(f"[SCOPE WARNING] {warning}")
    
    def _explore_sequential(self, hypotheses: List[Hypothesis]) -> None:
        """Execute sequential exploration loop."""
        for hypothesis in hypotheses:
            # Check boundaries
            if not self._boundary_manager.can_continue():
                logger.info("[EXPLORATION] Boundary reached, stopping")
                break
            
            # Check stop-loss
            if self._feedback_reactor.apply_stop_loss(self._session.stats):
                logger.info("[EXPLORATION] Stop-loss triggered")
                self._session.stopped_reason = "Stop-loss triggered"
                break
            
            # Execute hypothesis
            classification = self._execute_hypothesis(hypothesis)
            
            if classification:
                # React to MCP classification
                adjustment = self._feedback_reactor.react_to_classification(
                    hypothesis, classification
                )
                
                # Adapt strategy based on feedback
                self._strategy_engine.adapt_strategy(
                    classification, self._session.stats
                )
                
                # Handle adjustment
                self._handle_adjustment(adjustment, hypothesis, classification)
    
    def _explore_parallel(self, hypotheses: List[Hypothesis]) -> None:
        """Execute parallel exploration."""
        def executor_fn(h: Hypothesis) -> Observation:
            return self._create_observation(h)
        
        results = self._parallel_manager.explore_parallel(hypotheses, executor_fn)
        
        # Merge results
        merged_stats = self._parallel_manager.merge_results(results)
        self._session.stats.hypotheses_tested += merged_stats.hypotheses_tested
        self._session.stats.observations_submitted += merged_stats.observations_submitted
        self._session.stats.bugs_found += merged_stats.bugs_found
        self._session.stats.signals_found += merged_stats.signals_found
        self._session.stats.no_issues += merged_stats.no_issues
        self._session.stats.coverage_gaps += merged_stats.coverage_gaps
        self._session.stats.errors_encountered += merged_stats.errors_encountered
    
    def _execute_hypothesis(self, hypothesis: Hypothesis) -> Optional[MCPClassification]:
        """Execute a single hypothesis and submit to MCP.
        
        Returns:
            MCPClassification from MCP, or None if execution failed
        """
        logger.debug(f"[EXPLORATION] Testing hypothesis: {hypothesis.description[:50]}")
        
        # Consume budget
        if not self._boundary_manager.consume_action():
            raise BoundaryExceededError("Action budget exhausted")
        
        try:
            # Execute with retry
            classification = self._retry_manager.execute_with_retry(
                hypothesis,
                lambda h: self._tool_orchestrator.execute_hypothesis(h),
            )
            
            if classification:
                self._session.classifications.append(classification)
                self._update_stats(classification)
                
                # Log MCP's judgement (not ours)
                logger.info(
                    f"[MCP JUDGEMENT] Hypothesis {hypothesis.id[:8]} "
                    f"classified as {classification.classification}"
                )
            
            return classification
            
        except MCPUnavailableError:
            raise
        except Exception as e:
            logger.error(f"[EXPLORATION] Hypothesis execution failed: {e}")
            self._session.stats.errors_encountered += 1
            return None
    
    def _create_observation(self, hypothesis: Hypothesis) -> Observation:
        """Create observation from hypothesis for parallel execution."""
        action = ExplorationAction(
            action_type=ActionType.TOOL_EXECUTION,
            target=hypothesis.description,
        )
        
        return Observation(
            hypothesis_id=hypothesis.id,
            before_state={},
            action=action,
            after_state={},
        )
    
    def _update_stats(self, classification: MCPClassification) -> None:
        """Update session statistics based on MCP classification."""
        self._session.stats.observations_submitted += 1
        self._session.stats.hypotheses_tested += 1
        
        if classification.is_bug():
            self._session.stats.bugs_found += 1
        elif classification.is_signal():
            self._session.stats.signals_found += 1
        elif classification.is_no_issue():
            self._session.stats.no_issues += 1
        elif classification.is_coverage_gap():
            self._session.stats.coverage_gaps += 1
    
    def _handle_adjustment(
        self,
        adjustment: ExplorationAdjustment,
        hypothesis: Hypothesis,
        classification: MCPClassification
    ) -> None:
        """Handle exploration adjustment from feedback reactor."""
        if adjustment == ExplorationAdjustment.STOP_PATH:
            logger.info(f"[EXPLORATION] Stopping path - BUG found")
            
        elif adjustment == ExplorationAdjustment.INCREASE_DEPTH:
            logger.info(f"[EXPLORATION] Increasing depth for signals")
            # Generate follow-up hypotheses
            followups = self._hypothesis_generator.generate_from_signal(classification)
            self._session.hypotheses.extend(followups)
            
        elif adjustment == ExplorationAdjustment.STOP_CATEGORY:
            logger.info(f"[EXPLORATION] Stopping category - diminishing returns")
    
    def _generate_summary(self) -> ExplorationSummary:
        """Generate exploration summary.
        
        CRITICAL: This is an EXPLORATION summary, NOT a coverage report.
        MCP's CoverageReport is authoritative for invariant coverage.
        """
        return self._boundary_manager.generate_exploration_summary(
            stats=self._session.stats,
            target=self._session.target.domain if self._session.target else "",
            hypotheses_tested=[h.id for h in self._session.hypotheses if h.status == HypothesisStatus.RESOLVED],
            strategies_used=self._strategy_engine.get_used_strategies(),
            stopped_reason=self._session.stopped_reason,
        )
    
    def get_session(self) -> Optional[ExplorationSession]:
        """Get current exploration session."""
        return self._session
    
    def get_escalated_hypotheses(self) -> List[str]:
        """Get hypotheses that need human review."""
        return self._retry_manager.get_escalated_hypotheses()
    
    # =========================================================================
    # EXPLICITLY REJECTED METHODS
    # =========================================================================
    
    def classify_finding(self, *args, **kwargs):
        """REJECTED: Classification is MCP's responsibility.
        
        Raises:
            ArchitecturalViolationError: Always
        """
        raise ArchitecturalViolationError(
            "classify a finding",
            "Cyfer Brain explores; MCP judges. Submit observations to MCP."
        )
    
    def generate_proof(self, *args, **kwargs):
        """REJECTED: Proof generation is MCP's responsibility.
        
        Raises:
            ArchitecturalViolationError: Always
        """
        raise ArchitecturalViolationError(
            "generate a proof",
            "Proofs are generated by MCP when it classifies observations as BUG."
        )
    
    def compute_confidence(self, *args, **kwargs):
        """REJECTED: Confidence computation is MCP's responsibility.
        
        Raises:
            ArchitecturalViolationError: Always
        """
        raise ArchitecturalViolationError(
            "compute confidence",
            "Confidence is computed by MCP, not Cyfer Brain."
        )
    
    def auto_submit_report(self, *args, **kwargs):
        """REJECTED: Auto-submitting reports is not allowed.
        
        Raises:
            ArchitecturalViolationError: Always
        """
        raise ArchitecturalViolationError(
            "auto-submit a report",
            "Only MCP-proven bugs can be reported, and submission requires human review."
        )
