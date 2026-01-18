"""
Phase-5 Artifact Loader

READ-ONLY artifact loader for Phase-4 execution outputs.

INVARIANTS:
- Files are NEVER modified or deleted
- Hash verification before/after operations
- Graceful degradation on parse failures

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import hashlib
import json

from artifact_scanner.errors import (
    ArtifactNotFoundError,
    ArtifactParseError,
    NoArtifactsError,
)


@dataclass
class ExecutionManifest:
    """Execution manifest from Phase-4.
    
    Contains execution_id, timestamp, and artifact paths.
    """
    execution_id: str
    timestamp: str
    artifact_paths: list[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionManifest":
        """Create from dictionary."""
        return cls(
            execution_id=data["execution_id"],
            timestamp=data["timestamp"],
            artifact_paths=data.get("artifact_paths", []),
        )


@dataclass
class HAREntry:
    """Single HAR entry (request/response pair)."""
    request_url: str
    request_method: str
    request_headers: dict[str, str]
    response_status: int
    response_headers: dict[str, str]
    response_content: str
    response_mime_type: str


@dataclass
class HARData:
    """Parsed HAR file data."""
    entries: list[HAREntry] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HARData":
        """Parse HAR JSON structure."""
        entries = []
        log = data.get("log", {})
        for entry in log.get("entries", []):
            request = entry.get("request", {})
            response = entry.get("response", {})
            content = response.get("content", {})
            
            # Parse headers into dict
            req_headers = {
                h.get("name", ""): h.get("value", "")
                for h in request.get("headers", [])
            }
            resp_headers = {
                h.get("name", ""): h.get("value", "")
                for h in response.get("headers", [])
            }
            
            entries.append(HAREntry(
                request_url=request.get("url", ""),
                request_method=request.get("method", ""),
                request_headers=req_headers,
                response_status=response.get("status", 0),
                response_headers=resp_headers,
                response_content=content.get("text", ""),
                response_mime_type=content.get("mimeType", ""),
            ))
        
        return cls(entries=entries)


@dataclass
class ConsoleLogEntry:
    """Single console log entry."""
    level: str  # error, warning, info, log
    message: str
    timestamp: Optional[datetime] = None
    source: Optional[str] = None
    line_number: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConsoleLogEntry":
        """Parse console log entry."""
        timestamp = None
        if "timestamp" in data:
            try:
                timestamp = datetime.fromisoformat(data["timestamp"])
            except (ValueError, TypeError):
                pass
        
        return cls(
            level=data.get("level", "log"),
            message=data.get("message", ""),
            timestamp=timestamp,
            source=data.get("source"),
            line_number=data.get("lineNumber"),
        )


@dataclass
class TraceAction:
    """Single action in execution trace."""
    action_id: str
    action_type: str
    target: str
    parameters: dict[str, Any]
    outcome: str
    error: Optional[str] = None
    timestamp: Optional[datetime] = None


@dataclass
class ExecutionTrace:
    """Parsed execution trace."""
    execution_id: str
    actions: list[TraceAction] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionTrace":
        """Parse execution trace JSON."""
        actions = []
        for action_data in data.get("actions", []):
            timestamp = None
            if "timestamp" in action_data:
                try:
                    timestamp = datetime.fromisoformat(action_data["timestamp"])
                except (ValueError, TypeError):
                    pass
            
            actions.append(TraceAction(
                action_id=action_data.get("action_id", ""),
                action_type=action_data.get("action_type", ""),
                target=action_data.get("target", ""),
                parameters=action_data.get("parameters", {}),
                outcome=action_data.get("outcome", ""),
                error=action_data.get("error"),
                timestamp=timestamp,
            ))
        
        return cls(
            execution_id=data.get("execution_id", ""),
            actions=actions,
        )


@dataclass
class ScreenshotMetadata:
    """Screenshot file metadata (read-only)."""
    path: str
    size_bytes: int
    modified_at: datetime
    content_hash: str


class ArtifactLoader:
    """READ-ONLY artifact loader.
    
    INVARIANTS:
    - Files are NEVER modified or deleted
    - Hash verification for immutability
    - Graceful degradation on parse failures
    """
    
    def __init__(self, artifacts_dir: str) -> None:
        """Initialize loader with artifacts directory path."""
        self._artifacts_path = Path(artifacts_dir)
    
    def compute_file_hash(self, path: str) -> str:
        """Compute SHA-256 hash for immutability verification.
        
        Args:
            path: Path to file (relative to artifacts_dir or absolute)
        
        Returns:
            SHA-256 hex digest
        
        Raises:
            ArtifactNotFoundError: If file does not exist
        """
        file_path = self._resolve_path(path)
        if not file_path.exists():
            raise ArtifactNotFoundError(f"Artifact not found: {path}")
        
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def load_manifest(self, execution_id: str) -> ExecutionManifest:
        """Load and validate execution manifest.
        
        Args:
            execution_id: Execution identifier
        
        Returns:
            ExecutionManifest instance
        
        Raises:
            ArtifactNotFoundError: If manifest does not exist
            ArtifactParseError: If manifest is invalid JSON
        """
        manifest_path = self._artifacts_path / execution_id / "execution_manifest.json"
        if not manifest_path.exists():
            raise ArtifactNotFoundError(f"Manifest not found for execution: {execution_id}")
        
        try:
            with open(manifest_path, "r") as f:
                data = json.load(f)
            return ExecutionManifest.from_dict(data)
        except json.JSONDecodeError as e:
            raise ArtifactParseError(f"Invalid manifest JSON: {e}")
        except KeyError as e:
            raise ArtifactParseError(f"Missing required field in manifest: {e}")
    
    def load_har(self, path: str) -> HARData:
        """Load HAR file as read-only.
        
        Args:
            path: Path to HAR file
        
        Returns:
            HARData instance
        
        Raises:
            ArtifactNotFoundError: If file does not exist
            ArtifactParseError: If file is invalid
        """
        file_path = self._resolve_path(path)
        if not file_path.exists():
            raise ArtifactNotFoundError(f"HAR file not found: {path}")
        
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            return HARData.from_dict(data)
        except json.JSONDecodeError as e:
            raise ArtifactParseError(f"Invalid HAR JSON: {e}")
        except Exception as e:
            raise ArtifactParseError(f"Failed to parse HAR: {e}")
    
    def load_console_logs(self, path: str) -> list[ConsoleLogEntry]:
        """Load console log entries.
        
        Args:
            path: Path to console log file (JSON array)
        
        Returns:
            List of ConsoleLogEntry instances
        
        Raises:
            ArtifactNotFoundError: If file does not exist
            ArtifactParseError: If file is invalid
        """
        file_path = self._resolve_path(path)
        if not file_path.exists():
            raise ArtifactNotFoundError(f"Console log not found: {path}")
        
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            
            if isinstance(data, list):
                return [ConsoleLogEntry.from_dict(entry) for entry in data]
            elif isinstance(data, dict) and "entries" in data:
                return [ConsoleLogEntry.from_dict(entry) for entry in data["entries"]]
            else:
                raise ArtifactParseError("Console log must be array or object with 'entries'")
        except json.JSONDecodeError as e:
            raise ArtifactParseError(f"Invalid console log JSON: {e}")
    
    def load_execution_trace(self, path: str) -> ExecutionTrace:
        """Load execution trace.
        
        Args:
            path: Path to trace file
        
        Returns:
            ExecutionTrace instance
        
        Raises:
            ArtifactNotFoundError: If file does not exist
            ArtifactParseError: If file is invalid
        """
        file_path = self._resolve_path(path)
        if not file_path.exists():
            raise ArtifactNotFoundError(f"Execution trace not found: {path}")
        
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            return ExecutionTrace.from_dict(data)
        except json.JSONDecodeError as e:
            raise ArtifactParseError(f"Invalid trace JSON: {e}")
    
    def load_screenshot_metadata(self, path: str) -> ScreenshotMetadata:
        """Read screenshot file metadata without modifying the file.
        
        Args:
            path: Path to screenshot file
        
        Returns:
            ScreenshotMetadata instance
        
        Raises:
            ArtifactNotFoundError: If file does not exist
        """
        file_path = self._resolve_path(path)
        if not file_path.exists():
            raise ArtifactNotFoundError(f"Screenshot not found: {path}")
        
        stat = file_path.stat()
        content_hash = self.compute_file_hash(path)
        
        return ScreenshotMetadata(
            path=str(file_path),
            size_bytes=stat.st_size,
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            content_hash=content_hash,
        )
    
    def verify_artifact_exists(self, path: str) -> bool:
        """Check if artifact exists without loading it.
        
        Args:
            path: Path to artifact
        
        Returns:
            True if exists, False otherwise
        """
        file_path = self._resolve_path(path)
        return file_path.exists()
    
    def get_artifact_paths(self, execution_id: str) -> list[str]:
        """Get all artifact paths for an execution.
        
        Args:
            execution_id: Execution identifier
        
        Returns:
            List of artifact paths
        
        Raises:
            ArtifactNotFoundError: If execution directory does not exist
        """
        exec_dir = self._artifacts_path / execution_id
        if not exec_dir.exists():
            raise ArtifactNotFoundError(f"Execution directory not found: {execution_id}")
        
        paths = []
        for artifact_file in exec_dir.rglob("*"):
            if artifact_file.is_file():
                paths.append(str(artifact_file.relative_to(self._artifacts_path)))
        
        return sorted(paths)
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve path relative to artifacts directory.
        
        Args:
            path: Relative or absolute path
        
        Returns:
            Resolved Path object
        """
        path_obj = Path(path)
        if path_obj.is_absolute():
            return path_obj
        return self._artifacts_path / path
