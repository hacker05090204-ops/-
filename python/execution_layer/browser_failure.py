"""
Browser Failure Handler for Execution Layer

Phase-4.1 Track #5 Implementation

This module provides failure handling for browser operations:
- Failure type classification
- Recovery strategy mapping
- Partial evidence preservation
- Audit trail integration

CRITICAL CONSTRAINTS:
- Exception propagation UNCHANGED
- Human approval NEVER bypassed
- Recovery is for evidence preservation ONLY
- No automatic retry without re-approval

OBSERVE ONLY — NO STEALTH, NO EVASION, NO BYPASS.

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any, Callable
import hashlib
import json
import logging

from execution_layer.errors import (
    BrowserCrashError,
    NavigationFailureError,
    CSPBlockError,
    BrowserSessionError,
    ExecutionLayerError,
)
from execution_layer.types import SafeAction, EvidenceBundle, EvidenceArtifact, EvidenceType


logger = logging.getLogger(__name__)


class FailureType(str, Enum):
    """Classification of browser failure types."""
    BROWSER_CRASH = "browser_crash"
    NAVIGATION_FAILURE = "navigation_failure"
    CSP_BLOCK = "csp_block"
    SESSION_ERROR = "session_error"
    UNKNOWN = "unknown"


class RecoveryStrategy(str, Enum):
    """Recovery strategies for different failure types.
    
    NOTE: Recovery is for evidence preservation ONLY.
    NO automatic retry without human re-approval.
    """
    RESTART_BROWSER = "restart_browser"  # For crashes
    CLEAR_CACHE = "clear_cache"  # For navigation failures
    NO_RETRY = "no_retry"  # For CSP blocks (no bypass)
    CLEANUP_ONLY = "cleanup_only"  # For session errors


@dataclass
class FailureContext:
    """Context information about a browser failure."""
    failure_id: str
    failure_type: FailureType
    error: ExecutionLayerError
    session_id: str
    execution_id: str
    action: Optional[SafeAction]
    timestamp: datetime
    recovery_strategy: RecoveryStrategy
    evidence_preserved: list[dict[str, Any]] = field(default_factory=list)
    audit_recorded: bool = False
    
    def to_audit_record(self) -> dict[str, Any]:
        """Convert to audit record format."""
        return {
            "failure_id": self.failure_id,
            "failure_type": self.failure_type.value,
            "error_type": type(self.error).__name__,
            "error_message": str(self.error),
            "session_id": self.session_id,
            "execution_id": self.execution_id,
            "action_id": self.action.action_id if self.action else None,
            "timestamp": self.timestamp.isoformat(),
            "recovery_strategy": self.recovery_strategy.value,
            "evidence_count": len(self.evidence_preserved),
        }


@dataclass
class PartialEvidence:
    """Evidence captured before failure occurred."""
    evidence_type: str
    content_hash: str
    captured_at: datetime
    file_path: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BrowserFailureHandler:
    """Handler for browser failures with evidence preservation.
    
    CRITICAL: This handler does NOT implement automatic retry.
    Recovery strategies are for evidence preservation and cleanup ONLY.
    Any retry requires new human approval.
    
    Usage:
        handler = BrowserFailureHandler(audit_callback=audit_log.add_record)
        
        try:
            await browser.execute_action(session_id, action)
        except BrowserCrashError as e:
            context = handler.handle_failure(e, session_id, execution_id, action)
            # Evidence preserved, audit recorded
            raise  # ALWAYS re-raise - no suppression
    """
    
    # Mapping from error types to failure types
    ERROR_TO_FAILURE_TYPE: dict[type, FailureType] = {
        BrowserCrashError: FailureType.BROWSER_CRASH,
        NavigationFailureError: FailureType.NAVIGATION_FAILURE,
        CSPBlockError: FailureType.CSP_BLOCK,
        BrowserSessionError: FailureType.SESSION_ERROR,
    }
    
    # Mapping from failure types to recovery strategies
    FAILURE_TO_STRATEGY: dict[FailureType, RecoveryStrategy] = {
        FailureType.BROWSER_CRASH: RecoveryStrategy.RESTART_BROWSER,
        FailureType.NAVIGATION_FAILURE: RecoveryStrategy.CLEAR_CACHE,
        FailureType.CSP_BLOCK: RecoveryStrategy.NO_RETRY,  # NO BYPASS
        FailureType.SESSION_ERROR: RecoveryStrategy.CLEANUP_ONLY,
        FailureType.UNKNOWN: RecoveryStrategy.CLEANUP_ONLY,
    }
    
    def __init__(
        self,
        audit_callback: Optional[Callable[[dict[str, Any]], str]] = None,
    ) -> None:
        """Initialize failure handler.
        
        Args:
            audit_callback: Optional callback to record failures to audit trail.
                           Signature: (record: dict) -> record_hash: str
        """
        self._audit_callback = audit_callback
        self._failure_count = 0
        self._preserved_evidence: list[PartialEvidence] = []
    
    def classify_failure(self, error: Exception) -> FailureType:
        """Classify an error into a failure type.
        
        Args:
            error: The exception that occurred
            
        Returns:
            FailureType classification
        """
        for error_type, failure_type in self.ERROR_TO_FAILURE_TYPE.items():
            if isinstance(error, error_type):
                return failure_type
        return FailureType.UNKNOWN
    
    def get_recovery_strategy(self, failure_type: FailureType) -> RecoveryStrategy:
        """Get recovery strategy for a failure type.
        
        NOTE: Recovery strategies are for evidence preservation ONLY.
        NO automatic retry without human re-approval.
        
        Args:
            failure_type: The classified failure type
            
        Returns:
            RecoveryStrategy for the failure type
        """
        return self.FAILURE_TO_STRATEGY.get(failure_type, RecoveryStrategy.CLEANUP_ONLY)
    
    def handle_failure(
        self,
        error: ExecutionLayerError,
        session_id: str,
        execution_id: str,
        action: Optional[SafeAction] = None,
        partial_evidence: Optional[list[dict[str, Any]]] = None,
    ) -> FailureContext:
        """Handle a browser failure.
        
        This method:
        1. Classifies the failure type
        2. Determines recovery strategy
        3. Preserves any partial evidence
        4. Records to audit trail (if callback provided)
        
        CRITICAL: This method does NOT suppress the error.
        The caller MUST re-raise the error after calling this.
        
        Args:
            error: The exception that occurred
            session_id: Browser session ID
            execution_id: Execution ID for evidence grouping
            action: The action that was being executed (if any)
            partial_evidence: Any evidence captured before failure
            
        Returns:
            FailureContext with failure details and preserved evidence
        """
        self._failure_count += 1
        
        # Classify failure
        failure_type = self.classify_failure(error)
        
        # Get recovery strategy
        recovery_strategy = self.get_recovery_strategy(failure_type)
        
        # Generate failure ID
        failure_id = self._generate_failure_id(session_id, execution_id)
        
        # Create failure context
        context = FailureContext(
            failure_id=failure_id,
            failure_type=failure_type,
            error=error,
            session_id=session_id,
            execution_id=execution_id,
            action=action,
            timestamp=datetime.now(timezone.utc),
            recovery_strategy=recovery_strategy,
        )
        
        # Preserve partial evidence
        if partial_evidence:
            context.evidence_preserved = self._preserve_evidence(partial_evidence)
        
        # Record to audit trail
        if self._audit_callback:
            try:
                audit_record = context.to_audit_record()
                self._audit_callback(audit_record)
                context.audit_recorded = True
            except Exception as audit_error:
                logger.error(f"Failed to record failure to audit: {audit_error}")
        
        logger.warning(
            f"Browser failure handled: type={failure_type.value}, "
            f"strategy={recovery_strategy.value}, "
            f"session={session_id}, execution={execution_id}"
        )
        
        return context
    
    def preserve_evidence_on_failure(
        self,
        evidence_items: list[dict[str, Any]],
    ) -> list[PartialEvidence]:
        """Preserve evidence items captured before failure.
        
        Args:
            evidence_items: List of evidence items to preserve
            
        Returns:
            List of PartialEvidence objects
        """
        preserved = []
        for item in evidence_items:
            try:
                partial = PartialEvidence(
                    evidence_type=item.get("type", "unknown"),
                    content_hash=item.get("content_hash", ""),
                    captured_at=datetime.fromisoformat(item.get("captured_at", datetime.now(timezone.utc).isoformat())),
                    file_path=item.get("file_path"),
                    metadata=item.get("metadata", {}),
                )
                preserved.append(partial)
                self._preserved_evidence.append(partial)
            except Exception as e:
                logger.error(f"Failed to preserve evidence item: {e}")
        
        return preserved
    
    def _preserve_evidence(
        self,
        evidence_items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Internal method to preserve evidence and return as dicts."""
        preserved = self.preserve_evidence_on_failure(evidence_items)
        return [
            {
                "type": p.evidence_type,
                "content_hash": p.content_hash,
                "captured_at": p.captured_at.isoformat(),
                "file_path": p.file_path,
            }
            for p in preserved
        ]
    
    def _generate_failure_id(self, session_id: str, execution_id: str) -> str:
        """Generate unique failure ID."""
        content = f"{session_id}:{execution_id}:{self._failure_count}:{datetime.now(timezone.utc).isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    @property
    def failure_count(self) -> int:
        """Get total number of failures handled."""
        return self._failure_count
    
    @property
    def preserved_evidence_count(self) -> int:
        """Get total number of evidence items preserved."""
        return len(self._preserved_evidence)
    
    def get_preserved_evidence(self) -> list[PartialEvidence]:
        """Get all preserved evidence items."""
        return list(self._preserved_evidence)
    
    def clear_preserved_evidence(self) -> None:
        """Clear preserved evidence (for cleanup)."""
        self._preserved_evidence.clear()
