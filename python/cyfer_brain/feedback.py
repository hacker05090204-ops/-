"""
Feedback Reactor - Adjusts exploration based on MCP classification results

ARCHITECTURAL CONSTRAINTS:
    1. Reactions are DETERMINISTIC based on classification type
    2. NEVER reinterprets MCP classifications
    3. COVERAGE_GAP is NOT interpreted as a finding
    4. Only MCP BUG classifications count as bugs
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum, auto
from collections import defaultdict

from .types import (
    Hypothesis,
    HypothesisStatus,
    MCPClassification,
    ExplorationStats,
)

logger = logging.getLogger(__name__)


class ExplorationAdjustment(Enum):
    """Adjustments to exploration based on MCP feedback."""
    CONTINUE = auto()           # Continue exploring this path
    STOP_PATH = auto()          # Stop exploring this specific path (BUG found)
    DEPRIORITIZE = auto()       # Reduce priority of similar hypotheses
    INCREASE_DEPTH = auto()     # Explore deeper in this category
    STOP_CATEGORY = auto()      # Stop exploring this category (diminishing returns)


@dataclass
class CategoryStats:
    """Statistics for a specific invariant category."""
    bugs: int = 0
    signals: int = 0
    no_issues: int = 0
    coverage_gaps: int = 0
    total_tested: int = 0
    
    @property
    def signal_rate(self) -> float:
        """Rate of SIGNAL classifications."""
        if self.total_tested == 0:
            return 0.0
        return self.signals / self.total_tested
    
    @property
    def no_issue_rate(self) -> float:
        """Rate of NO_ISSUE classifications."""
        if self.total_tested == 0:
            return 0.0
        return self.no_issues / self.total_tested


@dataclass
class FeedbackState:
    """State tracking for feedback reactor."""
    category_stats: Dict[str, CategoryStats] = field(default_factory=lambda: defaultdict(CategoryStats))
    consecutive_no_issues: int = 0
    total_classifications: int = 0


class FeedbackReactor:
    """Adjusts exploration based on MCP classification results.
    
    ARCHITECTURAL CONSTRAINTS:
        - Reactions are DETERMINISTIC based on classification type
        - NEVER reinterprets MCP classifications
        - COVERAGE_GAP is NOT a finding
        - Only MCP BUG classifications count as bugs
    """
    
    # Thresholds for stop-loss rules
    SIGNAL_THRESHOLD_FOR_DEPTH = 0.3  # If >30% signals, increase depth
    NO_ISSUE_THRESHOLD_FOR_STOP = 0.8  # If >80% no-issues, stop category
    CONSECUTIVE_NO_ISSUE_LIMIT = 10   # Stop after 10 consecutive no-issues
    
    def __init__(self):
        self._state = FeedbackState()
    
    def react_to_classification(
        self, 
        hypothesis: Hypothesis, 
        classification: MCPClassification
    ) -> ExplorationAdjustment:
        """Adjust exploration based on MCP classification.
        
        CRITICAL: This method reacts to MCP's authoritative classification.
        It does NOT reinterpret or override the classification.
        
        Args:
            hypothesis: The hypothesis that was tested
            classification: MCP's classification (authoritative)
            
        Returns:
            ExplorationAdjustment indicating how to proceed
        """
        # Update hypothesis with MCP classification
        hypothesis.mcp_classification = classification
        hypothesis.status = HypothesisStatus.RESOLVED
        
        # Update statistics
        self._update_stats(hypothesis, classification)
        
        # Determine adjustment based on classification type
        # This is DETERMINISTIC — same classification always produces same adjustment
        if classification.is_bug():
            return self._react_to_bug(hypothesis, classification)
        elif classification.is_signal():
            return self._react_to_signal(hypothesis, classification)
        elif classification.is_no_issue():
            return self._react_to_no_issue(hypothesis, classification)
        elif classification.is_coverage_gap():
            return self._react_to_coverage_gap(hypothesis, classification)
        else:
            logger.warning(f"Unknown classification type: {classification.classification}")
            return ExplorationAdjustment.CONTINUE
    
    def _react_to_bug(
        self, 
        hypothesis: Hypothesis, 
        classification: MCPClassification
    ) -> ExplorationAdjustment:
        """React to MCP BUG classification.
        
        BUG means MCP has proven an invariant violation.
        We stop exploring this specific path (the bug is found).
        """
        logger.info(
            f"MCP classified {hypothesis.id} as BUG: {classification.invariant_violated}"
        )
        
        # Reset consecutive no-issues counter
        self._state.consecutive_no_issues = 0
        
        # Stop exploring this path — the bug is proven
        return ExplorationAdjustment.STOP_PATH
    
    def _react_to_signal(
        self, 
        hypothesis: Hypothesis, 
        classification: MCPClassification
    ) -> ExplorationAdjustment:
        """React to MCP SIGNAL classification.
        
        SIGNAL means something interesting but not proven.
        We continue exploring and may increase depth.
        """
        logger.info(f"MCP classified {hypothesis.id} as SIGNAL")
        
        # Reset consecutive no-issues counter
        self._state.consecutive_no_issues = 0
        
        # Check if we should increase depth in this category
        for category in hypothesis.target_invariant_categories:
            stats = self._state.category_stats[category]
            if stats.signal_rate > self.SIGNAL_THRESHOLD_FOR_DEPTH:
                logger.info(f"High signal rate in {category}, increasing depth")
                return ExplorationAdjustment.INCREASE_DEPTH
        
        return ExplorationAdjustment.CONTINUE
    
    def _react_to_no_issue(
        self, 
        hypothesis: Hypothesis, 
        classification: MCPClassification
    ) -> ExplorationAdjustment:
        """React to MCP NO_ISSUE classification.
        
        NO_ISSUE means MCP determined this is not a security issue.
        We deprioritize similar hypotheses.
        """
        logger.debug(f"MCP classified {hypothesis.id} as NO_ISSUE")
        
        # Increment consecutive no-issues counter
        self._state.consecutive_no_issues += 1
        
        # Check for stop-loss conditions
        if self._state.consecutive_no_issues >= self.CONSECUTIVE_NO_ISSUE_LIMIT:
            logger.info("Consecutive NO_ISSUE limit reached, applying stop-loss")
            return ExplorationAdjustment.STOP_CATEGORY
        
        # Check category-level stop-loss
        for category in hypothesis.target_invariant_categories:
            stats = self._state.category_stats[category]
            if stats.no_issue_rate > self.NO_ISSUE_THRESHOLD_FOR_STOP and stats.total_tested > 5:
                logger.info(f"High NO_ISSUE rate in {category}, stopping category")
                return ExplorationAdjustment.STOP_CATEGORY
        
        return ExplorationAdjustment.DEPRIORITIZE
    
    def _react_to_coverage_gap(
        self, 
        hypothesis: Hypothesis, 
        classification: MCPClassification
    ) -> ExplorationAdjustment:
        """React to MCP COVERAGE_GAP classification.
        
        CRITICAL: COVERAGE_GAP is NOT a finding.
        It means MCP couldn't validate due to incomplete invariant coverage.
        We log it but do NOT claim it as a bug.
        """
        logger.info(
            f"MCP reported COVERAGE_GAP for {hypothesis.id}: {classification.coverage_gaps}"
        )
        
        # IMPORTANT: We do NOT interpret this as a finding
        # We just continue exploring other hypotheses
        return ExplorationAdjustment.CONTINUE
    
    def _update_stats(
        self, 
        hypothesis: Hypothesis, 
        classification: MCPClassification
    ) -> None:
        """Update statistics based on classification."""
        self._state.total_classifications += 1
        
        for category in hypothesis.target_invariant_categories:
            stats = self._state.category_stats[category]
            stats.total_tested += 1
            
            if classification.is_bug():
                stats.bugs += 1
            elif classification.is_signal():
                stats.signals += 1
            elif classification.is_no_issue():
                stats.no_issues += 1
            elif classification.is_coverage_gap():
                stats.coverage_gaps += 1
    
    def should_continue_category(self, category: str) -> bool:
        """Determine if exploration should continue in a category.
        
        Args:
            category: The invariant category to check
            
        Returns:
            True if exploration should continue, False if stop-loss triggered
        """
        stats = self._state.category_stats.get(category)
        
        if stats is None:
            return True  # No data yet, continue exploring
        
        # Stop if high NO_ISSUE rate and enough samples
        if stats.no_issue_rate > self.NO_ISSUE_THRESHOLD_FOR_STOP and stats.total_tested > 5:
            return False
        
        return True
    
    def apply_stop_loss(self, exploration_stats: ExplorationStats) -> bool:
        """Apply stop-loss rules for diminishing returns.
        
        Args:
            exploration_stats: Current exploration statistics
            
        Returns:
            True if stop-loss should be applied (stop exploration)
        """
        # Stop if too many consecutive NO_ISSUE classifications
        if self._state.consecutive_no_issues >= self.CONSECUTIVE_NO_ISSUE_LIMIT:
            logger.info("Stop-loss triggered: consecutive NO_ISSUE limit")
            return True
        
        # Stop if overall NO_ISSUE rate is too high
        total = self._state.total_classifications
        if total > 10:
            total_no_issues = sum(
                s.no_issues for s in self._state.category_stats.values()
            )
            if total_no_issues / total > self.NO_ISSUE_THRESHOLD_FOR_STOP:
                logger.info("Stop-loss triggered: high overall NO_ISSUE rate")
                return True
        
        return False
    
    def get_category_stats(self, category: str) -> Optional[CategoryStats]:
        """Get statistics for a specific category."""
        return self._state.category_stats.get(category)
    
    def reset(self) -> None:
        """Reset feedback state."""
        self._state = FeedbackState()
