"""
Phase-9 Data Models

All data models are FROZEN (immutable) dataclasses to ensure:
- Observations cannot be modified after creation
- Hints cannot be altered
- Draft reports are tracked by hash
- Human confirmations are tamper-evident

SAFETY CONSTRAINTS (NON-NEGOTIABLE):
- All models are frozen=True
- NO automation fields
- NO execution fields
- NO classification fields (human decides)
- NO severity assignment fields (human decides)
- NO submission fields (human submits)
- All outputs include human_confirmation_required = True

EXPLICIT NON-GOALS:
- NO execute_payload, inject_traffic, modify_request methods
- NO classify_bug, is_vulnerability, determine_severity methods
- NO submit_report, auto_submit, guided_submission methods
- NO generate_poc, create_exploit methods
- NO record_video, auto_evidence methods
- NO chain_findings, auto_correlate methods

Phase-9 is ASSISTIVE ONLY. Human always clicks YES/NO.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Any
import hashlib


# ============================================================================
# Core Enums
# ============================================================================

class HintType(Enum):
    """Types of hints the assistant can provide."""
    PATTERN_REMINDER = "pattern_reminder"      # Reminds of known vulnerability patterns
    DUPLICATE_WARNING = "duplicate_warning"    # Warns of potential duplicate
    SCOPE_WARNING = "scope_warning"            # Warns about scope boundaries
    CONTEXT_INFO = "context_info"              # Contextual information
    CHECKLIST_ITEM = "checklist_item"          # Testing checklist reminder
    HISTORICAL_NOTE = "historical_note"        # Note from historical data


class HintSeverity(Enum):
    """
    Severity of hints - NOT vulnerability severity.
    
    This indicates how important the hint is for the human to review,
    NOT the severity of any potential vulnerability.
    """
    INFO = "info"           # Informational, low priority
    NOTICE = "notice"       # Worth noting
    ATTENTION = "attention" # Should review before proceeding


class ObservationType(Enum):
    """Types of browser observations."""
    URL_NAVIGATION = "url_navigation"
    DOM_CONTENT = "dom_content"
    FORM_DETECTED = "form_detected"
    PARAMETER_DETECTED = "parameter_detected"
    RESPONSE_HEADER = "response_header"
    COOKIE_OBSERVED = "cookie_observed"
    ERROR_MESSAGE = "error_message"
    REDIRECT_OBSERVED = "redirect_observed"


class ConfirmationStatus(Enum):
    """Status of human confirmation."""
    PENDING = "pending"       # Awaiting human response
    CONFIRMED = "confirmed"   # Human clicked YES
    REJECTED = "rejected"     # Human clicked NO
    EXPIRED = "expired"       # Confirmation window expired


# ============================================================================
# Browser Observation Types
# ============================================================================

@dataclass(frozen=True)
class BrowserObservation:
    """
    Immutable record of a browser observation.
    
    Phase-9 OBSERVES browser activity but NEVER:
    - Modifies requests
    - Injects payloads
    - Executes JavaScript
    - Intercepts traffic
    
    This is PASSIVE observation only.
    """
    observation_id: str
    observation_type: ObservationType
    timestamp: datetime
    url: str
    content: str                          # What was observed
    metadata: tuple[tuple[str, str], ...]  # Additional context as frozen tuples
    
    # Safety markers
    is_passive_observation: bool = True   # Always True - we only observe
    no_modification_performed: bool = True # Always True - we never modify


# ============================================================================
# Hint Types
# ============================================================================

@dataclass(frozen=True)
class ContextHint:
    """
    Immutable hint providing context to the human.
    
    This is a HINT only. It does NOT:
    - Classify vulnerabilities
    - Assign severity
    - Recommend actions
    - Make decisions
    
    Human interprets the hint and decides what to do.
    """
    hint_id: str
    hint_type: HintType
    hint_severity: HintSeverity
    title: str
    description: str
    related_observation_id: Optional[str]
    timestamp: datetime
    
    # Safety markers - ALL hints require human confirmation
    human_confirmation_required: bool = True  # Always True
    is_advisory_only: bool = True             # Always True
    no_auto_action: bool = True               # Always True


@dataclass(frozen=True)
class DuplicateHint:
    """
    Immutable warning about potential duplicate finding.
    
    This is a WARNING only. It does NOT:
    - Block any action
    - Auto-reject findings
    - Confirm duplication
    
    Human decides whether this is actually a duplicate.
    
    IMPORTANT: Similarity is HEURISTIC, not authoritative.
    - Scores are advisory only
    - No score implies duplication certainty
    - Human verification is always required
    """
    hint_id: str
    current_url: str
    similar_finding_id: Optional[str]
    similarity_score: float               # ADVISORY ONLY - heuristic
    similarity_reason: str
    timestamp: datetime
    
    # Safety markers
    human_confirmation_required: bool = True  # Always True
    is_heuristic: bool = True                 # Always True - never authoritative
    does_not_block: bool = True               # Always True - never blocks
    similarity_disclaimer: str = "Heuristic estimate - human verification required"


@dataclass(frozen=True)
class ScopeWarning:
    """
    Immutable warning about scope boundaries.
    
    This is a WARNING only. It does NOT:
    - Block navigation
    - Prevent testing
    - Make scope decisions
    
    Human decides whether to proceed.
    """
    warning_id: str
    url: str
    scope_status: str                     # "in_scope", "out_of_scope", "ambiguous"
    warning_message: str
    authorization_reference: Optional[str]
    timestamp: datetime
    
    # Safety markers
    human_confirmation_required: bool = True  # Always True
    does_not_block: bool = True               # Always True - never blocks
    is_advisory_only: bool = True             # Always True


# ============================================================================
# Draft Report Types
# ============================================================================

@dataclass(frozen=True)
class DraftReportContent:
    """
    Immutable draft report content for human review.
    
    This is a DRAFT only. It:
    - MUST be reviewed by human
    - MUST be edited by human if needed
    - MUST be explicitly confirmed by human
    - Is NEVER auto-submitted
    
    Human copies, edits, and submits manually.
    
    FORBIDDEN FIELDS (do not add):
    - severity (human assigns)
    - classification (human decides)
    - cvss_score (human calculates)
    - auto_submit
    - submit_to_platform
    """
    draft_id: str
    title_suggestion: str                 # SUGGESTION only
    description_template: str             # TEMPLATE only - human edits
    observed_behavior: str                # What was observed
    related_observations: tuple[str, ...] # Observation IDs
    timestamp: datetime
    content_hash: str                     # SHA-256 for integrity
    
    # Safety markers
    human_must_review: bool = True        # Always True
    human_must_edit: bool = True          # Always True - never submit as-is
    human_must_confirm: bool = True       # Always True
    is_template_only: bool = True         # Always True - not final report
    no_auto_submission: bool = True       # Always True
    no_severity_assigned: str = "Human must assign severity"
    no_classification_assigned: str = "Human must classify"
    
    @staticmethod
    def compute_hash(
        title: str,
        description: str,
        observed_behavior: str,
        observations: tuple[str, ...],
    ) -> str:
        """Compute SHA-256 hash of draft content."""
        sorted_obs = sorted(observations)
        content = f"{title}|{description}|{observed_behavior}|{sorted_obs}"
        return hashlib.sha256(content.encode()).hexdigest()


# ============================================================================
# Human Confirmation Types
# ============================================================================

@dataclass(frozen=True)
class HumanConfirmation:
    """
    Immutable record of human confirmation.
    
    Every assistant output requires explicit human confirmation.
    This record proves the human clicked YES or NO.
    
    SECURITY: Confirmations are:
    - Immutable (frozen dataclass)
    - Timestamped
    - Hashed for integrity
    - Single-use (cannot be replayed)
    """
    confirmation_id: str
    output_id: str                        # ID of the output being confirmed
    output_type: str                      # Type of output (hint, draft, etc.)
    status: ConfirmationStatus
    confirmed_by: str                     # Human identifier
    confirmed_at: datetime
    confirmation_hash: str                # SHA-256 for integrity
    
    # Safety markers
    is_explicit_human_action: bool = True # Always True
    is_single_use: bool = True            # Always True - no replay
    
    @staticmethod
    def compute_hash(
        output_id: str,
        output_type: str,
        status: ConfirmationStatus,
        confirmed_by: str,
        confirmed_at: datetime,
    ) -> str:
        """Compute SHA-256 hash of confirmation."""
        content = (
            f"{output_id}|{output_type}|{status.value}|"
            f"{confirmed_by}|{confirmed_at.isoformat()}"
        )
        return hashlib.sha256(content.encode()).hexdigest()


# ============================================================================
# Assistant Output Types
# ============================================================================

@dataclass(frozen=True)
class AssistantOutput:
    """
    Immutable container for all assistant outputs.
    
    Every output from the assistant is wrapped in this container
    to ensure:
    - Human confirmation is required
    - Output is tracked
    - Output cannot be modified
    
    FORBIDDEN FIELDS (do not add):
    - auto_action
    - execute_on_confirm
    - submit_on_confirm
    - bypass_confirmation
    """
    output_id: str
    output_type: str                      # "hint", "duplicate_warning", "scope_warning", "draft"
    content: Any                          # The actual output (ContextHint, DuplicateHint, etc.)
    timestamp: datetime
    confirmation_status: ConfirmationStatus
    confirmation_id: Optional[str]        # Set when confirmed
    
    # Safety markers - EVERY output requires confirmation
    requires_human_confirmation: bool = True  # Always True
    no_auto_action: bool = True               # Always True
    is_advisory_only: bool = True             # Always True


# ============================================================================
# FORBIDDEN TYPES - DO NOT IMPLEMENT
# ============================================================================
# The following types are FORBIDDEN and must NEVER be added:
#
# - PayloadExecution - Phase-9 does NOT execute payloads
# - TrafficInjection - Phase-9 does NOT inject traffic
# - RequestModification - Phase-9 does NOT modify requests
# - AutoClassification - Phase-9 does NOT classify bugs
# - SeverityAssignment - Phase-9 does NOT assign severity
# - AutoSubmission - Phase-9 does NOT submit reports
# - PoCGeneration - Phase-9 does NOT generate PoCs
# - VideoRecording - Phase-9 does NOT record video
# - FindingChain - Phase-9 does NOT chain findings
# - AutoConfirmation - Phase-9 does NOT auto-confirm
# ============================================================================
