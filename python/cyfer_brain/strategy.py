"""
Strategy Engine - Selects exploration strategies from a fixed catalog

ARCHITECTURAL CONSTRAINTS:
    1. Strategies are SELECTED from STRATEGY_CATALOG, not learned
    2. Strategy adaptation is based on MCP feedback only
    3. No machine learning or heuristic evolution
    4. Strategies guide exploration, not classification
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum, auto

from .types import (
    Hypothesis,
    MCPClassification,
    ExplorationStats,
)
from .feedback import ExplorationAdjustment

logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """Types of exploration strategies."""
    BREADTH_FIRST = auto()      # Explore many endpoints shallowly
    DEPTH_FIRST = auto()        # Explore one path deeply
    AUTH_FOCUSED = auto()       # Focus on authorization boundaries
    FINANCIAL_FOCUSED = auto()  # Focus on monetary invariants
    WORKFLOW_FOCUSED = auto()   # Focus on workflow invariants
    SIGNAL_FOLLOW = auto()      # Follow up on MCP SIGNAL classifications
    COVERAGE_DRIVEN = auto()    # Target unexplored invariant categories


@dataclass
class Strategy:
    """An exploration strategy from the catalog.
    
    NOTE: Strategies are FIXED definitions, not learned behaviors.
    """
    name: str
    strategy_type: StrategyType
    description: str
    target_categories: List[str] = field(default_factory=list)
    max_depth: int = 5
    max_breadth: int = 20
    priority_boost: float = 0.0  # Boost to testability for matching hypotheses
    
    def matches_hypothesis(self, hypothesis: Hypothesis) -> bool:
        """Check if this strategy applies to a hypothesis."""
        if not self.target_categories:
            return True  # Universal strategy
        
        for cat in hypothesis.target_invariant_categories:
            if cat in self.target_categories:
                return True
        return False


# =============================================================================
# STRATEGY_CATALOG - Fixed catalog of exploration strategies
# These are SELECTED, not learned. No ML or heuristic evolution.
# =============================================================================

STRATEGY_CATALOG: Dict[str, Strategy] = {
    "breadth_first": Strategy(
        name="breadth_first",
        strategy_type=StrategyType.BREADTH_FIRST,
        description="Explore many endpoints with shallow depth",
        target_categories=[],  # Universal
        max_depth=3,
        max_breadth=50,
        priority_boost=0.0,
    ),
    "depth_first": Strategy(
        name="depth_first",
        strategy_type=StrategyType.DEPTH_FIRST,
        description="Explore one path deeply before moving on",
        target_categories=[],  # Universal
        max_depth=10,
        max_breadth=5,
        priority_boost=0.0,
    ),
    "auth_boundary": Strategy(
        name="auth_boundary",
        strategy_type=StrategyType.AUTH_FOCUSED,
        description="Focus on authorization and access control boundaries",
        target_categories=["Authorization", "SessionManagement", "Trust"],
        max_depth=5,
        max_breadth=30,
        priority_boost=0.2,
    ),
    "financial_integrity": Strategy(
        name="financial_integrity",
        strategy_type=StrategyType.FINANCIAL_FOCUSED,
        description="Focus on monetary and financial invariants",
        target_categories=["Monetary", "DataIntegrity"],
        max_depth=7,
        max_breadth=20,
        priority_boost=0.3,
    ),
    "workflow_bypass": Strategy(
        name="workflow_bypass",
        strategy_type=StrategyType.WORKFLOW_FOCUSED,
        description="Focus on workflow step ordering and bypass",
        target_categories=["Workflow"],
        max_depth=8,
        max_breadth=15,
        priority_boost=0.2,
    ),
    "signal_followup": Strategy(
        name="signal_followup",
        strategy_type=StrategyType.SIGNAL_FOLLOW,
        description="Follow up on MCP SIGNAL classifications",
        target_categories=[],  # Determined by signal
        max_depth=6,
        max_breadth=10,
        priority_boost=0.4,
    ),
    "coverage_expansion": Strategy(
        name="coverage_expansion",
        strategy_type=StrategyType.COVERAGE_DRIVEN,
        description="Target unexplored invariant categories",
        target_categories=[],  # Determined by coverage gaps
        max_depth=5,
        max_breadth=25,
        priority_boost=0.1,
    ),
}


@dataclass
class StrategyState:
    """State tracking for strategy engine."""
    current_strategy: str = "breadth_first"
    strategies_used: Set[str] = field(default_factory=set)
    strategy_results: Dict[str, ExplorationStats] = field(default_factory=dict)
    consecutive_failures: int = 0


class StrategyEngine:
    """Selects and adapts exploration strategies from STRATEGY_CATALOG.
    
    ARCHITECTURAL CONSTRAINTS:
        - Strategies are SELECTED from catalog, not learned
        - Adaptation is based on MCP feedback only
        - No machine learning or heuristic evolution
        - Strategies guide exploration, not classification
    """
    
    # Thresholds for strategy switching
    FAILURE_THRESHOLD = 5  # Switch after 5 consecutive NO_ISSUE
    SIGNAL_THRESHOLD = 3   # Switch to signal_followup after 3 signals
    
    def __init__(self):
        self._state = StrategyState()
        self._catalog = STRATEGY_CATALOG.copy()
    
    @property
    def current_strategy(self) -> Strategy:
        """Get the current active strategy."""
        return self._catalog[self._state.current_strategy]
    
    def generate_strategy(
        self,
        target_info: Dict[str, any],
        coverage_gaps: Optional[List[str]] = None
    ) -> Strategy:
        """Select initial strategy based on target characteristics.
        
        NOTE: This SELECTS from catalog, does not generate new strategies.
        
        Args:
            target_info: Information about the target
            coverage_gaps: Known coverage gaps from MCP
            
        Returns:
            Selected strategy from catalog
        """
        # Select based on target characteristics
        has_financial = target_info.get("has_financial_features", False)
        has_workflow = target_info.get("has_workflow_features", False)
        has_auth = target_info.get("has_authentication", False)
        
        # Priority selection from catalog
        if has_financial:
            selected = "financial_integrity"
        elif has_workflow:
            selected = "workflow_bypass"
        elif has_auth:
            selected = "auth_boundary"
        elif coverage_gaps:
            selected = "coverage_expansion"
        else:
            selected = "breadth_first"
        
        self._state.current_strategy = selected
        self._state.strategies_used.add(selected)
        
        logger.info(f"Selected strategy: {selected}")
        return self._catalog[selected]
    
    def adapt_strategy(
        self,
        classification: MCPClassification,
        current_stats: ExplorationStats
    ) -> Strategy:
        """Adapt strategy based on MCP feedback.
        
        CRITICAL: Adaptation is based on MCP feedback ONLY.
        No learning or heuristic evolution.
        
        Args:
            classification: Latest MCP classification
            current_stats: Current exploration statistics
            
        Returns:
            Adapted strategy (may be same or different from catalog)
        """
        current = self._state.current_strategy
        
        # React to MCP classification
        if classification.is_bug():
            # Bug found - continue with current strategy
            self._state.consecutive_failures = 0
            logger.info(f"BUG found, continuing with {current}")
            return self._catalog[current]
        
        elif classification.is_signal():
            # Signal found - consider switching to signal_followup
            self._state.consecutive_failures = 0
            if current_stats.signals_found >= self.SIGNAL_THRESHOLD:
                return self.switch_strategy("signal_followup")
            return self._catalog[current]
        
        elif classification.is_no_issue():
            # No issue - track failures
            self._state.consecutive_failures += 1
            if self._state.consecutive_failures >= self.FAILURE_THRESHOLD:
                return self._select_alternative_strategy()
            return self._catalog[current]
        
        elif classification.is_coverage_gap():
            # Coverage gap - consider coverage_expansion
            return self.switch_strategy("coverage_expansion")
        
        return self._catalog[current]
    
    def switch_strategy(self, strategy_name: str) -> Strategy:
        """Switch to a specific strategy from catalog.
        
        Args:
            strategy_name: Name of strategy in catalog
            
        Returns:
            The selected strategy
            
        Raises:
            ValueError: If strategy not in catalog
        """
        if strategy_name not in self._catalog:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        old_strategy = self._state.current_strategy
        self._state.current_strategy = strategy_name
        self._state.strategies_used.add(strategy_name)
        self._state.consecutive_failures = 0
        
        logger.info(f"Switched strategy: {old_strategy} -> {strategy_name}")
        return self._catalog[strategy_name]
    
    def _select_alternative_strategy(self) -> Strategy:
        """Select an alternative strategy when current is failing."""
        current = self._state.current_strategy
        
        # Find unused strategies
        unused = set(self._catalog.keys()) - self._state.strategies_used
        
        if unused:
            # Select first unused strategy
            alternative = next(iter(unused))
        else:
            # All strategies used - cycle through
            strategies = list(self._catalog.keys())
            current_idx = strategies.index(current)
            alternative = strategies[(current_idx + 1) % len(strategies)]
        
        return self.switch_strategy(alternative)
    
    def prioritize_hypotheses(
        self,
        hypotheses: List[Hypothesis]
    ) -> List[Hypothesis]:
        """Prioritize hypotheses based on current strategy.
        
        Args:
            hypotheses: List of hypotheses to prioritize
            
        Returns:
            Prioritized list based on strategy
        """
        strategy = self.current_strategy
        
        def score(h: Hypothesis) -> float:
            base = h.testability_score
            if strategy.matches_hypothesis(h):
                base += strategy.priority_boost
            return base
        
        return sorted(hypotheses, key=score, reverse=True)
    
    def get_strategy_bounds(self) -> tuple:
        """Get depth and breadth bounds from current strategy."""
        strategy = self.current_strategy
        return strategy.max_depth, strategy.max_breadth
    
    def get_used_strategies(self) -> List[str]:
        """Get list of strategies that have been used."""
        return list(self._state.strategies_used)
    
    def reset(self) -> None:
        """Reset strategy state."""
        self._state = StrategyState()
