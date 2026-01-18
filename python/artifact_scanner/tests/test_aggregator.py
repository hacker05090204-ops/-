"""
Phase-5 Signal Aggregator Tests

Tests for signal aggregation.
Validates:
- Property 4: Signal Grouping Completeness

All tests use synthetic data (no real Phase-4 artifacts).
"""

import pytest
from hypothesis import given, strategies as st

from artifact_scanner.aggregator import SignalAggregator
from artifact_scanner.types import Signal, SignalType


# =============================================================================
# Test Fixtures
# =============================================================================

def make_signal(
    signal_type: SignalType = SignalType.SENSITIVE_DATA,
    endpoint: str = None,
    source_artifact: str = "test.har",
) -> Signal:
    """Helper to create signal."""
    return Signal.create(
        signal_type=signal_type,
        source_artifact=source_artifact,
        description="Test signal",
        evidence={"key": "value"},
        endpoint=endpoint,
    )


# =============================================================================
# Property 4: Signal Grouping Completeness
# =============================================================================

class TestSignalGroupingCompleteness:
    """Property 4: All signals with same endpoint are in same FindingCandidate."""
    
    def test_signals_grouped_by_endpoint(self):
        """Signals with same endpoint are grouped together."""
        signals = [
            make_signal(endpoint="https://example.com/api"),
            make_signal(endpoint="https://example.com/api"),
            make_signal(endpoint="https://example.com/other"),
        ]
        aggregator = SignalAggregator()
        
        candidates = aggregator.aggregate(signals)
        
        # Should have 2 candidates (2 unique endpoints)
        assert len(candidates) == 2
        
        # Find the candidate for /api endpoint
        api_candidate = next(
            c for c in candidates
            if c.endpoint == "https://example.com/api"
        )
        assert len(api_candidate.signals) == 2
    
    def test_all_signals_for_endpoint_included(self):
        """All signals for an endpoint are included in its FindingCandidate."""
        endpoint = "https://example.com/api"
        signals = [
            make_signal(signal_type=SignalType.SENSITIVE_DATA, endpoint=endpoint),
            make_signal(signal_type=SignalType.HEADER_MISCONFIG, endpoint=endpoint),
            make_signal(signal_type=SignalType.REFLECTION, endpoint=endpoint),
        ]
        aggregator = SignalAggregator()
        
        candidates = aggregator.aggregate(signals)
        
        assert len(candidates) == 1
        candidate = candidates[0]
        assert len(candidate.signals) == 3
        
        # Verify all signal types are present
        signal_types = {s.signal_type for s in candidate.signals}
        assert SignalType.SENSITIVE_DATA in signal_types
        assert SignalType.HEADER_MISCONFIG in signal_types
        assert SignalType.REFLECTION in signal_types
    
    def test_signals_without_endpoint_grouped_as_unknown(self):
        """Signals without endpoint are grouped under 'unknown'."""
        signals = [
            make_signal(endpoint=None),
            make_signal(endpoint=None),
        ]
        aggregator = SignalAggregator()
        
        candidates = aggregator.aggregate(signals)
        
        assert len(candidates) == 1
        assert candidates[0].endpoint == "unknown"
        assert len(candidates[0].signals) == 2
    
    def test_empty_signals_produces_no_candidates(self):
        """Empty signal list produces no candidates."""
        aggregator = SignalAggregator()
        
        candidates = aggregator.aggregate([])
        
        assert len(candidates) == 0


# =============================================================================
# Grouping Tests
# =============================================================================

class TestGroupByEndpoint:
    """Tests for group_by_endpoint method."""
    
    def test_group_by_endpoint_basic(self):
        """Basic grouping by endpoint."""
        signals = [
            make_signal(endpoint="https://a.com"),
            make_signal(endpoint="https://b.com"),
            make_signal(endpoint="https://a.com"),
        ]
        aggregator = SignalAggregator()
        
        grouped = aggregator.group_by_endpoint(signals)
        
        assert len(grouped) == 2
        assert len(grouped["https://a.com"]) == 2
        assert len(grouped["https://b.com"]) == 1
    
    def test_group_preserves_signal_order(self):
        """Grouping preserves signal order within groups."""
        signals = [
            make_signal(signal_type=SignalType.SENSITIVE_DATA, endpoint="https://a.com"),
            make_signal(signal_type=SignalType.HEADER_MISCONFIG, endpoint="https://a.com"),
        ]
        aggregator = SignalAggregator()
        
        grouped = aggregator.group_by_endpoint(signals)
        
        assert grouped["https://a.com"][0].signal_type == SignalType.SENSITIVE_DATA
        assert grouped["https://a.com"][1].signal_type == SignalType.HEADER_MISCONFIG


# =============================================================================
# FindingCandidate Creation Tests
# =============================================================================

class TestFindingCandidateCreation:
    """Tests for FindingCandidate creation during aggregation."""
    
    def test_candidate_includes_artifact_references(self):
        """FindingCandidate includes all artifact references from signals."""
        signals = [
            make_signal(endpoint="https://a.com", source_artifact="file1.har"),
            make_signal(endpoint="https://a.com", source_artifact="file2.har"),
            make_signal(endpoint="https://a.com", source_artifact="file1.har"),  # Duplicate
        ]
        aggregator = SignalAggregator()
        
        candidates = aggregator.aggregate(signals)
        
        assert len(candidates) == 1
        # Should have unique artifact references
        assert set(candidates[0].artifact_references) == {"file1.har", "file2.har"}
    
    def test_candidate_has_none_forbidden_fields(self):
        """FindingCandidate has None for forbidden fields."""
        signals = [make_signal(endpoint="https://a.com")]
        aggregator = SignalAggregator()
        
        candidates = aggregator.aggregate(signals)
        
        assert len(candidates) == 1
        assert candidates[0].severity is None
        assert candidates[0].classification is None
        assert candidates[0].confidence is None
