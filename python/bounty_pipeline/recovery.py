"""
Recovery Manager - Handles failures gracefully without losing work.

This module manages state persistence and recovery for the pipeline.

CRITICAL CONSTRAINTS:
- Preserve drafts on submission failure
- Save state on interrupted reviews
- Queue actions when network unavailable
- Alert human when recovery fails
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional
import hashlib
import json


from bounty_pipeline.errors import RecoveryError


class ActionType(str, Enum):
    """Types of pending actions."""

    SUBMIT = "submit"
    UPDATE_STATUS = "update_status"
    RETRY_SUBMISSION = "retry_submission"
    NOTIFY_HUMAN = "notify_human"


class ActionStatus(str, Enum):
    """Status of a pending action."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PendingAction:
    """An action queued for later execution."""

    action_id: str
    action_type: ActionType
    payload: dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: ActionStatus = ActionStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    last_error: Optional[str] = None
    last_attempt_at: Optional[datetime] = None

    @property
    def can_retry(self) -> bool:
        """Check if action can be retried."""
        return (
            self.retry_count < self.max_retries
            and self.status in (ActionStatus.PENDING, ActionStatus.FAILED)
        )


@dataclass
class ActionResult:
    """Result of processing a pending action."""

    action_id: str
    success: bool
    message: str
    processed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error: Optional[str] = None


@dataclass
class PipelineState:
    """Serializable pipeline state for recovery."""

    state_id: str
    created_at: datetime
    pending_drafts: list[dict[str, Any]]
    pending_reviews: list[dict[str, Any]]
    pending_submissions: list[dict[str, Any]]
    audit_records: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            "state_id": self.state_id,
            "created_at": self.created_at.isoformat(),
            "pending_drafts": self.pending_drafts,
            "pending_reviews": self.pending_reviews,
            "pending_submissions": self.pending_submissions,
            "audit_records": self.audit_records,
            "metadata": self.metadata,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "PipelineState":
        """Create state from dictionary."""
        return PipelineState(
            state_id=data["state_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            pending_drafts=data.get("pending_drafts", []),
            pending_reviews=data.get("pending_reviews", []),
            pending_submissions=data.get("pending_submissions", []),
            audit_records=data.get("audit_records", []),
            metadata=data.get("metadata", {}),
        )

    def compute_hash(self) -> str:
        """Compute hash of state for integrity verification."""
        content = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


class RecoveryManager:
    """
    Manages state persistence and recovery.

    Features:
    - Preserves drafts on submission failure
    - Saves state on interrupted reviews
    - Recovers pending work from persistent storage
    - Queues actions when network unavailable
    - Alerts human when recovery fails
    """

    def __init__(self) -> None:
        """Initialize recovery manager."""
        self._saved_states: dict[str, PipelineState] = {}
        self._pending_actions: dict[str, PendingAction] = {}
        self._action_counter = 0
        self._state_counter = 0
        self._human_alerts: list[dict[str, Any]] = []
        self._action_handlers: dict[ActionType, Callable[[PendingAction], ActionResult]] = {}

    def save_state(self, state: PipelineState) -> str:
        """
        Save current state to persistent storage.

        Args:
            state: Pipeline state to save

        Returns:
            State ID for later recovery
        """
        self._saved_states[state.state_id] = state
        return state.state_id

    def create_state(
        self,
        pending_drafts: Optional[list[dict[str, Any]]] = None,
        pending_reviews: Optional[list[dict[str, Any]]] = None,
        pending_submissions: Optional[list[dict[str, Any]]] = None,
        audit_records: Optional[list[dict[str, Any]]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> PipelineState:
        """
        Create a new pipeline state.

        Args:
            pending_drafts: Drafts awaiting review
            pending_reviews: Reviews in progress
            pending_submissions: Submissions in progress
            audit_records: Audit trail records
            metadata: Additional metadata

        Returns:
            New PipelineState object
        """
        self._state_counter += 1
        state_id = f"state-{self._state_counter:06d}"

        return PipelineState(
            state_id=state_id,
            created_at=datetime.now(timezone.utc),
            pending_drafts=pending_drafts or [],
            pending_reviews=pending_reviews or [],
            pending_submissions=pending_submissions or [],
            audit_records=audit_records or [],
            metadata=metadata or {},
        )

    def recover_state(self, state_id: Optional[str] = None) -> Optional[PipelineState]:
        """
        Recover state from persistent storage.

        Args:
            state_id: Specific state to recover, or None for latest

        Returns:
            Recovered PipelineState or None if not found
        """
        if state_id:
            return self._saved_states.get(state_id)

        # Return most recent state
        if not self._saved_states:
            return None

        return max(
            self._saved_states.values(),
            key=lambda s: s.created_at,
        )

    def get_all_states(self) -> list[PipelineState]:
        """Get all saved states."""
        return list(self._saved_states.values())

    def queue_action(
        self,
        action_type: ActionType,
        payload: dict[str, Any],
        max_retries: int = 3,
    ) -> PendingAction:
        """
        Queue action for later execution.

        Args:
            action_type: Type of action
            payload: Action payload
            max_retries: Maximum retry attempts

        Returns:
            PendingAction object
        """
        self._action_counter += 1
        action_id = f"action-{self._action_counter:06d}"

        action = PendingAction(
            action_id=action_id,
            action_type=action_type,
            payload=payload,
            max_retries=max_retries,
        )

        self._pending_actions[action_id] = action
        return action

    def get_pending_actions(self) -> list[PendingAction]:
        """Get all pending actions."""
        return [
            a for a in self._pending_actions.values()
            if a.status in (ActionStatus.PENDING, ActionStatus.FAILED) and a.can_retry
        ]

    def get_action(self, action_id: str) -> Optional[PendingAction]:
        """Get a specific action by ID."""
        return self._pending_actions.get(action_id)

    def register_handler(
        self,
        action_type: ActionType,
        handler: Callable[[PendingAction], ActionResult],
    ) -> None:
        """
        Register a handler for an action type.

        Args:
            action_type: Type of action to handle
            handler: Function to process the action
        """
        self._action_handlers[action_type] = handler

    def process_action(self, action_id: str) -> ActionResult:
        """
        Process a single pending action.

        Args:
            action_id: ID of action to process

        Returns:
            ActionResult with outcome

        Raises:
            ValueError: If action not found
            RecoveryError: If no handler registered
        """
        if action_id not in self._pending_actions:
            raise ValueError(f"Action not found: {action_id}")

        action = self._pending_actions[action_id]

        if action.action_type not in self._action_handlers:
            raise RecoveryError(
                f"No handler registered for action type: {action.action_type}"
            )

        action.status = ActionStatus.IN_PROGRESS
        action.last_attempt_at = datetime.now(timezone.utc)
        action.retry_count += 1

        try:
            handler = self._action_handlers[action.action_type]
            result = handler(action)

            if result.success:
                action.status = ActionStatus.COMPLETED
            else:
                action.status = ActionStatus.FAILED
                action.last_error = result.error

            return result

        except Exception as e:
            action.status = ActionStatus.FAILED
            action.last_error = str(e)

            return ActionResult(
                action_id=action_id,
                success=False,
                message=f"Action failed: {e}",
                error=str(e),
            )

    def process_queue(self) -> list[ActionResult]:
        """
        Process all pending actions.

        Returns:
            List of ActionResult objects
        """
        results = []
        pending = self.get_pending_actions()

        for action in pending:
            try:
                result = self.process_action(action.action_id)
                results.append(result)
            except (ValueError, RecoveryError) as e:
                results.append(ActionResult(
                    action_id=action.action_id,
                    success=False,
                    message=str(e),
                    error=str(e),
                ))

        return results

    def alert_human(
        self,
        error: Exception,
        diagnostic: dict[str, Any],
        severity: str = "error",
    ) -> None:
        """
        Alert human operator of recovery failure.

        Args:
            error: The exception that occurred
            diagnostic: Diagnostic information
            severity: Alert severity (info, warning, error, critical)
        """
        alert = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": severity,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "diagnostic": diagnostic,
        }

        self._human_alerts.append(alert)

    def get_alerts(self) -> list[dict[str, Any]]:
        """Get all human alerts."""
        return list(self._human_alerts)

    def clear_alerts(self) -> int:
        """Clear all alerts and return count cleared."""
        count = len(self._human_alerts)
        self._human_alerts.clear()
        return count

    def cleanup_completed(self) -> int:
        """
        Remove completed actions from queue.

        Returns:
            Number of actions removed
        """
        completed = [
            action_id
            for action_id, action in self._pending_actions.items()
            if action.status == ActionStatus.COMPLETED
        ]

        for action_id in completed:
            del self._pending_actions[action_id]

        return len(completed)

    @property
    def pending_count(self) -> int:
        """Get number of pending actions."""
        return len(self.get_pending_actions())

    @property
    def alert_count(self) -> int:
        """Get number of uncleared alerts."""
        return len(self._human_alerts)
