"""
Phase-5 Scanner Type Tests

Tests for Signal, FindingCandidate, and ScanResult data models.
Validates:
- Property 2: No Classification in Signals
- Property 3: No Classification in FindingCandidates
- Property 7: JSON Serialization Round-Trip

All tests use synthetic data (no real Phase-4 artifacts).
"""

import pytest
from datetime import datetime, timezone
from hypothesis import given, strategies as st

from artifact_scanner.types import (
    SignalType,
    Signal,
    FindingCandidate,
    ScanResult,
)


# =============================================================================
# Hypothesis Strategies for Synthetic Data
# =============================================================================

signal_type_strategy = st.sampled_from(list(SignalType))

evidence_strategy = st.fixed_dictionaries({
    "key": st.text(min_size=1, max_size=50),
    "value": st.text(min_size=0, max_size=100),
})

signal_strategy = st.builds(
    Signal.create,
    signal_type=signal_type_strategy,
    source_artifact=st.text(min_size=1, max_size=100).map(lambda s: f"artifacts/{s}.har"),
    description=st.text(min_size=1, max_size=200),
    evidence=evidence_strategy,
    endpoint=st.one_of(st.none(), st.text(min_size=1, max_size=100).map(lambda s: f"https://example.com/{s}")),
)


# =============================================================================
# Property 2: No Classification in Signals
# =============================================================================

class TestSignalForbiddenFields:
    """Property 2: For any Signal, severity/classification/confidence MUST be None."""
    
    @given(signal_strategy)
    def test_signal_forbidden_fields_are_none(self, signal: Signal) -> None:
        """Property: All forbidden fields are None."""
        assert signal.severity is None, "Signal.severity MUST be None"
        assert signal.classification is None, "Signal.classification MUST be None"
        assert signal.confidence is None, "Signal.confidence MUST be None"
    
    def test_signal_rejects_non_none_severity(self) -> None:
        """Attempting to set severity raises ValueError."""
        with pytest.raises(ValueError, match="severity MUST be None"):
            Signal(
                signal_id="test",
                signal_type=SignalType.SENSITIVE_DATA,
                source_artifact="test.har",
                description="test",
                evidence={},
                detected_at=datetime.now(timezone.utc),
                severity="HIGH",  # type: ignore - intentional violation
            )
    
    def test_signal_rejects_non_none_classification(self) -> None:
        """Attempting to set classification raises ValueError."""
        with pytest.raises(ValueError, match="classification MUST be None"):
            Signal(
                signal_id="test",
                signal_type=SignalType.SENSITIVE_DATA,
                source_artifact="test.har",
                description="test",
                evidence={},
                detected_at=datetime.now(timezone.utc),
                classification="XSS",  # type: ignore - intentional violation
            )
    
    def test_signal_rejects_non_none_confidence(self) -> None:
        """Attempting to set confidence raises ValueError."""
        with pytest.raises(ValueError, match="confidence MUST be None"):
            Signal(
                signal_id="test",
                signal_type=SignalType.SENSITIVE_DATA,
                source_artifact="test.har",
                description="test",
                evidence={},
                detected_at=datetime.now(timezone.utc),
                confidence=0.95,  # type: ignore - intentional violation
            )
    
    @given(signal_strategy)
    def test_signal_serialization_preserves_none_fields(self, signal: Signal) -> None:
        """Serialized signal explicitly includes None for forbidden fields."""
        data = signal.to_dict()
        assert data["severity"] is None
        assert data["classification"] is None
        assert data["confidence"] is None


# =============================================================================
# Property 3: No Classification in FindingCandidates
# =============================================================================

class TestFindingCandidateForbiddenFields:
    """Property 3: For any FindingCandidate, severity/classification/confidence MUST be None."""
    
    def test_finding_candidate_forbidden_fields_are_none(self) -> None:
        """Property: All forbidden fields are None."""
        signal = Signal.create(
            signal_type=SignalType.SENSITIVE_DATA,
            source_artifact="test.har",
            description="Test signal",
            evidence={"key": "value"},
            endpoint="https://example.com/api",
        )
        candidate = FindingCandidate.create(
            endpoint="https://example.com/api",
            signals=[signal],
        )
        
        assert candidate.severity is None, "FindingCandidate.severity MUST be None"
        assert candidate.classification is None, "FindingCandidate.classification MUST be None"
        assert candidate.confidence is None, "FindingCandidate.confidence MUST be None"
    
    def test_finding_candidate_rejects_non_none_severity(self) -> None:
        """Attempting to set severity raises ValueError."""
        signal = Signal.create(
            signal_type=SignalType.SENSITIVE_DATA,
            source_artifact="test.har",
            description="Test signal",
            evidence={},
        )
        with pytest.raises(ValueError, match="severity MUST be None"):
            FindingCandidate(
                candidate_id="test",
                endpoint="https://example.com",
                signals=(signal,),
                artifact_references=("test.har",),
                created_at=datetime.now(timezone.utc),
                severity="HIGH",  # type: ignore - intentional violation
            )
    
    def test_finding_candidate_serialization_preserves_none_fields(self) -> None:
        """Serialized FindingCandidate explicitly includes None for forbidden fields."""
        signal = Signal.create(
            signal_type=SignalType.SENSITIVE_DATA,
            source_artifact="test.har",
            description="Test signal",
            evidence={},
        )
        candidate = FindingCandidate.create(
            endpoint="https://example.com/api",
            signals=[signal],
        )
        
        data = candidate.to_dict()
        assert data["severity"] is None
        assert data["classification"] is None
        assert data["confidence"] is None


# =============================================================================
# Property 7: JSON Serialization Round-Trip
# =============================================================================

class TestScanResultJsonRoundTrip:
    """Property 7: Serializing to JSON and deserializing produces equivalent ScanResult."""
    
    def test_scan_result_json_round_trip(self) -> None:
        """Property: to_json() -> from_json() produces equivalent result."""
        signal = Signal.create(
            signal_type=SignalType.HEADER_MISCONFIG,
            source_artifact="test.har",
            description="Missing CSP header",
            evidence={"header": "Content-Security-Policy", "status": "missing"},
            endpoint="https://example.com/api",
        )
        candidate = FindingCandidate.create(
            endpoint="https://example.com/api",
            signals=[signal],
        )
        
        original = ScanResult.create(
            execution_id="exec-123",
            signals=[signal],
            finding_candidates=[candidate],
            artifacts_scanned=["test.har", "console.log"],
            artifacts_failed=["trace.json"],
            scan_started_at=datetime.now(timezone.utc),
            immutability_verified=True,
        )
        
        # Round-trip through JSON
        json_str = original.to_json()
        restored = ScanResult.from_json(json_str)
        
        # Verify equivalence
        assert restored.result_id == original.result_id
        assert restored.execution_id == original.execution_id
        assert len(restored.signals) == len(original.signals)
        assert len(restored.finding_candidates) == len(original.finding_candidates)
        assert restored.artifacts_scanned == original.artifacts_scanned
        assert restored.artifacts_failed == original.artifacts_failed
        assert restored.immutability_verified == original.immutability_verified
        
        # Verify signal equivalence
        for orig_sig, rest_sig in zip(original.signals, restored.signals):
            assert rest_sig.signal_id == orig_sig.signal_id
            assert rest_sig.signal_type == orig_sig.signal_type
            assert rest_sig.source_artifact == orig_sig.source_artifact
            assert rest_sig.description == orig_sig.description
            assert rest_sig.severity is None
            assert rest_sig.classification is None
            assert rest_sig.confidence is None
    
    def test_scan_result_dict_round_trip(self) -> None:
        """Property: to_dict() -> from_dict() produces equivalent result."""
        signal = Signal.create(
            signal_type=SignalType.REFLECTION,
            source_artifact="network.har",
            description="User input reflected in response",
            evidence={"input": "test", "output": "test"},
        )
        
        original = ScanResult.create(
            execution_id="exec-456",
            signals=[signal],
            finding_candidates=[],
            artifacts_scanned=["network.har"],
            artifacts_failed=[],
            scan_started_at=datetime.now(timezone.utc),
            immutability_verified=True,
        )
        
        # Round-trip through dict
        data = original.to_dict()
        restored = ScanResult.from_dict(data)
        
        assert restored.result_id == original.result_id
        assert restored.execution_id == original.execution_id
        assert len(restored.signals) == 1
        assert restored.signals[0].signal_id == signal.signal_id
    
    def test_empty_scan_result_round_trip(self) -> None:
        """Empty scan result (no signals) round-trips correctly."""
        original = ScanResult.create(
            execution_id="exec-empty",
            signals=[],
            finding_candidates=[],
            artifacts_scanned=[],
            artifacts_failed=["all-failed.har"],
            scan_started_at=datetime.now(timezone.utc),
            immutability_verified=False,
        )
        
        json_str = original.to_json()
        restored = ScanResult.from_json(json_str)
        
        assert restored.execution_id == "exec-empty"
        assert len(restored.signals) == 0
        assert len(restored.finding_candidates) == 0
        assert restored.artifacts_failed == ("all-failed.har",)
        assert restored.immutability_verified is False


# =============================================================================
# Unit Tests for Data Model Validation
# =============================================================================

class TestSignalValidation:
    """Unit tests for Signal validation."""
    
    def test_signal_requires_signal_id(self) -> None:
        """Signal must have signal_id."""
        with pytest.raises(ValueError, match="must have signal_id"):
            Signal(
                signal_id="",
                signal_type=SignalType.SENSITIVE_DATA,
                source_artifact="test.har",
                description="test",
                evidence={},
                detected_at=datetime.now(timezone.utc),
            )
    
    def test_signal_requires_source_artifact(self) -> None:
        """Signal must have source_artifact."""
        with pytest.raises(ValueError, match="must have source_artifact"):
            Signal(
                signal_id="test",
                signal_type=SignalType.SENSITIVE_DATA,
                source_artifact="",
                description="test",
                evidence={},
                detected_at=datetime.now(timezone.utc),
            )
    
    def test_signal_requires_description(self) -> None:
        """Signal must have description."""
        with pytest.raises(ValueError, match="must have description"):
            Signal(
                signal_id="test",
                signal_type=SignalType.SENSITIVE_DATA,
                source_artifact="test.har",
                description="",
                evidence={},
                detected_at=datetime.now(timezone.utc),
            )
    
    def test_signal_create_generates_id(self) -> None:
        """Signal.create() generates unique ID."""
        s1 = Signal.create(
            signal_type=SignalType.SENSITIVE_DATA,
            source_artifact="test.har",
            description="test",
            evidence={},
        )
        s2 = Signal.create(
            signal_type=SignalType.SENSITIVE_DATA,
            source_artifact="test.har",
            description="test",
            evidence={},
        )
        assert s1.signal_id != s2.signal_id


class TestFindingCandidateValidation:
    """Unit tests for FindingCandidate validation."""
    
    def test_finding_candidate_requires_candidate_id(self) -> None:
        """FindingCandidate must have candidate_id."""
        signal = Signal.create(
            signal_type=SignalType.SENSITIVE_DATA,
            source_artifact="test.har",
            description="test",
            evidence={},
        )
        with pytest.raises(ValueError, match="must have candidate_id"):
            FindingCandidate(
                candidate_id="",
                endpoint="https://example.com",
                signals=(signal,),
                artifact_references=("test.har",),
                created_at=datetime.now(timezone.utc),
            )
    
    def test_finding_candidate_requires_endpoint(self) -> None:
        """FindingCandidate must have endpoint."""
        signal = Signal.create(
            signal_type=SignalType.SENSITIVE_DATA,
            source_artifact="test.har",
            description="test",
            evidence={},
        )
        with pytest.raises(ValueError, match="must have endpoint"):
            FindingCandidate(
                candidate_id="test",
                endpoint="",
                signals=(signal,),
                artifact_references=("test.har",),
                created_at=datetime.now(timezone.utc),
            )
    
    def test_finding_candidate_requires_signals(self) -> None:
        """FindingCandidate must have at least one signal."""
        with pytest.raises(ValueError, match="must have at least one signal"):
            FindingCandidate(
                candidate_id="test",
                endpoint="https://example.com",
                signals=(),
                artifact_references=(),
                created_at=datetime.now(timezone.utc),
            )
    
    def test_finding_candidate_collects_artifact_references(self) -> None:
        """FindingCandidate.create() collects artifact references from signals."""
        s1 = Signal.create(
            signal_type=SignalType.SENSITIVE_DATA,
            source_artifact="file1.har",
            description="test1",
            evidence={},
        )
        s2 = Signal.create(
            signal_type=SignalType.HEADER_MISCONFIG,
            source_artifact="file2.har",
            description="test2",
            evidence={},
        )
        s3 = Signal.create(
            signal_type=SignalType.REFLECTION,
            source_artifact="file1.har",  # Duplicate
            description="test3",
            evidence={},
        )
        
        candidate = FindingCandidate.create(
            endpoint="https://example.com",
            signals=[s1, s2, s3],
        )
        
        # Should have unique, sorted artifact references
        assert candidate.artifact_references == ("file1.har", "file2.har")


class TestScanResultValidation:
    """Unit tests for ScanResult validation."""
    
    def test_scan_result_requires_result_id(self) -> None:
        """ScanResult must have result_id."""
        with pytest.raises(ValueError, match="must have result_id"):
            ScanResult(
                result_id="",
                execution_id="exec-123",
                signals=(),
                finding_candidates=(),
                artifacts_scanned=(),
                artifacts_failed=(),
                scan_started_at=datetime.now(timezone.utc),
                scan_completed_at=datetime.now(timezone.utc),
                immutability_verified=True,
            )
    
    def test_scan_result_requires_execution_id(self) -> None:
        """ScanResult must have execution_id."""
        with pytest.raises(ValueError, match="must have execution_id"):
            ScanResult(
                result_id="test",
                execution_id="",
                signals=(),
                finding_candidates=(),
                artifacts_scanned=(),
                artifacts_failed=(),
                scan_started_at=datetime.now(timezone.utc),
                scan_completed_at=datetime.now(timezone.utc),
                immutability_verified=True,
            )
