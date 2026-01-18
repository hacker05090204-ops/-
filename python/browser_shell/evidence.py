# PHASE-13 GOVERNANCE COMPLIANCE
# This module is part of Phase-13 (Controlled Bug Bounty Browser Shell)
#
# FORBIDDEN CAPABILITIES:
# - NO automation logic
# - NO execution authority
# - NO decision authority
# - NO learning or personalization
# - NO audit modification
# - NO scope expansion
# - NO session extension
# - NO batch approvals
# - NO scheduled actions
#
# MANDATORY DECLARATION:
# Phase-13 must not alter execution authority, human control,
# governance friction, audit invariants, or legal accountability.

"""
Evidence Capture for Phase-13 Browser Shell.

Requirements: 4.1, 4.2, 4.3 (Evidence Capture)

This module implements:
- TASK-5.1: Human-Initiated Evidence Capture
- TASK-5.2: Evidence Size Limits
- TASK-5.3: Evidence Content Restrictions

NO automatic capture. NO background capture. NO batch capture.
All evidence requires explicit human initiation and confirmation.
"""

from dataclasses import dataclass
from typing import Dict, Optional
import re
import uuid


# =============================================================================
# Result Dataclasses (Immutable)
# =============================================================================

@dataclass(frozen=True)
class CaptureResult:
    """Result of evidence capture attempt."""
    success: bool
    evidence_id: Optional[str] = None
    stored: bool = False
    error_message: Optional[str] = None


@dataclass(frozen=True)
class EvidencePreview:
    """Preview of evidence before storage."""
    preview_id: str
    evidence_type: str
    size_bytes: int
    stored: bool = False
    blocked: bool = False
    block_reason: str = ""
    exceeds_soft_limit: bool = False
    requires_size_confirmation: bool = False
    flagged_pii: bool = False
    flagged_bulk_data: bool = False
    requires_redaction_review: bool = False


@dataclass(frozen=True)
class StorageResult:
    """Result of evidence storage confirmation."""
    success: bool
    stored: bool = False
    evidence_id: Optional[str] = None
    error_message: Optional[str] = None


@dataclass(frozen=True)
class BudgetStatus:
    """Status of evidence budget for a session."""
    total_bytes: int
    used_bytes: int
    remaining_bytes: int


# =============================================================================
# TASK-5.1, 5.2, 5.3: Evidence Capture
# =============================================================================

class EvidenceCapture:
    """
    Human-initiated evidence capture with size and content restrictions.
    
    Per Requirement 4.1 (Evidence Initiation):
    - NO evidence captured without explicit human initiation
    - Evidence displayed for human review before storage
    - Human confirmation required before storing evidence
    
    Per Requirement 4.2 (Evidence Size Limits):
    - Size limits enforced by type
    - Soft limit exceeded requires human confirmation
    - Hard limit exceeded BLOCKS capture
    
    Per Requirement 4.3 (Evidence Content Restrictions):
    - Credentials detected → BLOCK storage
    - PII detected → FLAG for human redaction review
    - Bulk data patterns detected → FLAG for human review
    
    FORBIDDEN METHODS (not implemented):
    - auto_*, background_*, schedule_*, batch_*
    """
    
    # Size limits (TH-09 through TH-21)
    SCREENSHOT_SOFT_LIMIT = 2 * 1024 * 1024      # TH-09: 2MB
    SCREENSHOT_HARD_LIMIT = 5 * 1024 * 1024      # TH-10: 5MB
    RESPONSE_BODY_SOFT_LIMIT = 50 * 1024        # TH-11: 50KB
    RESPONSE_BODY_HARD_LIMIT = 200 * 1024       # TH-12: 200KB
    REQUEST_HEADERS_SOFT_LIMIT = 10 * 1024      # TH-13: 10KB
    REQUEST_HEADERS_HARD_LIMIT = 50 * 1024      # TH-14: 50KB
    VIDEO_CLIP_SOFT_LIMIT = 20 * 1024 * 1024    # TH-15: 20MB
    VIDEO_CLIP_HARD_LIMIT = 50 * 1024 * 1024    # TH-16: 50MB
    CONSOLE_LOG_SOFT_LIMIT = 100 * 1024         # TH-17: 100KB
    CONSOLE_LOG_HARD_LIMIT = 500 * 1024         # TH-18: 500KB
    NETWORK_TRACE_SOFT_LIMIT = 500 * 1024       # TH-19: 500KB
    NETWORK_TRACE_HARD_LIMIT = 2 * 1024 * 1024  # TH-20: 2MB
    SESSION_AGGREGATE_LIMIT = 100 * 1024 * 1024 # TH-21: 100MB
    
    # Credential patterns (BLOCK on detection)
    CREDENTIAL_PATTERNS = [
        rb'"password"\s*:\s*"[^"]+',
        rb"'password'\s*:\s*'[^']+",
        rb'password\s*=\s*[^\s&]+',
        rb'api_key\s*=\s*[^\s&]+',
        rb'apikey\s*=\s*[^\s&]+',
        rb'secret\s*=\s*[^\s&]+',
        rb'token\s*=\s*[^\s&]+',
        rb'bearer\s+[a-zA-Z0-9_\-\.]+',
        rb'sk_live_[a-zA-Z0-9]+',
        rb'sk_test_[a-zA-Z0-9]+',
    ]
    
    # PII patterns (FLAG for review)
    PII_PATTERNS = [
        rb'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # Email
        rb'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone number
        rb'\b\d{3}[-]?\d{2}[-]?\d{4}\b',    # SSN pattern
    ]
    
    # Bulk data threshold
    BULK_DATA_RECORD_THRESHOLD = 50
    
    def __init__(self, storage, hash_chain):
        """
        Initialize evidence capture.
        
        Args:
            storage: AuditStorage instance for logging
            hash_chain: HashChain instance for entry linking
        """
        self._storage = storage
        self._hash_chain = hash_chain
        # Pending previews (preview_id -> preview data)
        self._pending_previews: Dict[str, dict] = {}
        # Session usage tracking (session_id -> bytes used)
        self._session_usage: Dict[str, int] = {}
    
    def capture_screenshot(
        self,
        session_id: str,
        data: bytes,
        human_initiated: bool,
    ) -> CaptureResult:
        """
        Capture a screenshot.
        
        REQUIRES human_initiated=True.
        
        Args:
            session_id: Session identifier
            data: Screenshot data
            human_initiated: Must be True
            
        Returns:
            CaptureResult with status
        """
        if not human_initiated:
            return CaptureResult(
                success=False,
                error_message="Evidence capture requires human initiation"
            )
        
        # Use initiate_capture flow
        preview = self.initiate_capture(
            session_id=session_id,
            evidence_type="SCREENSHOT",
            data=data,
        )
        
        if preview.blocked:
            return CaptureResult(
                success=False,
                error_message=preview.block_reason
            )
        
        return CaptureResult(
            success=True,
            evidence_id=preview.preview_id,
            stored=False,  # Not stored until confirmed
        )
    
    def initiate_capture(
        self,
        session_id: str,
        evidence_type: str,
        data: bytes,
    ) -> EvidencePreview:
        """
        Initiate evidence capture (returns preview, not stored).
        
        Per Requirement 4.1:
        - Evidence displayed for human review before storage
        
        Args:
            session_id: Session identifier
            evidence_type: Type of evidence
            data: Evidence data
            
        Returns:
            EvidencePreview for human review
        """
        preview_id = str(uuid.uuid4())
        size_bytes = len(data)
        
        # Check for credentials (BLOCK)
        if self._contains_credentials(data):
            self._log_audit_entry(
                entry_id=preview_id,
                action_type="EVIDENCE_BLOCKED",
                initiator="SYSTEM",
                session_id=session_id,
                action_details=f"Evidence blocked: credential pattern detected in {evidence_type}",
                outcome="BLOCKED",
            )
            return EvidencePreview(
                preview_id=preview_id,
                evidence_type=evidence_type,
                size_bytes=size_bytes,
                blocked=True,
                block_reason="Credential pattern detected - evidence blocked",
            )
        
        # Check size limits
        soft_limit, hard_limit = self._get_limits(evidence_type)
        
        if size_bytes > hard_limit:
            self._log_audit_entry(
                entry_id=preview_id,
                action_type="EVIDENCE_SIZE_EXCEEDED",
                initiator="SYSTEM",
                session_id=session_id,
                action_details=f"Evidence blocked: {evidence_type} exceeds hard limit ({size_bytes} > {hard_limit})",
                outcome="BLOCKED",
            )
            return EvidencePreview(
                preview_id=preview_id,
                evidence_type=evidence_type,
                size_bytes=size_bytes,
                blocked=True,
                block_reason=f"Evidence exceeds hard limit ({size_bytes} bytes > {hard_limit} bytes)",
            )
        
        exceeds_soft = size_bytes > soft_limit
        
        # Check for PII (FLAG)
        flagged_pii = self._contains_pii(data)
        
        # Check for bulk data (FLAG)
        flagged_bulk = self._contains_bulk_data(data)
        
        # Store pending preview
        self._pending_previews[preview_id] = {
            "session_id": session_id,
            "evidence_type": evidence_type,
            "data": data,
            "size_bytes": size_bytes,
        }
        
        return EvidencePreview(
            preview_id=preview_id,
            evidence_type=evidence_type,
            size_bytes=size_bytes,
            stored=False,
            blocked=False,
            exceeds_soft_limit=exceeds_soft,
            requires_size_confirmation=exceeds_soft,
            flagged_pii=flagged_pii,
            flagged_bulk_data=flagged_bulk,
            requires_redaction_review=flagged_pii,
        )
    
    def confirm_storage(
        self,
        preview_id: str,
        human_confirmed: bool,
    ) -> StorageResult:
        """
        Confirm evidence storage after human review.
        
        Per Requirement 4.1:
        - Human confirmation required before storing evidence
        
        Args:
            preview_id: Preview identifier from initiate_capture
            human_confirmed: Must be True to store
            
        Returns:
            StorageResult with status
        """
        if not human_confirmed:
            return StorageResult(
                success=False,
                error_message="Human confirmation required to store evidence"
            )
        
        if preview_id not in self._pending_previews:
            return StorageResult(
                success=False,
                error_message="Preview not found or already processed"
            )
        
        preview_data = self._pending_previews.pop(preview_id)
        session_id = preview_data["session_id"]
        evidence_type = preview_data["evidence_type"]
        size_bytes = preview_data["size_bytes"]
        
        # Update session usage
        if session_id not in self._session_usage:
            self._session_usage[session_id] = 0
        self._session_usage[session_id] += size_bytes
        
        # Log to audit trail
        evidence_id = str(uuid.uuid4())
        self._log_audit_entry(
            entry_id=evidence_id,
            action_type="EVIDENCE_CAPTURED",
            initiator="HUMAN",
            session_id=session_id,
            action_details=f"Evidence stored: {evidence_type}, {size_bytes} bytes",
            outcome="SUCCESS",
        )
        
        return StorageResult(
            success=True,
            stored=True,
            evidence_id=evidence_id,
        )
    
    def get_remaining_budget(self, session_id: str) -> BudgetStatus:
        """
        Get remaining evidence budget for a session.
        
        Per Requirement 4.2:
        - Remaining evidence budget displayed to human
        
        Args:
            session_id: Session identifier
            
        Returns:
            BudgetStatus with usage information
        """
        used = self._session_usage.get(session_id, 0)
        remaining = self.SESSION_AGGREGATE_LIMIT - used
        
        return BudgetStatus(
            total_bytes=self.SESSION_AGGREGATE_LIMIT,
            used_bytes=used,
            remaining_bytes=max(0, remaining),
        )
    
    def _get_limits(self, evidence_type: str) -> tuple:
        """Get soft and hard limits for evidence type."""
        limits = {
            "SCREENSHOT": (self.SCREENSHOT_SOFT_LIMIT, self.SCREENSHOT_HARD_LIMIT),
            "RESPONSE_BODY": (self.RESPONSE_BODY_SOFT_LIMIT, self.RESPONSE_BODY_HARD_LIMIT),
            "REQUEST_HEADERS": (self.REQUEST_HEADERS_SOFT_LIMIT, self.REQUEST_HEADERS_HARD_LIMIT),
            "VIDEO_CLIP": (self.VIDEO_CLIP_SOFT_LIMIT, self.VIDEO_CLIP_HARD_LIMIT),
            "CONSOLE_LOG": (self.CONSOLE_LOG_SOFT_LIMIT, self.CONSOLE_LOG_HARD_LIMIT),
            "NETWORK_TRACE": (self.NETWORK_TRACE_SOFT_LIMIT, self.NETWORK_TRACE_HARD_LIMIT),
        }
        return limits.get(evidence_type, (self.RESPONSE_BODY_SOFT_LIMIT, self.RESPONSE_BODY_HARD_LIMIT))
    
    def _contains_credentials(self, data: bytes) -> bool:
        """Check if data contains credential patterns."""
        for pattern in self.CREDENTIAL_PATTERNS:
            if re.search(pattern, data, re.IGNORECASE):
                return True
        return False
    
    def _contains_pii(self, data: bytes) -> bool:
        """Check if data contains PII patterns."""
        for pattern in self.PII_PATTERNS:
            if re.search(pattern, data):
                return True
        return False
    
    def _contains_bulk_data(self, data: bytes) -> bool:
        """Check if data contains bulk data patterns."""
        # Count JSON-like record patterns
        record_count = len(re.findall(rb'\{[^{}]+\}', data))
        return record_count >= self.BULK_DATA_RECORD_THRESHOLD
    
    def _log_audit_entry(
        self,
        entry_id: str,
        action_type: str,
        initiator: str,
        session_id: str,
        action_details: str,
        outcome: str,
    ) -> None:
        """Log an entry to the audit trail."""
        from browser_shell.audit_types import AuditEntry
        from browser_shell.hash_chain import HashChain
        
        # Get previous hash from last entry
        last_entry = self._storage.get_last_entry()
        previous_hash = last_entry.entry_hash if last_entry else HashChain.GENESIS_HASH
        
        # Get timestamp from external source
        timestamp = self._hash_chain.get_external_timestamp()
        
        # Compute entry hash
        entry_hash = self._hash_chain.compute_entry_hash(
            entry_id=entry_id,
            timestamp=timestamp,
            previous_hash=previous_hash,
            action_type=action_type,
            initiator=initiator,
            session_id=session_id,
            scope_hash="",
            action_details=action_details,
            outcome=outcome,
        )
        
        # Create and store entry
        entry = AuditEntry(
            entry_id=entry_id,
            timestamp=timestamp,
            previous_hash=previous_hash,
            action_type=action_type,
            initiator=initiator,
            session_id=session_id,
            scope_hash="",
            action_details=action_details,
            outcome=outcome,
            entry_hash=entry_hash,
        )
        
        self._storage.append(entry)
