"""
Phase-5 Trace Analyzer Tests

Tests for execution trace analysis.
All tests use synthetic data (no real Phase-4 artifacts).
"""

import pytest
from datetime import datetime, timezone, timedelta

from artifact_scanner.analyzers.trace import TraceAnalyzer, ActionSequence
from artifact_scanner.loader import ExecutionTrace, TraceAction
from artifact_scanner.types import SignalType


# =============================================================================
# Test Fixtures
# =============================================================================

def make_action(
    action_id: str = "a1",
    action_type: str = "click",
    target: str = "#button",
    outcome: str = "success",
    error: str = None,
    timestamp: datetime = None,
) -> TraceAction:
    """Helper to create trace action."""
    return TraceAction(
        action_id=action_id,
        action_type=action_type,
        target=target,
        parameters={},
        outcome=outcome,
        error=error,
        timestamp=timestamp,
    )


def make_trace(execution_id: str, actions: list[TraceAction]) -> ExecutionTrace:
    """Helper to create execution trace."""
    return ExecutionTrace(
        execution_id=execution_id,
        actions=actions,
    )


# =============================================================================
# Sequence Reconstruction Tests
# =============================================================================

class TestSequenceReconstruction:
    """Tests for action sequence reconstruction."""
    
    def test_reconstruct_preserves_order(self):
        """Reconstruct preserves action order when no timestamps."""
        actions = [
            make_action(action_id="a1", action_type="navigate"),
            make_action(action_id="a2", action_type="click"),
            make_action(action_id="a3", action_type="input_text"),
        ]
        trace = make_trace("exec-1", actions)
        analyzer = TraceAnalyzer("trace.json")
        
        sequence = analyzer.reconstruct_sequence(trace)
        
        assert len(sequence.actions) == 3
        assert sequence.actions[0].action_id == "a1"
        assert sequence.actions[1].action_id == "a2"
        assert sequence.actions[2].action_id == "a3"
    
    def test_reconstruct_sorts_by_timestamp(self):
        """Reconstruct sorts actions by timestamp when available."""
        now = datetime.now(timezone.utc)
        actions = [
            make_action(action_id="a3", timestamp=now + timedelta(seconds=2)),
            make_action(action_id="a1", timestamp=now),
            make_action(action_id="a2", timestamp=now + timedelta(seconds=1)),
        ]
        trace = make_trace("exec-1", actions)
        analyzer = TraceAnalyzer("trace.json")
        
        sequence = analyzer.reconstruct_sequence(trace)
        
        assert sequence.actions[0].action_id == "a1"
        assert sequence.actions[1].action_id == "a2"
        assert sequence.actions[2].action_id == "a3"
    
    def test_sequence_counts_successes_and_failures(self):
        """ActionSequence correctly counts successes and failures."""
        actions = [
            make_action(action_id="a1", outcome="success"),
            make_action(action_id="a2", outcome="failed"),
            make_action(action_id="a3", outcome="success"),
            make_action(action_id="a4", outcome="error"),
        ]
        trace = make_trace("exec-1", actions)
        analyzer = TraceAnalyzer("trace.json")
        
        sequence = analyzer.reconstruct_sequence(trace)
        
        assert sequence.success_count == 2
        assert sequence.failure_count == 2


# =============================================================================
# State Anomaly Detection Tests
# =============================================================================

class TestStateAnomalyDetection:
    """Tests for state anomaly detection."""
    
    def test_detects_high_failure_rate(self):
        """Detect high action failure rate (>50%)."""
        actions = [
            make_action(action_id="a1", outcome="failed"),
            make_action(action_id="a2", outcome="failed"),
            make_action(action_id="a3", outcome="failed"),
            make_action(action_id="a4", outcome="success"),
        ]
        sequence = ActionSequence(execution_id="exec-1", actions=actions)
        analyzer = TraceAnalyzer("trace.json")
        
        signals = analyzer.detect_state_anomalies(sequence)
        
        assert any(
            "failure rate" in s.description.lower()
            for s in signals
        )
    
    def test_no_signal_for_low_failure_rate(self):
        """No signal for low failure rate (<50%)."""
        actions = [
            make_action(action_id="a1", outcome="success"),
            make_action(action_id="a2", outcome="success"),
            make_action(action_id="a3", outcome="success"),
            make_action(action_id="a4", outcome="failed"),
        ]
        sequence = ActionSequence(execution_id="exec-1", actions=actions)
        analyzer = TraceAnalyzer("trace.json")
        
        signals = analyzer.detect_state_anomalies(sequence)
        
        assert not any(
            "failure rate" in s.description.lower()
            for s in signals
        )
    
    def test_detects_repeated_failures_on_target(self):
        """Detect repeated failures on same target."""
        actions = [
            make_action(action_id="a1", target="#submit", outcome="failed"),
            make_action(action_id="a2", target="#submit", outcome="failed"),
            make_action(action_id="a3", target="#submit", outcome="failed"),
        ]
        sequence = ActionSequence(execution_id="exec-1", actions=actions)
        analyzer = TraceAnalyzer("trace.json")
        
        signals = analyzer.detect_state_anomalies(sequence)
        
        assert any(
            "repeated failures" in s.description.lower()
            for s in signals
        )
    
    def test_detects_unexpected_sequence(self):
        """Detect action after failed action."""
        actions = [
            make_action(action_id="a1", action_type="click", outcome="failed"),
            make_action(action_id="a2", action_type="input_text", outcome="success"),
        ]
        sequence = ActionSequence(execution_id="exec-1", actions=actions)
        analyzer = TraceAnalyzer("trace.json")
        
        signals = analyzer.detect_state_anomalies(sequence)
        
        assert any(
            "unexpected" in s.description.lower()
            for s in signals
        )
    
    def test_no_unexpected_sequence_for_wait_after_failure(self):
        """Wait after failure is not unexpected."""
        actions = [
            make_action(action_id="a1", action_type="click", outcome="failed"),
            make_action(action_id="a2", action_type="wait", outcome="success"),
        ]
        sequence = ActionSequence(execution_id="exec-1", actions=actions)
        analyzer = TraceAnalyzer("trace.json")
        
        signals = analyzer.detect_state_anomalies(sequence)
        
        assert not any(
            "unexpected" in s.description.lower()
            for s in signals
        )


# =============================================================================
# Full Analysis Tests
# =============================================================================

class TestFullAnalysis:
    """Tests for full trace analysis."""
    
    def test_analyze_includes_error_context(self):
        """Analysis includes error context for failed actions."""
        actions = [
            make_action(
                action_id="a1",
                action_type="click",
                target="#missing",
                outcome="failed",
                error="Element not found: #missing",
            ),
        ]
        trace = make_trace("exec-1", actions)
        analyzer = TraceAnalyzer("trace.json")
        
        signals = analyzer.analyze(trace)
        
        assert any(
            s.evidence.get("error") == "Element not found: #missing"
            for s in signals
        )
    
    def test_analyze_empty_trace(self):
        """Analyze empty trace produces no signals."""
        trace = make_trace("exec-1", [])
        analyzer = TraceAnalyzer("trace.json")
        
        signals = analyzer.analyze(trace)
        
        assert len(signals) == 0
    
    def test_signals_include_source_artifact(self):
        """All signals include source artifact reference."""
        actions = [
            make_action(outcome="failed", error="Test error"),
        ]
        trace = make_trace("exec-1", actions)
        analyzer = TraceAnalyzer("exec-1/trace.json")
        
        signals = analyzer.analyze(trace)
        
        for signal in signals:
            assert signal.source_artifact == "exec-1/trace.json"
    
    def test_signals_have_none_forbidden_fields(self):
        """All signals have None for forbidden fields."""
        actions = [
            make_action(outcome="failed", error="Test error"),
        ]
        trace = make_trace("exec-1", actions)
        analyzer = TraceAnalyzer("trace.json")
        
        signals = analyzer.analyze(trace)
        
        for signal in signals:
            assert signal.severity is None
            assert signal.classification is None
            assert signal.confidence is None
