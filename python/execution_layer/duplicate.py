"""
Execution Layer Duplicate Handler

Advisory duplicate handling with exploration STOP conditions.
Duplicate handling is advisory, not automatic.

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Any
import secrets

from execution_layer.types import (
    DuplicateExplorationConfig,
    SafeAction,
)
from execution_layer.errors import DuplicateExplorationLimitError


@dataclass
class DuplicateCandidate:
    """Potential duplicate finding."""
    candidate_id: str
    original_finding_id: str
    similarity_score: float  # NOT confidence — just similarity metric
    comparison_details: dict[str, Any]
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ExplorationState:
    """State of duplicate exploration."""
    exploration_id: str
    original_finding_id: str
    current_depth: int = 0
    hypotheses_generated: int = 0
    total_actions: int = 0
    hypotheses: list[dict[str, Any]] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    stopped: bool = False
    stop_reason: Optional[str] = None


class DuplicateHandler:
    """Handles duplicate detection and exploration.
    
    RULES:
    - Duplicate handling is ADVISORY only
    - Human decision required for duplicate confirmation
    - Exploration has STOP conditions:
      - max_depth: Maximum exploration depth
      - max_hypotheses: Maximum hypotheses to generate
      - max_total_actions: Maximum total actions
    """
    
    def __init__(
        self,
        config: Optional[DuplicateExplorationConfig] = None,
    ) -> None:
        self._config = config or DuplicateExplorationConfig()
        self._candidates: dict[str, DuplicateCandidate] = {}
        self._explorations: dict[str, ExplorationState] = {}
        self._human_decisions: dict[str, bool] = {}  # finding_id -> is_duplicate
    
    @property
    def config(self) -> DuplicateExplorationConfig:
        return self._config
    
    def detect_duplicate(
        self,
        finding_id: str,
        finding_data: dict[str, Any],
        existing_findings: list[dict[str, Any]],
    ) -> Optional[DuplicateCandidate]:
        """Detect if finding is a potential duplicate.
        
        Returns:
            DuplicateCandidate if potential duplicate found, None otherwise
        """
        for existing in existing_findings:
            similarity = self._compute_similarity(finding_data, existing)
            if similarity >= 0.8:  # High similarity threshold
                candidate = DuplicateCandidate(
                    candidate_id=secrets.token_urlsafe(16),
                    original_finding_id=existing.get("finding_id", ""),
                    similarity_score=similarity,
                    comparison_details={
                        "new_finding": finding_id,
                        "existing_finding": existing.get("finding_id"),
                        "similarity": similarity,
                    },
                )
                self._candidates[candidate.candidate_id] = candidate
                return candidate
        
        return None

    def start_exploration(
        self,
        finding_id: str,
    ) -> ExplorationState:
        """Start duplicate exploration for a finding."""
        exploration_id = secrets.token_urlsafe(16)
        state = ExplorationState(
            exploration_id=exploration_id,
            original_finding_id=finding_id,
        )
        self._explorations[exploration_id] = state
        return state
    
    def generate_hypothesis(
        self,
        exploration_id: str,
        hypothesis_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a new hypothesis for exploration.
        
        Raises:
            DuplicateExplorationLimitError: If max_hypotheses exceeded
        """
        state = self._get_exploration(exploration_id)
        
        # Check STOP condition: max_hypotheses
        if state.hypotheses_generated >= self._config.max_hypotheses:
            state.stopped = True
            state.stop_reason = f"max_hypotheses ({self._config.max_hypotheses}) exceeded"
            raise DuplicateExplorationLimitError(
                f"Maximum hypotheses ({self._config.max_hypotheses}) exceeded — "
                f"STOP exploration"
            )
        
        hypothesis = {
            "hypothesis_id": secrets.token_urlsafe(8),
            "exploration_id": exploration_id,
            "data": hypothesis_data,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        state.hypotheses.append(hypothesis)
        state.hypotheses_generated += 1
        
        return hypothesis
    
    def record_action(
        self,
        exploration_id: str,
        action: SafeAction,
    ) -> None:
        """Record an action in exploration.
        
        Raises:
            DuplicateExplorationLimitError: If max_total_actions exceeded
        """
        state = self._get_exploration(exploration_id)
        
        # Check STOP condition: max_total_actions
        if state.total_actions >= self._config.max_total_actions:
            state.stopped = True
            state.stop_reason = f"max_total_actions ({self._config.max_total_actions}) exceeded"
            raise DuplicateExplorationLimitError(
                f"Maximum total actions ({self._config.max_total_actions}) exceeded — "
                f"STOP exploration"
            )
        
        state.total_actions += 1
    
    def increment_depth(self, exploration_id: str) -> int:
        """Increment exploration depth.
        
        Raises:
            DuplicateExplorationLimitError: If max_depth exceeded
        """
        state = self._get_exploration(exploration_id)
        
        # Check STOP condition: max_depth
        if state.current_depth >= self._config.max_depth:
            state.stopped = True
            state.stop_reason = f"max_depth ({self._config.max_depth}) exceeded"
            raise DuplicateExplorationLimitError(
                f"Maximum depth ({self._config.max_depth}) exceeded — "
                f"STOP exploration"
            )
        
        state.current_depth += 1
        return state.current_depth
    
    def record_human_decision(
        self,
        finding_id: str,
        is_duplicate: bool,
    ) -> None:
        """Record human decision on duplicate status."""
        self._human_decisions[finding_id] = is_duplicate
    
    def get_human_decision(self, finding_id: str) -> Optional[bool]:
        """Get human decision for finding if it exists."""
        return self._human_decisions.get(finding_id)
    
    def is_exploration_stopped(self, exploration_id: str) -> bool:
        """Check if exploration has been stopped."""
        state = self._explorations.get(exploration_id)
        return state.stopped if state else True
    
    def get_exploration(self, exploration_id: str) -> Optional[ExplorationState]:
        """Get exploration state."""
        return self._explorations.get(exploration_id)
    
    def _get_exploration(self, exploration_id: str) -> ExplorationState:
        """Get exploration state or raise error."""
        state = self._explorations.get(exploration_id)
        if state is None:
            raise ValueError(f"No exploration with ID '{exploration_id}'")
        if state.stopped:
            raise DuplicateExplorationLimitError(
                f"Exploration '{exploration_id}' has been stopped: {state.stop_reason}"
            )
        return state
    
    def _compute_similarity(
        self,
        finding1: dict[str, Any],
        finding2: dict[str, Any],
    ) -> float:
        """Compute similarity between two findings.
        
        This is a simple similarity metric, NOT confidence scoring.
        """
        # Simple field-based similarity
        common_fields = set(finding1.keys()) & set(finding2.keys())
        if not common_fields:
            return 0.0
        
        matches = 0
        for field in common_fields:
            if finding1.get(field) == finding2.get(field):
                matches += 1
        
        return matches / len(common_fields)
