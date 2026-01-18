"""
Phase-10: Governance & Friction Layer - Rubber-Stamp Detector

Identifies patterns of hasty confirmation.
ADVISORY ONLY - does NOT block decisions.
"""

import time
from collections import defaultdict
from typing import Dict, List, Optional

from governance_friction.types import (
    RubberStampWarning,
    WarningLevel,
    MIN_DECISIONS_FOR_ANALYSIS,
)


class RubberStampDetector:
    """
    Detects patterns of hasty confirmation (rubber-stamping).
    
    SECURITY: This detector WARNS only. It NEVER:
    - Blocks confirmations
    - Auto-rejects flagged items
    - Makes decisions for humans
    
    IMPORTANT: Detection is ADVISORY only.
    
    Cold-start safety: Reviewers with < MIN_DECISIONS_FOR_ANALYSIS
    decisions receive NO warnings.
    """
    
    # Thresholds for detection
    RAPID_SUCCESSION_THRESHOLD_SECONDS = 10.0
    RAPID_SUCCESSION_COUNT = 3
    PERCENTILE_THRESHOLD = 10  # Below 10th percentile is flagged
    
    def __init__(self):
        """Initialize the rubber-stamp detector."""
        # reviewer_id -> list of (timestamp, deliberation_seconds)
        self._reviewer_history: Dict[str, List[tuple]] = defaultdict(list)
    
    def record_confirmation(
        self,
        reviewer_id: str,
        decision_id: str,
        deliberation_seconds: float,
    ) -> None:
        """
        Record a confirmation for pattern analysis.
        
        Args:
            reviewer_id: ID of the reviewer
            decision_id: ID of the decision
            deliberation_seconds: Time spent deliberating
        """
        timestamp = time.monotonic()
        self._reviewer_history[reviewer_id].append(
            (timestamp, deliberation_seconds)
        )
    
    def analyze_pattern(
        self,
        reviewer_id: str,
    ) -> RubberStampWarning:
        """
        Analyze a reviewer's confirmation patterns.
        
        Args:
            reviewer_id: ID of the reviewer
            
        Returns:
            RubberStampWarning (ADVISORY ONLY)
        """
        history = self._reviewer_history.get(reviewer_id, [])
        decision_count = len(history)
        
        # Cold-start safety: No warnings for new reviewers
        if decision_count < MIN_DECISIONS_FOR_ANALYSIS:
            return RubberStampWarning(
                reviewer_id=reviewer_id,
                warning_level=WarningLevel.NONE,
                reason="Insufficient history for analysis",
                decision_count=decision_count,
                approval_rate=0.0,
                average_deliberation_seconds=0.0,
                is_cold_start=True,
            )
        
        # Calculate statistics
        deliberation_times = [d for _, d in history]
        avg_deliberation = sum(deliberation_times) / len(deliberation_times)
        
        # Check for rapid succession
        rapid_succession = self._detect_rapid_succession(history)
        
        # Check for below-percentile deliberation
        below_percentile = self._detect_below_percentile(history)
        
        # Determine warning level
        warning_level = WarningLevel.NONE
        reason = "No concerning patterns detected"
        
        if rapid_succession and below_percentile:
            warning_level = WarningLevel.HIGH
            reason = "Rapid succession AND below-average deliberation detected"
        elif rapid_succession:
            warning_level = WarningLevel.MEDIUM
            reason = f"Rapid succession detected: {self.RAPID_SUCCESSION_COUNT}+ confirmations in < {self.RAPID_SUCCESSION_THRESHOLD_SECONDS}s"
        elif below_percentile:
            warning_level = WarningLevel.LOW
            reason = f"Deliberation time below {self.PERCENTILE_THRESHOLD}th percentile"
        
        return RubberStampWarning(
            reviewer_id=reviewer_id,
            warning_level=warning_level,
            reason=reason,
            decision_count=decision_count,
            approval_rate=1.0,  # All recorded are approvals
            average_deliberation_seconds=avg_deliberation,
            is_cold_start=False,
        )
    
    def _detect_rapid_succession(
        self,
        history: List[tuple],
    ) -> bool:
        """
        Detect rapid succession pattern.
        
        Args:
            history: List of (timestamp, deliberation_seconds)
            
        Returns:
            True if rapid succession detected
        """
        if len(history) < self.RAPID_SUCCESSION_COUNT:
            return False
        
        # Check last N confirmations
        recent = history[-self.RAPID_SUCCESSION_COUNT:]
        timestamps = [t for t, _ in recent]
        
        # Check if all within threshold
        time_span = timestamps[-1] - timestamps[0]
        return time_span < self.RAPID_SUCCESSION_THRESHOLD_SECONDS
    
    def _detect_below_percentile(
        self,
        history: List[tuple],
    ) -> bool:
        """
        Detect below-percentile deliberation.
        
        Args:
            history: List of (timestamp, deliberation_seconds)
            
        Returns:
            True if recent deliberation is below threshold percentile
        """
        if len(history) < 2:
            return False
        
        deliberation_times = sorted([d for _, d in history])
        
        # Calculate percentile threshold
        percentile_index = max(0, int(len(deliberation_times) * self.PERCENTILE_THRESHOLD / 100))
        threshold = deliberation_times[percentile_index]
        
        # Check if most recent is below threshold
        _, recent_deliberation = history[-1]
        return recent_deliberation < threshold
    
    def get_reviewer_statistics(
        self,
        reviewer_id: str,
    ) -> Dict[str, float]:
        """
        Get statistics for a reviewer.
        
        Args:
            reviewer_id: ID of the reviewer
            
        Returns:
            Dictionary of statistics
        """
        history = self._reviewer_history.get(reviewer_id, [])
        
        if not history:
            return {
                "decision_count": 0,
                "average_deliberation": 0.0,
                "min_deliberation": 0.0,
                "max_deliberation": 0.0,
            }
        
        deliberation_times = [d for _, d in history]
        
        return {
            "decision_count": len(history),
            "average_deliberation": sum(deliberation_times) / len(deliberation_times),
            "min_deliberation": min(deliberation_times),
            "max_deliberation": max(deliberation_times),
        }
    
    def clear_history(self, reviewer_id: str) -> None:
        """
        Clear history for a reviewer.
        
        Args:
            reviewer_id: ID of the reviewer
        """
        self._reviewer_history.pop(reviewer_id, None)
