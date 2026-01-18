"""
Phase-5 Execution Trace Analyzer

Analyzes execution traces for behavioral patterns.

INVARIANTS:
- No actions replayed or re-executed
- No file modifications

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

from dataclasses import dataclass
from typing import Optional

from artifact_scanner.loader import ExecutionTrace, TraceAction
from artifact_scanner.types import Signal, SignalType


@dataclass
class ActionSequence:
    """Reconstructed action sequence from trace."""
    execution_id: str
    actions: list[TraceAction]
    
    @property
    def success_count(self) -> int:
        return sum(1 for a in self.actions if a.outcome == "success")
    
    @property
    def failure_count(self) -> int:
        return sum(1 for a in self.actions if a.outcome != "success")


class TraceAnalyzer:
    """Analyzes execution traces for behavioral patterns.
    
    INVARIANTS:
    - No actions replayed or re-executed
    - No file modifications
    """
    
    def __init__(self, source_artifact: str) -> None:
        """Initialize analyzer with source artifact path."""
        self._source_artifact = source_artifact
    
    def analyze(self, trace: ExecutionTrace) -> list[Signal]:
        """Extract signals from execution trace.
        
        Args:
            trace: Execution trace to analyze
        
        Returns:
            List of detected signals
        """
        signals: list[Signal] = []
        
        # Reconstruct action sequence
        sequence = self.reconstruct_sequence(trace)
        
        # Detect state anomalies
        anomaly_signals = self.detect_state_anomalies(sequence)
        signals.extend(anomaly_signals)
        
        # Include error context for failed actions
        for action in trace.actions:
            if action.outcome != "success" and action.error:
                signals.append(Signal.create(
                    signal_type=SignalType.STATE_ANOMALY,
                    source_artifact=self._source_artifact,
                    description=f"Action '{action.action_type}' failed with error",
                    evidence={
                        "action_id": action.action_id,
                        "action_type": action.action_type,
                        "target": action.target,
                        "error": action.error[:200] if action.error else None,
                        "outcome": action.outcome,
                    },
                ))
        
        return signals
    
    def reconstruct_sequence(self, trace: ExecutionTrace) -> ActionSequence:
        """Reconstruct action sequence from trace.
        
        Args:
            trace: Execution trace
        
        Returns:
            ActionSequence with ordered actions
        """
        # Sort by timestamp if available, otherwise preserve order
        actions = list(trace.actions)
        actions_with_ts = [(a, a.timestamp) for a in actions if a.timestamp]
        
        if actions_with_ts:
            actions_with_ts.sort(key=lambda x: x[1])
            sorted_actions = [a for a, _ in actions_with_ts]
            # Add actions without timestamps at the end
            sorted_actions.extend(a for a in actions if not a.timestamp)
            actions = sorted_actions
        
        return ActionSequence(
            execution_id=trace.execution_id,
            actions=actions,
        )
    
    def detect_state_anomalies(self, sequence: ActionSequence) -> list[Signal]:
        """Detect unexpected state changes.
        
        Args:
            sequence: Action sequence to analyze
        
        Returns:
            List of StateAnomalySignal instances
        """
        signals: list[Signal] = []
        
        # Detect high failure rate
        if sequence.actions:
            failure_rate = sequence.failure_count / len(sequence.actions)
            if failure_rate > 0.5:
                signals.append(Signal.create(
                    signal_type=SignalType.STATE_ANOMALY,
                    source_artifact=self._source_artifact,
                    description="High action failure rate detected",
                    evidence={
                        "execution_id": sequence.execution_id,
                        "total_actions": len(sequence.actions),
                        "failed_actions": sequence.failure_count,
                        "failure_rate": round(failure_rate, 2),
                    },
                ))
        
        # Detect repeated failures on same target
        target_failures: dict[str, int] = {}
        for action in sequence.actions:
            if action.outcome != "success":
                target_failures[action.target] = target_failures.get(action.target, 0) + 1
        
        for target, count in target_failures.items():
            if count >= 3:
                signals.append(Signal.create(
                    signal_type=SignalType.STATE_ANOMALY,
                    source_artifact=self._source_artifact,
                    description=f"Repeated failures on target: {target[:50]}",
                    evidence={
                        "execution_id": sequence.execution_id,
                        "target": target,
                        "failure_count": count,
                    },
                ))
        
        # Detect unexpected action sequences (e.g., click before navigate)
        prev_action = None
        for action in sequence.actions:
            if prev_action:
                if self._is_unexpected_sequence(prev_action, action):
                    signals.append(Signal.create(
                        signal_type=SignalType.STATE_ANOMALY,
                        source_artifact=self._source_artifact,
                        description="Unexpected action sequence detected",
                        evidence={
                            "execution_id": sequence.execution_id,
                            "previous_action": prev_action.action_type,
                            "current_action": action.action_type,
                            "previous_outcome": prev_action.outcome,
                        },
                    ))
            prev_action = action
        
        return signals
    
    def _is_unexpected_sequence(self, prev: TraceAction, curr: TraceAction) -> bool:
        """Check if action sequence is unexpected.
        
        Args:
            prev: Previous action
            curr: Current action
        
        Returns:
            True if sequence is unexpected
        """
        # Action after failed action (might indicate state issue)
        if prev.outcome != "success" and curr.action_type not in ("wait", "screenshot"):
            return True
        
        return False
