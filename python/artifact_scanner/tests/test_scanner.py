"""
Phase-5 Scanner Tests

Tests for main Scanner orchestrator.
Validates:
- Property 5: Partial Result on Failure
- Full scan pipeline

All tests use synthetic artifacts (no real Phase-4 data).
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timezone

from artifact_scanner.scanner import Scanner
from artifact_scanner.types import SignalType
from artifact_scanner.errors import (
    NoArtifactsError,
    ImmutabilityViolationError,
    ArchitecturalViolationError,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def temp_artifacts_dir():
    """Create temporary artifacts directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def scanner(temp_artifacts_dir):
    """Create Scanner with temp directory."""
    return Scanner(str(temp_artifacts_dir))


def create_manifest(artifacts_dir: Path, execution_id: str, artifact_paths: list[str]) -> None:
    """Helper to create manifest."""
    exec_dir = artifacts_dir / execution_id
    exec_dir.mkdir(parents=True, exist_ok=True)
    
    manifest = {
        "execution_id": execution_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "artifact_paths": artifact_paths,
    }
    
    with open(exec_dir / "execution_manifest.json", "w") as f:
        json.dump(manifest, f)


def create_har(artifacts_dir: Path, path: str, entries: list[dict]) -> None:
    """Helper to create HAR file."""
    file_path = artifacts_dir / path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    har = {"log": {"version": "1.2", "entries": entries}}
    with open(file_path, "w") as f:
        json.dump(har, f)


def create_console_log(artifacts_dir: Path, path: str, entries: list[dict]) -> None:
    """Helper to create console log."""
    file_path = artifacts_dir / path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, "w") as f:
        json.dump(entries, f)


def create_trace(artifacts_dir: Path, path: str, execution_id: str, actions: list[dict]) -> None:
    """Helper to create trace file."""
    file_path = artifacts_dir / path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    trace = {"execution_id": execution_id, "actions": actions}
    with open(file_path, "w") as f:
        json.dump(trace, f)


# =============================================================================
# Property 5: Partial Result on Failure
# =============================================================================

class TestPartialResultOnFailure:
    """Property 5: Scan returns partial results when some artifacts fail."""
    
    def test_partial_result_on_missing_artifact(self, temp_artifacts_dir, scanner):
        """Scan continues when some artifacts are missing."""
        # Create manifest with one valid and one missing artifact
        create_manifest(temp_artifacts_dir, "exec-1", [
            "exec-1/network.har",
            "exec-1/missing.har",  # This doesn't exist
        ])
        
        # Create only the first artifact
        create_har(temp_artifacts_dir, "exec-1/network.har", [
            {
                "request": {"url": "https://example.com", "method": "GET", "headers": []},
                "response": {
                    "status": 200,
                    "headers": [],
                    "content": {"text": '{"api_key": "sk_test_1234567890abcdef"}'},
                },
            }
        ])
        
        result = scanner.scan("exec-1")
        
        # Should have partial results
        assert len(result.artifacts_scanned) == 1
        assert "exec-1/network.har" in result.artifacts_scanned
        assert len(result.artifacts_failed) == 1
        assert "exec-1/missing.har" in result.artifacts_failed
        
        # Should still have signals from successful artifact
        assert len(result.signals) >= 1
    
    def test_partial_result_on_parse_error(self, temp_artifacts_dir, scanner):
        """Scan continues when some artifacts fail to parse."""
        create_manifest(temp_artifacts_dir, "exec-1", [
            "exec-1/valid.har",
            "exec-1/invalid.har",
        ])
        
        # Create valid HAR
        create_har(temp_artifacts_dir, "exec-1/valid.har", [
            {
                "request": {"url": "https://example.com", "method": "GET", "headers": []},
                "response": {"status": 200, "headers": [], "content": {"text": "ok"}},
            }
        ])
        
        # Create invalid HAR (not valid JSON)
        invalid_path = temp_artifacts_dir / "exec-1" / "invalid.har"
        with open(invalid_path, "w") as f:
            f.write("not valid json {{{")
        
        result = scanner.scan("exec-1")
        
        assert "exec-1/valid.har" in result.artifacts_scanned
        assert "exec-1/invalid.har" in result.artifacts_failed
    
    def test_all_artifacts_failed_raises_error(self, temp_artifacts_dir, scanner):
        """Raise NoArtifactsError when all artifacts fail."""
        create_manifest(temp_artifacts_dir, "exec-1", [
            "exec-1/missing1.har",
            "exec-1/missing2.har",
        ])
        
        with pytest.raises(NoArtifactsError):
            scanner.scan("exec-1")


# =============================================================================
# Full Scan Pipeline Tests
# =============================================================================

class TestFullScanPipeline:
    """Tests for full scan pipeline."""
    
    def test_scan_with_all_artifact_types(self, temp_artifacts_dir, scanner):
        """Scan processes all artifact types."""
        create_manifest(temp_artifacts_dir, "exec-1", [
            "exec-1/network.har",
            "exec-1/console.json",
            "exec-1/trace.json",
        ])
        
        # Create HAR with sensitive data
        create_har(temp_artifacts_dir, "exec-1/network.har", [
            {
                "request": {"url": "https://api.example.com/config", "method": "GET", "headers": []},
                "response": {
                    "status": 200,
                    "headers": [],
                    "content": {"text": '{"api_key": "sk_live_1234567890abcdef1234567890"}'},
                },
            }
        ])
        
        # Create console log with path disclosure
        create_console_log(temp_artifacts_dir, "exec-1/console.json", [
            {"level": "error", "message": "Error at /home/user/app/src/index.js:42"},
        ])
        
        # Create trace with failed action
        create_trace(temp_artifacts_dir, "exec-1/trace.json", "exec-1", [
            {
                "action_id": "a1",
                "action_type": "click",
                "target": "#submit",
                "parameters": {},
                "outcome": "failed",
                "error": "Element not found",
            }
        ])
        
        result = scanner.scan("exec-1")
        
        # Should have scanned all artifacts
        assert len(result.artifacts_scanned) == 3
        assert len(result.artifacts_failed) == 0
        
        # Should have signals from all analyzers
        signal_types = {s.signal_type for s in result.signals}
        assert SignalType.SENSITIVE_DATA in signal_types
        assert SignalType.PATH_DISCLOSURE in signal_types
        assert SignalType.STATE_ANOMALY in signal_types
    
    def test_scan_aggregates_signals(self, temp_artifacts_dir, scanner):
        """Scan aggregates signals into finding candidates."""
        create_manifest(temp_artifacts_dir, "exec-1", ["exec-1/network.har"])
        
        # Create HAR with multiple signals for same endpoint
        create_har(temp_artifacts_dir, "exec-1/network.har", [
            {
                "request": {"url": "https://api.example.com/config", "method": "GET", "headers": []},
                "response": {
                    "status": 200,
                    "headers": [{"name": "Access-Control-Allow-Origin", "value": "*"}],
                    "content": {"text": '{"api_key": "sk_live_1234567890abcdef1234567890"}'},
                },
            }
        ])
        
        result = scanner.scan("exec-1")
        
        # Should have finding candidates
        assert len(result.finding_candidates) >= 1
        
        # Candidate should have multiple signals
        candidate = result.finding_candidates[0]
        assert len(candidate.signals) >= 1
    
    def test_scan_verifies_immutability(self, temp_artifacts_dir, scanner):
        """Scan verifies artifact immutability."""
        create_manifest(temp_artifacts_dir, "exec-1", ["exec-1/network.har"])
        create_har(temp_artifacts_dir, "exec-1/network.har", [])
        
        result = scanner.scan("exec-1")
        
        assert result.immutability_verified is True
    
    def test_scan_result_includes_execution_id(self, temp_artifacts_dir, scanner):
        """ScanResult includes execution_id."""
        create_manifest(temp_artifacts_dir, "exec-123", ["exec-123/network.har"])
        create_har(temp_artifacts_dir, "exec-123/network.har", [])
        
        result = scanner.scan("exec-123")
        
        assert result.execution_id == "exec-123"
    
    def test_scan_result_includes_timestamps(self, temp_artifacts_dir, scanner):
        """ScanResult includes scan timestamps."""
        create_manifest(temp_artifacts_dir, "exec-1", ["exec-1/network.har"])
        create_har(temp_artifacts_dir, "exec-1/network.har", [])
        
        result = scanner.scan("exec-1")
        
        assert result.scan_started_at is not None
        assert result.scan_completed_at is not None
        assert result.scan_completed_at >= result.scan_started_at


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Tests for error handling."""
    
    def test_no_artifacts_error_for_missing_execution(self, scanner):
        """Raise NoArtifactsError for missing execution."""
        with pytest.raises(NoArtifactsError):
            scanner.scan("nonexistent-execution")
    
    def test_no_artifacts_error_for_empty_manifest(self, temp_artifacts_dir, scanner):
        """Raise NoArtifactsError for empty manifest."""
        create_manifest(temp_artifacts_dir, "exec-1", [])
        
        with pytest.raises(NoArtifactsError):
            scanner.scan("exec-1")


# =============================================================================
# Architectural Boundary Tests
# =============================================================================

class TestArchitecturalBoundaries:
    """Tests for architectural boundary enforcement."""
    
    def test_classify_vulnerability_raises_error(self, scanner):
        """classify_vulnerability raises ArchitecturalViolationError."""
        with pytest.raises(ArchitecturalViolationError, match="MCP's responsibility"):
            scanner.classify_vulnerability()
    
    def test_assign_severity_raises_error(self, scanner):
        """assign_severity raises ArchitecturalViolationError."""
        with pytest.raises(ArchitecturalViolationError, match="human's responsibility"):
            scanner.assign_severity()
    
    def test_compute_confidence_raises_error(self, scanner):
        """compute_confidence raises ArchitecturalViolationError."""
        with pytest.raises(ArchitecturalViolationError, match="MCP's responsibility"):
            scanner.compute_confidence()
    
    def test_submit_report_raises_error(self, scanner):
        """submit_report raises ArchitecturalViolationError."""
        with pytest.raises(ArchitecturalViolationError, match="human's responsibility"):
            scanner.submit_report()
    
    def test_trigger_execution_raises_error(self, scanner):
        """trigger_execution raises ArchitecturalViolationError."""
        with pytest.raises(ArchitecturalViolationError, match="Phase-4's responsibility"):
            scanner.trigger_execution()
    
    def test_generate_proof_raises_error(self, scanner):
        """generate_proof raises ArchitecturalViolationError."""
        with pytest.raises(ArchitecturalViolationError, match="MCP's responsibility"):
            scanner.generate_proof()
