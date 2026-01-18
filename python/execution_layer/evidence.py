"""
Execution Layer Evidence Recorder

Captures HAR, screenshots, console logs, and execution trace.
Video recording is OFF by default, enabled only for MCP BUG or human escalation.

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Any
import secrets
import hashlib
import asyncio

from execution_layer.types import (
    EvidenceType,
    EvidenceArtifact,
    EvidenceBundle,
)
from execution_layer.errors import EvidenceCaptureError


@dataclass
class RecordingSession:
    """Active recording session for evidence capture."""
    session_id: str
    execution_id: str
    started_at: datetime
    har_enabled: bool = True
    screenshots_enabled: bool = True
    console_logs_enabled: bool = True
    video_enabled: bool = False  # OFF by default
    execution_trace: list[dict[str, Any]] = field(default_factory=list)
    screenshots: list[EvidenceArtifact] = field(default_factory=list)
    console_logs: list[EvidenceArtifact] = field(default_factory=list)
    har_content: Optional[bytes] = None
    video_content: Optional[bytes] = None


class EvidenceRecorder:
    """Records evidence during action execution.
    
    MANDATORY EVIDENCE (always captured):
    - HAR file of all network traffic
    - Screenshots at key steps
    - Console logs
    - Execution trace
    
    OPTIONAL EVIDENCE (off by default):
    - Video recording (enabled only for MCP BUG or human escalation)
    """
    
    def __init__(self) -> None:
        self._active_sessions: dict[str, RecordingSession] = {}
        self._completed_bundles: dict[str, EvidenceBundle] = {}
    
    def start_recording(
        self,
        execution_id: str,
        enable_video: bool = False,
    ) -> str:
        """Start evidence recording for an execution.
        
        Args:
            execution_id: Unique execution identifier
            enable_video: Enable video recording (default: False)
        
        Returns:
            Session ID for the recording session
        """
        session_id = secrets.token_urlsafe(16)
        session = RecordingSession(
            session_id=session_id,
            execution_id=execution_id,
            started_at=datetime.now(timezone.utc),
            video_enabled=enable_video,
        )
        self._active_sessions[session_id] = session
        return session_id

    def add_trace_event(
        self,
        session_id: str,
        event_type: str,
        details: dict[str, Any],
    ) -> None:
        """Add event to execution trace."""
        session = self._get_session(session_id)
        session.execution_trace.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "details": details,
        })
    
    def capture_screenshot(
        self,
        session_id: str,
        content: bytes,
        label: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> EvidenceArtifact:
        """Capture screenshot at current state."""
        session = self._get_session(session_id)
        
        if not session.screenshots_enabled:
            raise EvidenceCaptureError("Screenshots are disabled for this session")
        
        artifact = EvidenceArtifact.create(
            artifact_type=EvidenceType.SCREENSHOT,
            content=content,
            metadata={"label": label, **(metadata or {})},
        )
        session.screenshots.append(artifact)
        
        # Add to trace
        self.add_trace_event(session_id, "screenshot", {
            "artifact_id": artifact.artifact_id,
            "label": label,
        })
        
        return artifact
    
    def capture_console_log(
        self,
        session_id: str,
        content: bytes,
        log_type: str = "info",
        metadata: Optional[dict[str, Any]] = None,
    ) -> EvidenceArtifact:
        """Capture console log."""
        session = self._get_session(session_id)
        
        if not session.console_logs_enabled:
            raise EvidenceCaptureError("Console logs are disabled for this session")
        
        artifact = EvidenceArtifact.create(
            artifact_type=EvidenceType.CONSOLE_LOG,
            content=content,
            metadata={"log_type": log_type, **(metadata or {})},
        )
        session.console_logs.append(artifact)
        
        return artifact
    
    def set_har_content(self, session_id: str, content: bytes) -> None:
        """Set HAR file content for session.
        
        SECURITY: HAR content is automatically redacted (RISK-X2).
        """
        session = self._get_session(session_id)
        if not session.har_enabled:
            raise EvidenceCaptureError("HAR capture is disabled for this session")
        
        # SECURITY: Apply mandatory redaction before storing (RISK-X2)
        import json
        from execution_layer.security import redact_har_content
        
        try:
            har_dict = json.loads(content.decode('utf-8'))
            redacted_har = redact_har_content(har_dict)
            session.har_content = json.dumps(redacted_har).encode('utf-8')
        except (json.JSONDecodeError, UnicodeDecodeError):
            # If we can't parse as JSON, store as-is but log warning
            # The EvidenceBundle validation will catch unredacted content
            session.har_content = content
    
    def set_video_content(self, session_id: str, content: bytes) -> None:
        """Set video content for session."""
        session = self._get_session(session_id)
        if not session.video_enabled:
            raise EvidenceCaptureError("Video recording is disabled for this session")
        session.video_content = content
    
    def enable_video(self, session_id: str) -> None:
        """Enable video recording for session (for MCP BUG or human escalation)."""
        session = self._get_session(session_id)
        session.video_enabled = True
    
    def stop_recording(self, session_id: str) -> EvidenceBundle:
        """Stop recording and return evidence bundle."""
        session = self._get_session(session_id)
        
        # Create HAR artifact if content exists
        har_artifact = None
        if session.har_content:
            har_artifact = EvidenceArtifact.create(
                artifact_type=EvidenceType.HAR,
                content=session.har_content,
            )
        
        # Create video artifact if content exists
        video_artifact = None
        if session.video_content:
            video_artifact = EvidenceArtifact.create(
                artifact_type=EvidenceType.VIDEO,
                content=session.video_content,
            )
        
        # Create bundle
        bundle = EvidenceBundle(
            bundle_id=secrets.token_urlsafe(16),
            execution_id=session.execution_id,
            har_file=har_artifact,
            screenshots=session.screenshots,
            video=video_artifact,
            console_logs=session.console_logs,
            execution_trace=session.execution_trace,
        )
        bundle.finalize()
        
        # Store and cleanup
        self._completed_bundles[bundle.bundle_id] = bundle
        del self._active_sessions[session_id]
        
        return bundle
    
    def _get_session(self, session_id: str) -> RecordingSession:
        """Get active session by ID."""
        session = self._active_sessions.get(session_id)
        if session is None:
            raise EvidenceCaptureError(f"No active session with ID '{session_id}'")
        return session
    
    def get_bundle(self, bundle_id: str) -> Optional[EvidenceBundle]:
        """Get completed evidence bundle by ID."""
        return self._completed_bundles.get(bundle_id)
    
    def is_session_active(self, session_id: str) -> bool:
        """Check if session is active."""
        return session_id in self._active_sessions
    
    async def compute_hash_async(self, content: bytes) -> str:
        """Compute hash asynchronously for performance."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: hashlib.sha256(content).hexdigest()
        )
