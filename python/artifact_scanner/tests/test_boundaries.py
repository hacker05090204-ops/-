"""
Phase-5 Architectural Boundary Tests

Tests for Property 6: Architectural Boundary Enforcement.
Validates that forbidden actions raise ArchitecturalViolationError.

All tests use synthetic data (no real Phase-4 artifacts).
"""

import pytest
import tempfile
from pathlib import Path

from artifact_scanner.scanner import Scanner
from artifact_scanner.errors import ArchitecturalViolationError


# =============================================================================
# Property 6: Architectural Boundary Enforcement
# =============================================================================

class TestArchitecturalBoundaryEnforcement:
    """Property 6: Forbidden methods raise ArchitecturalViolationError."""
    
    @pytest.fixture
    def scanner(self):
        """Create Scanner with temp directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Scanner(tmpdir)
    
    def test_classify_vulnerability_forbidden(self, scanner):
        """classify_vulnerability is forbidden."""
        with pytest.raises(ArchitecturalViolationError) as exc_info:
            scanner.classify_vulnerability("signal-1", "XSS")
        
        assert "MCP's responsibility" in str(exc_info.value)
    
    def test_assign_severity_forbidden(self, scanner):
        """assign_severity is forbidden."""
        with pytest.raises(ArchitecturalViolationError) as exc_info:
            scanner.assign_severity("signal-1", "HIGH")
        
        assert "human's responsibility" in str(exc_info.value)
    
    def test_compute_confidence_forbidden(self, scanner):
        """compute_confidence is forbidden."""
        with pytest.raises(ArchitecturalViolationError) as exc_info:
            scanner.compute_confidence("signal-1")
        
        assert "MCP's responsibility" in str(exc_info.value)
    
    def test_submit_report_forbidden(self, scanner):
        """submit_report is forbidden."""
        with pytest.raises(ArchitecturalViolationError) as exc_info:
            scanner.submit_report({"finding": "test"})
        
        assert "human's responsibility" in str(exc_info.value)
    
    def test_trigger_execution_forbidden(self, scanner):
        """trigger_execution is forbidden."""
        with pytest.raises(ArchitecturalViolationError) as exc_info:
            scanner.trigger_execution("action-1")
        
        assert "Phase-4's responsibility" in str(exc_info.value)
    
    def test_generate_proof_forbidden(self, scanner):
        """generate_proof is forbidden."""
        with pytest.raises(ArchitecturalViolationError) as exc_info:
            scanner.generate_proof("finding-1")
        
        assert "MCP's responsibility" in str(exc_info.value)
    
    def test_forbidden_methods_with_various_args(self, scanner):
        """Forbidden methods raise error regardless of arguments."""
        # Test with no args
        with pytest.raises(ArchitecturalViolationError):
            scanner.classify_vulnerability()
        
        # Test with positional args
        with pytest.raises(ArchitecturalViolationError):
            scanner.assign_severity("a", "b", "c")
        
        # Test with keyword args
        with pytest.raises(ArchitecturalViolationError):
            scanner.compute_confidence(signal_id="test", method="ml")
        
        # Test with mixed args
        with pytest.raises(ArchitecturalViolationError):
            scanner.submit_report("report", format="json", urgent=True)


# =============================================================================
# Data Model Boundary Tests
# =============================================================================

class TestDataModelBoundaries:
    """Tests for data model boundary enforcement."""
    
    def test_signal_rejects_severity(self):
        """Signal rejects non-None severity."""
        from artifact_scanner.types import Signal, SignalType
        from datetime import datetime, timezone
        
        with pytest.raises(ValueError, match="severity MUST be None"):
            Signal(
                signal_id="test",
                signal_type=SignalType.SENSITIVE_DATA,
                source_artifact="test.har",
                description="test",
                evidence={},
                detected_at=datetime.now(timezone.utc),
                severity="HIGH",  # type: ignore
            )
    
    def test_signal_rejects_classification(self):
        """Signal rejects non-None classification."""
        from artifact_scanner.types import Signal, SignalType
        from datetime import datetime, timezone
        
        with pytest.raises(ValueError, match="classification MUST be None"):
            Signal(
                signal_id="test",
                signal_type=SignalType.SENSITIVE_DATA,
                source_artifact="test.har",
                description="test",
                evidence={},
                detected_at=datetime.now(timezone.utc),
                classification="XSS",  # type: ignore
            )
    
    def test_signal_rejects_confidence(self):
        """Signal rejects non-None confidence."""
        from artifact_scanner.types import Signal, SignalType
        from datetime import datetime, timezone
        
        with pytest.raises(ValueError, match="confidence MUST be None"):
            Signal(
                signal_id="test",
                signal_type=SignalType.SENSITIVE_DATA,
                source_artifact="test.har",
                description="test",
                evidence={},
                detected_at=datetime.now(timezone.utc),
                confidence=0.95,  # type: ignore
            )
    
    def test_finding_candidate_rejects_severity(self):
        """FindingCandidate rejects non-None severity."""
        from artifact_scanner.types import Signal, SignalType, FindingCandidate
        from datetime import datetime, timezone
        
        signal = Signal.create(
            signal_type=SignalType.SENSITIVE_DATA,
            source_artifact="test.har",
            description="test",
            evidence={},
        )
        
        with pytest.raises(ValueError, match="severity MUST be None"):
            FindingCandidate(
                candidate_id="test",
                endpoint="https://example.com",
                signals=(signal,),
                artifact_references=("test.har",),
                created_at=datetime.now(timezone.utc),
                severity="HIGH",  # type: ignore
            )
    
    def test_finding_candidate_rejects_classification(self):
        """FindingCandidate rejects non-None classification."""
        from artifact_scanner.types import Signal, SignalType, FindingCandidate
        from datetime import datetime, timezone
        
        signal = Signal.create(
            signal_type=SignalType.SENSITIVE_DATA,
            source_artifact="test.har",
            description="test",
            evidence={},
        )
        
        with pytest.raises(ValueError, match="classification MUST be None"):
            FindingCandidate(
                candidate_id="test",
                endpoint="https://example.com",
                signals=(signal,),
                artifact_references=("test.har",),
                created_at=datetime.now(timezone.utc),
                classification="XSS",  # type: ignore
            )
    
    def test_finding_candidate_rejects_confidence(self):
        """FindingCandidate rejects non-None confidence."""
        from artifact_scanner.types import Signal, SignalType, FindingCandidate
        from datetime import datetime, timezone
        
        signal = Signal.create(
            signal_type=SignalType.SENSITIVE_DATA,
            source_artifact="test.har",
            description="test",
            evidence={},
        )
        
        with pytest.raises(ValueError, match="confidence MUST be None"):
            FindingCandidate(
                candidate_id="test",
                endpoint="https://example.com",
                signals=(signal,),
                artifact_references=("test.har",),
                created_at=datetime.now(timezone.utc),
                confidence=0.95,  # type: ignore
            )
