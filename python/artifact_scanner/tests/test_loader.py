"""
Phase-5 Artifact Loader Tests

Tests for ArtifactLoader read-only operations.
Validates:
- Property 1: Artifact Immutability
- Graceful degradation on missing/invalid artifacts

All tests use synthetic artifacts (no real Phase-4 data).
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timezone
from hypothesis import given, strategies as st

from artifact_scanner.loader import (
    ArtifactLoader,
    ExecutionManifest,
    HARData,
    ConsoleLogEntry,
    ExecutionTrace,
    ScreenshotMetadata,
)
from artifact_scanner.errors import (
    ArtifactNotFoundError,
    ArtifactParseError,
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
def loader(temp_artifacts_dir):
    """Create ArtifactLoader with temp directory."""
    return ArtifactLoader(str(temp_artifacts_dir))


def create_manifest(artifacts_dir: Path, execution_id: str, artifact_paths: list[str]) -> Path:
    """Helper to create a manifest file."""
    exec_dir = artifacts_dir / execution_id
    exec_dir.mkdir(parents=True, exist_ok=True)
    
    manifest = {
        "execution_id": execution_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "artifact_paths": artifact_paths,
    }
    
    manifest_path = exec_dir / "execution_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f)
    
    return manifest_path


def create_har_file(artifacts_dir: Path, path: str, entries: list[dict]) -> Path:
    """Helper to create a HAR file."""
    file_path = artifacts_dir / path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    har = {
        "log": {
            "version": "1.2",
            "entries": entries,
        }
    }
    
    with open(file_path, "w") as f:
        json.dump(har, f)
    
    return file_path


def create_console_log(artifacts_dir: Path, path: str, entries: list[dict]) -> Path:
    """Helper to create a console log file."""
    file_path = artifacts_dir / path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, "w") as f:
        json.dump(entries, f)
    
    return file_path


def create_trace_file(artifacts_dir: Path, path: str, execution_id: str, actions: list[dict]) -> Path:
    """Helper to create an execution trace file."""
    file_path = artifacts_dir / path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    trace = {
        "execution_id": execution_id,
        "actions": actions,
    }
    
    with open(file_path, "w") as f:
        json.dump(trace, f)
    
    return file_path


def create_screenshot(artifacts_dir: Path, path: str, content: bytes = b"fake png data") -> Path:
    """Helper to create a screenshot file."""
    file_path = artifacts_dir / path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    return file_path


# =============================================================================
# Property 1: Artifact Immutability
# =============================================================================

class TestArtifactImmutability:
    """Property 1: File hash before == hash after for any operation."""
    
    def test_load_har_does_not_modify_file(self, temp_artifacts_dir, loader):
        """Loading HAR file does not modify it."""
        har_path = "exec-1/network.har"
        create_har_file(temp_artifacts_dir, har_path, [
            {
                "request": {"url": "https://example.com", "method": "GET", "headers": []},
                "response": {"status": 200, "headers": [], "content": {"text": "OK"}},
            }
        ])
        
        # Hash before
        hash_before = loader.compute_file_hash(har_path)
        
        # Load HAR
        har_data = loader.load_har(har_path)
        assert len(har_data.entries) == 1
        
        # Hash after
        hash_after = loader.compute_file_hash(har_path)
        
        assert hash_before == hash_after, "HAR file was modified during load"
    
    def test_load_console_logs_does_not_modify_file(self, temp_artifacts_dir, loader):
        """Loading console logs does not modify file."""
        log_path = "exec-1/console.json"
        create_console_log(temp_artifacts_dir, log_path, [
            {"level": "error", "message": "Test error"},
            {"level": "warning", "message": "Test warning"},
        ])
        
        hash_before = loader.compute_file_hash(log_path)
        logs = loader.load_console_logs(log_path)
        hash_after = loader.compute_file_hash(log_path)
        
        assert len(logs) == 2
        assert hash_before == hash_after, "Console log was modified during load"
    
    def test_load_trace_does_not_modify_file(self, temp_artifacts_dir, loader):
        """Loading execution trace does not modify file."""
        trace_path = "exec-1/trace.json"
        create_trace_file(temp_artifacts_dir, trace_path, "exec-1", [
            {"action_id": "a1", "action_type": "click", "target": "#btn", "parameters": {}, "outcome": "success"},
        ])
        
        hash_before = loader.compute_file_hash(trace_path)
        trace = loader.load_execution_trace(trace_path)
        hash_after = loader.compute_file_hash(trace_path)
        
        assert len(trace.actions) == 1
        assert hash_before == hash_after, "Trace file was modified during load"
    
    def test_load_screenshot_metadata_does_not_modify_file(self, temp_artifacts_dir, loader):
        """Loading screenshot metadata does not modify file."""
        screenshot_path = "exec-1/screenshot.png"
        create_screenshot(temp_artifacts_dir, screenshot_path, b"PNG fake data 12345")
        
        hash_before = loader.compute_file_hash(screenshot_path)
        metadata = loader.load_screenshot_metadata(screenshot_path)
        hash_after = loader.compute_file_hash(screenshot_path)
        
        assert metadata.size_bytes > 0
        assert hash_before == hash_after, "Screenshot was modified during metadata load"
    
    def test_load_manifest_does_not_modify_file(self, temp_artifacts_dir, loader):
        """Loading manifest does not modify file."""
        create_manifest(temp_artifacts_dir, "exec-1", ["network.har"])
        manifest_path = "exec-1/execution_manifest.json"
        
        hash_before = loader.compute_file_hash(manifest_path)
        manifest = loader.load_manifest("exec-1")
        hash_after = loader.compute_file_hash(manifest_path)
        
        assert manifest.execution_id == "exec-1"
        assert hash_before == hash_after, "Manifest was modified during load"
    
    @given(st.binary(min_size=1, max_size=1000))
    def test_hash_is_deterministic(self, content):
        """Hash computation is deterministic for any content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_artifacts_dir = Path(tmpdir)
            loader = ArtifactLoader(str(temp_artifacts_dir))
            file_path = temp_artifacts_dir / "test_file.bin"
            
            with open(file_path, "wb") as f:
                f.write(content)
            
            hash1 = loader.compute_file_hash("test_file.bin")
            hash2 = loader.compute_file_hash("test_file.bin")
            hash3 = loader.compute_file_hash("test_file.bin")
            
            assert hash1 == hash2 == hash3, "Hash should be deterministic"


# =============================================================================
# Manifest Loading Tests
# =============================================================================

class TestManifestLoading:
    """Tests for manifest loading."""
    
    def test_load_manifest_success(self, temp_artifacts_dir, loader):
        """Successfully load valid manifest."""
        create_manifest(temp_artifacts_dir, "exec-123", ["network.har", "console.json"])
        
        manifest = loader.load_manifest("exec-123")
        
        assert manifest.execution_id == "exec-123"
        assert manifest.artifact_paths == ["network.har", "console.json"]
    
    def test_load_manifest_not_found(self, loader):
        """Raise ArtifactNotFoundError for missing manifest."""
        with pytest.raises(ArtifactNotFoundError, match="Manifest not found"):
            loader.load_manifest("nonexistent-exec")
    
    def test_load_manifest_invalid_json(self, temp_artifacts_dir, loader):
        """Raise ArtifactParseError for invalid JSON."""
        exec_dir = temp_artifacts_dir / "exec-bad"
        exec_dir.mkdir()
        
        manifest_path = exec_dir / "execution_manifest.json"
        with open(manifest_path, "w") as f:
            f.write("not valid json {{{")
        
        with pytest.raises(ArtifactParseError, match="Invalid manifest JSON"):
            loader.load_manifest("exec-bad")


# =============================================================================
# HAR Loading Tests
# =============================================================================

class TestHARLoading:
    """Tests for HAR file loading."""
    
    def test_load_har_success(self, temp_artifacts_dir, loader):
        """Successfully load valid HAR file."""
        create_har_file(temp_artifacts_dir, "exec-1/network.har", [
            {
                "request": {
                    "url": "https://example.com/api",
                    "method": "POST",
                    "headers": [{"name": "Content-Type", "value": "application/json"}],
                },
                "response": {
                    "status": 200,
                    "headers": [{"name": "X-Custom", "value": "test"}],
                    "content": {"text": '{"result": "ok"}', "mimeType": "application/json"},
                },
            }
        ])
        
        har = loader.load_har("exec-1/network.har")
        
        assert len(har.entries) == 1
        entry = har.entries[0]
        assert entry.request_url == "https://example.com/api"
        assert entry.request_method == "POST"
        assert entry.request_headers["Content-Type"] == "application/json"
        assert entry.response_status == 200
        assert entry.response_headers["X-Custom"] == "test"
        assert entry.response_content == '{"result": "ok"}'
    
    def test_load_har_not_found(self, loader):
        """Raise ArtifactNotFoundError for missing HAR."""
        with pytest.raises(ArtifactNotFoundError, match="HAR file not found"):
            loader.load_har("nonexistent.har")
    
    def test_load_har_invalid_json(self, temp_artifacts_dir, loader):
        """Raise ArtifactParseError for invalid HAR JSON."""
        file_path = temp_artifacts_dir / "bad.har"
        with open(file_path, "w") as f:
            f.write("not json")
        
        with pytest.raises(ArtifactParseError, match="Invalid HAR JSON"):
            loader.load_har("bad.har")
    
    def test_load_har_empty_entries(self, temp_artifacts_dir, loader):
        """Handle HAR with no entries."""
        create_har_file(temp_artifacts_dir, "empty.har", [])
        
        har = loader.load_har("empty.har")
        assert len(har.entries) == 0


# =============================================================================
# Console Log Loading Tests
# =============================================================================

class TestConsoleLogLoading:
    """Tests for console log loading."""
    
    def test_load_console_logs_array_format(self, temp_artifacts_dir, loader):
        """Load console logs in array format."""
        create_console_log(temp_artifacts_dir, "console.json", [
            {"level": "error", "message": "Error 1", "source": "app.js", "lineNumber": 42},
            {"level": "warning", "message": "Warning 1"},
            {"level": "log", "message": "Info message"},
        ])
        
        logs = loader.load_console_logs("console.json")
        
        assert len(logs) == 3
        assert logs[0].level == "error"
        assert logs[0].message == "Error 1"
        assert logs[0].source == "app.js"
        assert logs[0].line_number == 42
        assert logs[1].level == "warning"
        assert logs[2].level == "log"
    
    def test_load_console_logs_object_format(self, temp_artifacts_dir, loader):
        """Load console logs in object format with 'entries' key."""
        file_path = temp_artifacts_dir / "console2.json"
        with open(file_path, "w") as f:
            json.dump({"entries": [{"level": "error", "message": "Test"}]}, f)
        
        logs = loader.load_console_logs("console2.json")
        assert len(logs) == 1
    
    def test_load_console_logs_not_found(self, loader):
        """Raise ArtifactNotFoundError for missing console log."""
        with pytest.raises(ArtifactNotFoundError, match="Console log not found"):
            loader.load_console_logs("missing.json")
    
    def test_load_console_logs_with_timestamp(self, temp_artifacts_dir, loader):
        """Parse timestamp in console log entries."""
        create_console_log(temp_artifacts_dir, "timed.json", [
            {"level": "error", "message": "Test", "timestamp": "2025-01-01T12:00:00+00:00"},
        ])
        
        logs = loader.load_console_logs("timed.json")
        assert logs[0].timestamp is not None


# =============================================================================
# Execution Trace Loading Tests
# =============================================================================

class TestTraceLoading:
    """Tests for execution trace loading."""
    
    def test_load_trace_success(self, temp_artifacts_dir, loader):
        """Successfully load execution trace."""
        create_trace_file(temp_artifacts_dir, "trace.json", "exec-1", [
            {
                "action_id": "a1",
                "action_type": "navigate",
                "target": "https://example.com",
                "parameters": {},
                "outcome": "success",
            },
            {
                "action_id": "a2",
                "action_type": "click",
                "target": "#submit",
                "parameters": {"wait": True},
                "outcome": "failed",
                "error": "Element not found",
            },
        ])
        
        trace = loader.load_execution_trace("trace.json")
        
        assert trace.execution_id == "exec-1"
        assert len(trace.actions) == 2
        assert trace.actions[0].action_type == "navigate"
        assert trace.actions[0].outcome == "success"
        assert trace.actions[1].error == "Element not found"
    
    def test_load_trace_not_found(self, loader):
        """Raise ArtifactNotFoundError for missing trace."""
        with pytest.raises(ArtifactNotFoundError, match="Execution trace not found"):
            loader.load_execution_trace("missing.json")


# =============================================================================
# Screenshot Metadata Loading Tests
# =============================================================================

class TestScreenshotMetadataLoading:
    """Tests for screenshot metadata loading."""
    
    def test_load_screenshot_metadata_success(self, temp_artifacts_dir, loader):
        """Successfully load screenshot metadata."""
        content = b"PNG fake image data with some content"
        create_screenshot(temp_artifacts_dir, "screenshot.png", content)
        
        metadata = loader.load_screenshot_metadata("screenshot.png")
        
        assert metadata.size_bytes == len(content)
        assert metadata.content_hash  # Non-empty hash
        assert "screenshot.png" in metadata.path
    
    def test_load_screenshot_metadata_not_found(self, loader):
        """Raise ArtifactNotFoundError for missing screenshot."""
        with pytest.raises(ArtifactNotFoundError, match="Screenshot not found"):
            loader.load_screenshot_metadata("missing.png")


# =============================================================================
# Utility Method Tests
# =============================================================================

class TestUtilityMethods:
    """Tests for utility methods."""
    
    def test_verify_artifact_exists_true(self, temp_artifacts_dir, loader):
        """verify_artifact_exists returns True for existing file."""
        create_screenshot(temp_artifacts_dir, "exists.png")
        assert loader.verify_artifact_exists("exists.png") is True
    
    def test_verify_artifact_exists_false(self, loader):
        """verify_artifact_exists returns False for missing file."""
        assert loader.verify_artifact_exists("missing.png") is False
    
    def test_get_artifact_paths(self, temp_artifacts_dir, loader):
        """get_artifact_paths returns all files in execution directory."""
        exec_dir = temp_artifacts_dir / "exec-1"
        exec_dir.mkdir()
        
        (exec_dir / "network.har").write_text("{}")
        (exec_dir / "console.json").write_text("[]")
        (exec_dir / "screenshot.png").write_bytes(b"png")
        
        paths = loader.get_artifact_paths("exec-1")
        
        assert len(paths) == 3
        assert "exec-1/network.har" in paths
        assert "exec-1/console.json" in paths
        assert "exec-1/screenshot.png" in paths
    
    def test_get_artifact_paths_not_found(self, loader):
        """Raise ArtifactNotFoundError for missing execution directory."""
        with pytest.raises(ArtifactNotFoundError, match="Execution directory not found"):
            loader.get_artifact_paths("nonexistent")
    
    def test_compute_file_hash_not_found(self, loader):
        """Raise ArtifactNotFoundError for missing file."""
        with pytest.raises(ArtifactNotFoundError, match="Artifact not found"):
            loader.compute_file_hash("missing.txt")
