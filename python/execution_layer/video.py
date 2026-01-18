"""
Execution Layer Video PoC Generator

Generates video proof-of-concept for MCP-confirmed BUG only.
IDEMPOTENCY GUARD: Only ONE VideoPoC per finding_id.

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

from datetime import datetime, timezone
from typing import Optional, Any

from execution_layer.types import (
    EvidenceType,
    EvidenceArtifact,
    EvidenceBundle,
    VideoPoC,
    MCPClassification,
    MCPVerificationResult,
)
from execution_layer.errors import (
    VideoPoCExistsError,
    ArchitecturalViolationError,
)


class VideoPoCGenerator:
    """Generates Video PoC for confirmed bugs.
    
    RULES:
    - Video PoC ONLY for MCP-confirmed BUG classification
    - IDEMPOTENCY GUARD: Only ONE VideoPoC per finding_id
    - Video recording is OFF by default
    - Enable only on MCP BUG or human escalation
    """
    
    def __init__(self) -> None:
        # Idempotency guard: track generated PoCs by finding_id
        self._generated_pocs: dict[str, VideoPoC] = {}
    
    def has_poc(self, finding_id: str) -> bool:
        """Check if VideoPoC already exists for finding_id."""
        return finding_id in self._generated_pocs
    
    def get_poc(self, finding_id: str) -> Optional[VideoPoC]:
        """Get existing VideoPoC for finding_id if it exists."""
        return self._generated_pocs.get(finding_id)
    
    def generate(
        self,
        finding_id: str,
        mcp_result: MCPVerificationResult,
        evidence_bundle: EvidenceBundle,
    ) -> VideoPoC:
        """Generate Video PoC for confirmed BUG.
        
        Args:
            finding_id: Unique finding identifier
            mcp_result: MCP verification result (must be BUG)
            evidence_bundle: Evidence bundle with video content
        
        Returns:
            VideoPoC for the finding
        
        Raises:
            VideoPoCExistsError: If PoC already exists for finding_id
            ArchitecturalViolationError: If MCP classification is not BUG
        """
        # IDEMPOTENCY GUARD: Check if PoC already exists
        if self.has_poc(finding_id):
            raise VideoPoCExistsError(
                f"VideoPoC already exists for finding_id '{finding_id}' — "
                f"only ONE VideoPoC per finding allowed"
            )
        
        # Verify MCP classification is BUG
        if not mcp_result.is_bug:
            raise ArchitecturalViolationError(
                f"Cannot generate VideoPoC for non-BUG classification "
                f"'{mcp_result.classification.value}' — "
                f"Video PoC is ONLY for MCP-confirmed BUG"
            )
        
        # Verify video content exists
        if evidence_bundle.video is None:
            raise ValueError(
                "Evidence bundle does not contain video — "
                "enable video recording before generating PoC"
            )
        
        # Generate timestamps from execution trace
        timestamps = self._extract_timestamps(evidence_bundle.execution_trace)
        
        # Create VideoPoC
        poc = VideoPoC.create(
            finding_id=finding_id,
            video_artifact=evidence_bundle.video,
            execution_trace=evidence_bundle.execution_trace,
            timestamps=timestamps,
        )
        
        # Store for idempotency
        self._generated_pocs[finding_id] = poc
        
        return poc

    def _extract_timestamps(
        self,
        execution_trace: list[dict[str, Any]],
    ) -> list[tuple[float, str]]:
        """Extract timestamps from execution trace."""
        timestamps: list[tuple[float, str]] = []
        
        if not execution_trace:
            return timestamps
        
        # Get start time from first event
        first_event = execution_trace[0]
        start_time = datetime.fromisoformat(first_event.get("timestamp", ""))
        
        for event in execution_trace:
            event_time = datetime.fromisoformat(event.get("timestamp", ""))
            elapsed = (event_time - start_time).total_seconds()
            event_type = event.get("event_type", "unknown")
            timestamps.append((elapsed, event_type))
        
        return timestamps
    
    def should_enable_video(
        self,
        mcp_result: Optional[MCPVerificationResult] = None,
        human_escalation: bool = False,
    ) -> bool:
        """Determine if video recording should be enabled.
        
        Video is enabled ONLY for:
        - MCP-confirmed BUG classification
        - Human escalation request
        """
        if human_escalation:
            return True
        
        if mcp_result and mcp_result.is_bug:
            return True
        
        return False
    
    def get_all_pocs(self) -> dict[str, VideoPoC]:
        """Get all generated PoCs."""
        return dict(self._generated_pocs)
    
    def clear_poc(self, finding_id: str) -> bool:
        """Clear PoC for finding_id (for testing only).
        
        WARNING: This should only be used in tests.
        PoCs are immutable once created.
        """
        if finding_id in self._generated_pocs:
            del self._generated_pocs[finding_id]
            return True
        return False
