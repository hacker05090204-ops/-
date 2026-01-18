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
#
# CRITICAL GOVERNANCE CLARIFICATION:
# Decision Point tracking is COUNTING ONLY, LOGGING ONLY, VALIDATION ONLY.
# Decision tracking MUST NOT: interpret, score, recommend, infer, store patterns,
# create memory, create heuristics, or adapt behavior.
# A "Decision Point" is a STRUCTURAL EVENT, not a semantic judgment.

"""
Human Decision Framework for Phase-13 Browser Shell.

Requirements: 3.1, 3.2, 3.3 (Human Decision)

This module implements:
- TASK-4.1: Decision Point Tracking (counting, logging, validation ONLY)
- TASK-4.2: Confirmation System (frequency limits, rubber-stamp detection)
- TASK-4.3: Attribution System (HUMAN vs SYSTEM initiator)

NO interpretation. NO scoring. NO recommendations. NO inference.
NO pattern storage. NO memory. NO heuristics. NO behavior adaptation.
"""

from dataclasses import dataclass
from typing import List, Optional
import time
import uuid


# =============================================================================
# Result Dataclasses (Immutable)
# =============================================================================

@dataclass(frozen=True)
class DecisionResult:
    """Result of recording a decision point."""
    valid: bool
    decision_id: Optional[str] = None
    error_message: Optional[str] = None


@dataclass(frozen=True)
class RatioStatus:
    """Status of decision point ratio check."""
    ratio: float
    decision_count: int
    state_change_count: int
    flagged: bool


@dataclass(frozen=True)
class RepetitionStatus:
    """Status of repetition check."""
    flagged: bool
    most_common_option: Optional[str] = None
    most_common_percentage: float = 0.0


@dataclass(frozen=True)
class ConfirmationResult:
    """Result of recording a confirmation."""
    valid: bool
    confirmation_id: Optional[str] = None
    flagged_rubber_stamp: bool = False
    error_message: Optional[str] = None


@dataclass(frozen=True)
class FrequencyStatus:
    """Status of confirmation frequency check."""
    paused: bool
    confirmations_in_window: int
    window_seconds: int
    max_allowed: int


@dataclass(frozen=True)
class AttributionResult:
    """Result of attribution validation."""
    valid: bool
    error_message: Optional[str] = None


# =============================================================================
# TASK-4.1: Decision Point Tracking
# =============================================================================

class DecisionTracker:
    """
    Tracks decision points for governance compliance.
    
    COUNTING ONLY. LOGGING ONLY. VALIDATION ONLY.
    
    NO interpretation. NO scoring. NO recommendations.
    NO inference. NO pattern storage. NO memory.
    NO heuristics. NO behavior adaptation.
    """
    
    def __init__(self, storage, hash_chain):
        """
        Initialize decision tracker.
        
        Args:
            storage: AuditStorage instance for logging
            hash_chain: HashChain instance for entry linking
        """
        self._storage = storage
        self._hash_chain = hash_chain
        # Per-session counters (counting only, no patterns)
        self._decision_counts: dict = {}
        self._state_change_counts: dict = {}
        # Per-session option selections (for repetition check only)
        self._option_selections: dict = {}

    def record_decision_point(
        self,
        session_id: str,
        options_presented: List[str],
        option_selected: str,
    ) -> DecisionResult:
        """
        Record a decision point.
        
        A decision point requires:
        - At least 2 options presented
        - Selection from presented options
        
        COUNTING ONLY. LOGGING ONLY. VALIDATION ONLY.
        
        Args:
            session_id: Session identifier
            options_presented: List of options shown to human
            option_selected: Option chosen by human
            
        Returns:
            DecisionResult with validation status
        """
        # Validate: requires at least 2 options
        if len(options_presented) < 2:
            return DecisionResult(
                valid=False,
                error_message="Decision point requires at least 2 options"
            )
        
        # Validate: selection must be from presented options
        if option_selected not in options_presented:
            return DecisionResult(
                valid=False,
                error_message="Selected option not in presented options"
            )
        
        # Generate decision ID
        decision_id = str(uuid.uuid4())
        
        # Increment counter (counting only)
        if session_id not in self._decision_counts:
            self._decision_counts[session_id] = 0
            self._option_selections[session_id] = []
        
        self._decision_counts[session_id] += 1
        self._option_selections[session_id].append(option_selected)
        
        # Log to audit trail (logging only)
        self._log_audit_entry(
            entry_id=decision_id,
            action_type="DECISION_POINT",
            initiator="HUMAN",  # Decision points are HUMAN initiated
            session_id=session_id,
            action_details=f"Options: {options_presented}, Selected: {option_selected}",
            outcome="SUCCESS",
        )
        
        return DecisionResult(valid=True, decision_id=decision_id)
    
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
    
    def get_decision_count(self, session_id: str) -> int:
        """
        Get decision count for a session.
        
        COUNTING ONLY.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Number of decision points recorded
        """
        return self._decision_counts.get(session_id, 0)
    
    def record_state_change(self, session_id: str) -> None:
        """
        Record a state change for ratio tracking.
        
        COUNTING ONLY. LOGGING ONLY.
        
        Args:
            session_id: Session identifier
        """
        if session_id not in self._state_change_counts:
            self._state_change_counts[session_id] = 0
        
        self._state_change_counts[session_id] += 1
        
        # Log to audit trail (logging only)
        entry_id = str(uuid.uuid4())
        
        self._log_audit_entry(
            entry_id=entry_id,
            action_type="STATE_CHANGE",
            initiator="SYSTEM",  # State change logging is SYSTEM
            session_id=session_id,
            action_details="State change recorded",
            outcome="SUCCESS",
        )
    
    def check_decision_ratio(self, session_id: str) -> RatioStatus:
        """
        Check decision point ratio for a session.
        
        VALIDATION ONLY. Flags if ratio < 1:1.
        
        Args:
            session_id: Session identifier
            
        Returns:
            RatioStatus with ratio and flag status
        """
        decision_count = self._decision_counts.get(session_id, 0)
        state_change_count = self._state_change_counts.get(session_id, 0)
        
        if state_change_count == 0:
            # No state changes, ratio is infinite (good)
            return RatioStatus(
                ratio=float('inf'),
                decision_count=decision_count,
                state_change_count=state_change_count,
                flagged=False
            )
        
        ratio = decision_count / state_change_count
        
        # Flag if ratio < 1:1 (TH-03)
        flagged = ratio < 1.0
        
        return RatioStatus(
            ratio=ratio,
            decision_count=decision_count,
            state_change_count=state_change_count,
            flagged=flagged
        )
    
    def check_repetition(self, session_id: str) -> RepetitionStatus:
        """
        Check for repetitive option selection.
        
        VALIDATION ONLY. Flags if >95% same option (TH-22).
        
        Args:
            session_id: Session identifier
            
        Returns:
            RepetitionStatus with flag status
        """
        selections = self._option_selections.get(session_id, [])
        
        if len(selections) < 2:
            return RepetitionStatus(flagged=False)
        
        # Count occurrences (counting only, no pattern inference)
        counts: dict = {}
        for option in selections:
            counts[option] = counts.get(option, 0) + 1
        
        # Find most common
        most_common = max(counts.keys(), key=lambda k: counts[k])
        most_common_count = counts[most_common]
        percentage = most_common_count / len(selections)
        
        # Flag if >=95% same option (TH-22)
        flagged = percentage >= 0.95
        
        return RepetitionStatus(
            flagged=flagged,
            most_common_option=most_common,
            most_common_percentage=percentage
        )


# =============================================================================
# TASK-4.2: Confirmation System
# =============================================================================

class ConfirmationSystem:
    """
    Manages confirmation requirements for significant actions.
    
    Implements:
    - Confirmation requirements by action type
    - Frequency limits (TH-04: 1 per 30 sec average over 5-min window)
    - Rubber-stamp detection (TH-05: <1 sec response flagged)
    
    NO automation. NO execution authority.
    """
    
    # TH-04: 1 per 30 seconds average over 5-minute window
    # 5 minutes = 300 seconds, 1 per 30 sec = 10 confirmations max
    WINDOW_SECONDS = 300
    MAX_CONFIRMATIONS_PER_WINDOW = 10
    
    # TH-05: Response time threshold for rubber-stamp detection
    RUBBER_STAMP_THRESHOLD_SECONDS = 1.0
    
    # Actions requiring confirmation
    CONFIRMATION_REQUIRED_ACTIONS = frozenset([
        "SCOPE_BOUNDARY",
        "EVIDENCE_CAPTURE",
        "REPORT_OPERATION",
        "SESSION_MANAGEMENT",
    ])
    
    # Actions NOT requiring confirmation
    CONFIRMATION_EXEMPT_ACTIONS = frozenset([
        "ROUTINE_NAVIGATION",
    ])
    
    def __init__(self, storage, hash_chain):
        """
        Initialize confirmation system.
        
        Args:
            storage: AuditStorage instance for logging
            hash_chain: HashChain instance for entry linking
        """
        self._storage = storage
        self._hash_chain = hash_chain
        # Per-session confirmation timestamps (for frequency check)
        self._confirmation_timestamps: dict = {}
    
    def requires_confirmation(self, action_type: str) -> bool:
        """
        Check if action type requires confirmation.
        
        VALIDATION ONLY.
        
        Args:
            action_type: Type of action
            
        Returns:
            True if confirmation required
        """
        if action_type in self.CONFIRMATION_EXEMPT_ACTIONS:
            return False
        
        return action_type in self.CONFIRMATION_REQUIRED_ACTIONS
    
    def record_confirmation(
        self,
        session_id: str,
        action_type: str,
        confirmation_input: str,
        response_time_seconds: Optional[float] = None,
    ) -> ConfirmationResult:
        """
        Record a confirmation.
        
        LOGGING ONLY. VALIDATION ONLY.
        
        Args:
            session_id: Session identifier
            action_type: Type of action being confirmed
            confirmation_input: Variable input from human
            response_time_seconds: Time taken to respond (optional)
            
        Returns:
            ConfirmationResult with validation status
        """
        # Validate: confirmation requires non-empty input
        if not confirmation_input or confirmation_input.strip() == "":
            return ConfirmationResult(
                valid=False,
                error_message="Confirmation requires non-empty input"
            )
        
        # Generate confirmation ID
        confirmation_id = str(uuid.uuid4())
        
        # Check for rubber-stamping (TH-05)
        flagged_rubber_stamp = False
        if response_time_seconds is not None:
            if response_time_seconds < self.RUBBER_STAMP_THRESHOLD_SECONDS:
                flagged_rubber_stamp = True
        
        # Record timestamp for frequency tracking
        current_time = time.time()
        if session_id not in self._confirmation_timestamps:
            self._confirmation_timestamps[session_id] = []
        
        self._confirmation_timestamps[session_id].append(current_time)
        
        # Log to audit trail (logging only)
        self._log_audit_entry(
            entry_id=confirmation_id,
            action_type="CONFIRMATION_RECEIVED",
            initiator="HUMAN",  # Confirmations are HUMAN initiated
            session_id=session_id,
            action_details=f"Action: {action_type}, Rubber-stamp flagged: {flagged_rubber_stamp}",
            outcome="SUCCESS",
        )
        
        return ConfirmationResult(
            valid=True,
            confirmation_id=confirmation_id,
            flagged_rubber_stamp=flagged_rubber_stamp
        )
    
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
    
    def check_frequency_status(self, session_id: str) -> FrequencyStatus:
        """
        Check confirmation frequency status.
        
        VALIDATION ONLY. Pauses if frequency exceeded.
        
        Args:
            session_id: Session identifier
            
        Returns:
            FrequencyStatus with pause status
        """
        timestamps = self._confirmation_timestamps.get(session_id, [])
        
        if not timestamps:
            return FrequencyStatus(
                paused=False,
                confirmations_in_window=0,
                window_seconds=self.WINDOW_SECONDS,
                max_allowed=self.MAX_CONFIRMATIONS_PER_WINDOW
            )
        
        # Count confirmations in window
        current_time = time.time()
        window_start = current_time - self.WINDOW_SECONDS
        
        confirmations_in_window = sum(
            1 for ts in timestamps if ts >= window_start
        )
        
        # Pause if exceeded (TH-04)
        paused = confirmations_in_window > self.MAX_CONFIRMATIONS_PER_WINDOW
        
        return FrequencyStatus(
            paused=paused,
            confirmations_in_window=confirmations_in_window,
            window_seconds=self.WINDOW_SECONDS,
            max_allowed=self.MAX_CONFIRMATIONS_PER_WINDOW
        )


# =============================================================================
# TASK-4.3: Attribution System
# =============================================================================

class AttributionValidator:
    """
    Validates attribution for all actions.
    
    VALIDATION ONLY. Blocks actions without clear attribution.
    
    NO automation. NO execution authority.
    """
    
    # Valid initiator values
    VALID_INITIATORS = frozenset(["HUMAN", "SYSTEM"])
    
    def validate_attribution(
        self,
        action_type: str,
        initiator: Optional[str],
    ) -> AttributionResult:
        """
        Validate attribution for an action.
        
        VALIDATION ONLY. Blocks if attribution missing or invalid.
        
        Args:
            action_type: Type of action
            initiator: Claimed initiator (HUMAN or SYSTEM)
            
        Returns:
            AttributionResult with validation status
        """
        # Validate: initiator must be provided
        if initiator is None:
            return AttributionResult(
                valid=False,
                error_message="Attribution required: initiator must be specified"
            )
        
        # Validate: initiator must be valid value
        if initiator not in self.VALID_INITIATORS:
            return AttributionResult(
                valid=False,
                error_message=f"Invalid initiator: must be HUMAN or SYSTEM, got {initiator}"
            )
        
        return AttributionResult(valid=True)
