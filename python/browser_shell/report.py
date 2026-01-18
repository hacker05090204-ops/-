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
Report Submission for Phase-13 Browser Shell.

Requirements: 5.1, 5.2 (Report Submission)

This module implements:
- TASK-6.1: Three-Step Submission Confirmation
- TASK-6.2: Report Content Controls

NO automatic submission. NO auto-fill. NO auto-severity.
All submissions require explicit 3-step human confirmation.
"""

from dataclasses import dataclass
from typing import Dict, Optional
import time
import uuid


# =============================================================================
# Result Dataclasses (Immutable)
# =============================================================================

@dataclass(frozen=True)
class DraftResult:
    """Result of creating a draft."""
    draft_id: str
    session_id: str
    title: str
    description: str
    severity: str = ""
    requires_human_edit: bool = True


@dataclass(frozen=True)
class StepResult:
    """Result of a confirmation step."""
    success: bool
    step_number: int
    error_message: str = ""
    flagged_timing_violation: bool = False


@dataclass(frozen=True)
class SubmissionResult:
    """Result of submission execution."""
    success: bool
    submission_id: Optional[str] = None
    error_message: str = ""


@dataclass(frozen=True)
class SeverityResult:
    """Result of setting severity."""
    success: bool
    error_message: str = ""


@dataclass(frozen=True)
class Template:
    """Report template."""
    template_type: str
    content: str
    requires_human_edit: bool = True


# =============================================================================
# TASK-6.1, 6.2: Report Submission
# =============================================================================

class ReportSubmission:
    """
    Three-step submission confirmation with content controls.
    
    Per Requirement 5.1 (Submission Confirmation):
    - Exactly 3 confirmation steps required (TH-01)
    - Each step requires distinct human input
    - Minimum 2 second delay between steps (TH-02)
    - <2 sec timing triggers halt
    - All steps logged to audit trail
    
    Per Requirement 5.2 (Report Content Controls):
    - NO automatic severity assignment
    - NO auto-fill from previous reports
    - Templates require human modification
    - Severity requires human confirmation
    - All content changes logged
    
    FORBIDDEN METHODS (not implemented):
    - auto_*, batch_*, schedule_*, submit (without confirmation)
    """
    
    # TH-01: Exactly 3 confirmation steps
    REQUIRED_CONFIRMATION_STEPS = 3
    
    # TH-02: Minimum 2 second delay between steps
    MINIMUM_STEP_DELAY_SECONDS = 2
    
    def __init__(self, storage, hash_chain):
        """
        Initialize report submission.
        
        Args:
            storage: AuditStorage instance for logging
            hash_chain: HashChain instance for entry linking
        """
        self._storage = storage
        self._hash_chain = hash_chain
        # Draft storage (draft_id -> draft data)
        self._drafts: Dict[str, dict] = {}
        # Step completion tracking (draft_id -> step data)
        self._step_completions: Dict[str, dict] = {}
    
    def create_draft(
        self,
        session_id: str,
        title: str,
        description: str,
    ) -> DraftResult:
        """
        Create a new report draft.
        
        NO auto-fill. NO auto-severity.
        
        Args:
            session_id: Session identifier
            title: Report title
            description: Report description
            
        Returns:
            DraftResult with draft details
        """
        draft_id = str(uuid.uuid4())
        
        self._drafts[draft_id] = {
            "session_id": session_id,
            "title": title,
            "description": description,
            "severity": "",  # NO auto-severity
            "created_at": time.time(),
        }
        
        self._step_completions[draft_id] = {
            "step_1_completed": False,
            "step_1_time": None,
            "step_2_completed": False,
            "step_2_time": None,
            "step_3_completed": False,
            "step_3_time": None,
        }
        
        # Log draft creation
        self._log_audit_entry(
            entry_id=draft_id,
            action_type="DRAFT_CREATED",
            initiator="HUMAN",
            session_id=session_id,
            action_details=f"Draft created: {title}",
            outcome="SUCCESS",
        )
        
        return DraftResult(
            draft_id=draft_id,
            session_id=session_id,
            title=title,
            description=description,
            severity="",  # NO auto-severity
            requires_human_edit=True,
        )
    
    def confirm_step_1(
        self,
        draft_id: str,
        human_input: str,
    ) -> StepResult:
        """
        Confirm step 1 of submission.
        
        Args:
            draft_id: Draft identifier
            human_input: Human-provided input
            
        Returns:
            StepResult with status
        """
        if not human_input or human_input.strip() == "":
            return StepResult(
                success=False,
                step_number=1,
                error_message="Step 1 requires human input",
            )
        
        if draft_id not in self._drafts:
            return StepResult(
                success=False,
                step_number=1,
                error_message="Draft not found",
            )
        
        self._step_completions[draft_id]["step_1_completed"] = True
        self._step_completions[draft_id]["step_1_time"] = time.time()
        
        # Log step 1
        self._log_audit_entry(
            entry_id=str(uuid.uuid4()),
            action_type="SUBMISSION_STEP_1",
            initiator="HUMAN",
            session_id=self._drafts[draft_id]["session_id"],
            action_details=f"Step 1 confirmed for draft {draft_id}",
            outcome="SUCCESS",
        )
        
        return StepResult(
            success=True,
            step_number=1,
        )
    
    def confirm_step_2(
        self,
        draft_id: str,
        human_input: str,
    ) -> StepResult:
        """
        Confirm step 2 of submission.
        
        Requires step 1 completed and minimum delay.
        
        Args:
            draft_id: Draft identifier
            human_input: Human-provided input
            
        Returns:
            StepResult with status
        """
        if not human_input or human_input.strip() == "":
            return StepResult(
                success=False,
                step_number=2,
                error_message="Step 2 requires human input",
            )
        
        if draft_id not in self._drafts:
            return StepResult(
                success=False,
                step_number=2,
                error_message="Draft not found",
            )
        
        steps = self._step_completions[draft_id]
        
        if not steps["step_1_completed"]:
            return StepResult(
                success=False,
                step_number=2,
                error_message="Step 1 must be completed first",
            )
        
        # Check timing (TH-02)
        elapsed = time.time() - steps["step_1_time"]
        if elapsed < self.MINIMUM_STEP_DELAY_SECONDS:
            # Log timing violation
            self._log_audit_entry(
                entry_id=str(uuid.uuid4()),
                action_type="TIMING_VIOLATION",
                initiator="SYSTEM",
                session_id=self._drafts[draft_id]["session_id"],
                action_details=f"Step 2 attempted too quickly: {elapsed:.2f}s < {self.MINIMUM_STEP_DELAY_SECONDS}s",
                outcome="BLOCKED",
            )
            return StepResult(
                success=False,
                step_number=2,
                error_message=f"Timing violation: minimum {self.MINIMUM_STEP_DELAY_SECONDS}s delay required",
                flagged_timing_violation=True,
            )
        
        self._step_completions[draft_id]["step_2_completed"] = True
        self._step_completions[draft_id]["step_2_time"] = time.time()
        
        # Log step 2
        self._log_audit_entry(
            entry_id=str(uuid.uuid4()),
            action_type="SUBMISSION_STEP_2",
            initiator="HUMAN",
            session_id=self._drafts[draft_id]["session_id"],
            action_details=f"Step 2 confirmed for draft {draft_id}",
            outcome="SUCCESS",
        )
        
        return StepResult(
            success=True,
            step_number=2,
        )
    
    def confirm_step_3(
        self,
        draft_id: str,
        human_input: str,
    ) -> StepResult:
        """
        Confirm step 3 of submission.
        
        Requires step 2 completed and minimum delay.
        
        Args:
            draft_id: Draft identifier
            human_input: Human-provided input
            
        Returns:
            StepResult with status
        """
        if not human_input or human_input.strip() == "":
            return StepResult(
                success=False,
                step_number=3,
                error_message="Step 3 requires human input",
            )
        
        if draft_id not in self._drafts:
            return StepResult(
                success=False,
                step_number=3,
                error_message="Draft not found",
            )
        
        steps = self._step_completions[draft_id]
        
        if not steps["step_2_completed"]:
            return StepResult(
                success=False,
                step_number=3,
                error_message="Step 2 must be completed first",
            )
        
        # Check timing (TH-02)
        elapsed = time.time() - steps["step_2_time"]
        if elapsed < self.MINIMUM_STEP_DELAY_SECONDS:
            # Log timing violation
            self._log_audit_entry(
                entry_id=str(uuid.uuid4()),
                action_type="TIMING_VIOLATION",
                initiator="SYSTEM",
                session_id=self._drafts[draft_id]["session_id"],
                action_details=f"Step 3 attempted too quickly: {elapsed:.2f}s < {self.MINIMUM_STEP_DELAY_SECONDS}s",
                outcome="BLOCKED",
            )
            return StepResult(
                success=False,
                step_number=3,
                error_message=f"Timing violation: minimum {self.MINIMUM_STEP_DELAY_SECONDS}s delay required",
                flagged_timing_violation=True,
            )
        
        self._step_completions[draft_id]["step_3_completed"] = True
        self._step_completions[draft_id]["step_3_time"] = time.time()
        
        # Log step 3
        self._log_audit_entry(
            entry_id=str(uuid.uuid4()),
            action_type="SUBMISSION_STEP_3",
            initiator="HUMAN",
            session_id=self._drafts[draft_id]["session_id"],
            action_details=f"Step 3 confirmed for draft {draft_id}",
            outcome="SUCCESS",
        )
        
        return StepResult(
            success=True,
            step_number=3,
        )
    
    def execute_submission(
        self,
        draft_id: str,
    ) -> SubmissionResult:
        """
        Execute submission after all 3 steps completed.
        
        BLOCKS if any step missing.
        
        Args:
            draft_id: Draft identifier
            
        Returns:
            SubmissionResult with status
        """
        if draft_id not in self._drafts:
            return SubmissionResult(
                success=False,
                error_message="Draft not found",
            )
        
        steps = self._step_completions[draft_id]
        
        # Verify all 3 steps completed
        if not steps["step_1_completed"]:
            return SubmissionResult(
                success=False,
                error_message="Step 1 not completed",
            )
        
        if not steps["step_2_completed"]:
            return SubmissionResult(
                success=False,
                error_message="Step 2 not completed",
            )
        
        if not steps["step_3_completed"]:
            return SubmissionResult(
                success=False,
                error_message="Step 3 not completed",
            )
        
        submission_id = str(uuid.uuid4())
        
        # Log submission
        self._log_audit_entry(
            entry_id=submission_id,
            action_type="REPORT_SUBMITTED",
            initiator="HUMAN",
            session_id=self._drafts[draft_id]["session_id"],
            action_details=f"Report submitted: {self._drafts[draft_id]['title']}",
            outcome="SUCCESS",
        )
        
        return SubmissionResult(
            success=True,
            submission_id=submission_id,
        )
    
    def set_severity(
        self,
        draft_id: str,
        severity: str,
        human_confirmed: bool,
    ) -> SeverityResult:
        """
        Set severity for a draft.
        
        REQUIRES human confirmation.
        
        Args:
            draft_id: Draft identifier
            severity: Severity level
            human_confirmed: Must be True
            
        Returns:
            SeverityResult with status
        """
        if not human_confirmed:
            return SeverityResult(
                success=False,
                error_message="Severity requires human confirmation",
            )
        
        if draft_id not in self._drafts:
            return SeverityResult(
                success=False,
                error_message="Draft not found",
            )
        
        self._drafts[draft_id]["severity"] = severity
        
        # Log severity change
        self._log_audit_entry(
            entry_id=str(uuid.uuid4()),
            action_type="SEVERITY_SET",
            initiator="HUMAN",
            session_id=self._drafts[draft_id]["session_id"],
            action_details=f"Severity set to {severity} for draft {draft_id}",
            outcome="SUCCESS",
        )
        
        return SeverityResult(success=True)
    
    def get_template(self, template_type: str) -> Template:
        """
        Get a report template.
        
        Templates REQUIRE human modification.
        
        Args:
            template_type: Type of template
            
        Returns:
            Template with content
        """
        templates = {
            "vulnerability": "[TITLE]\n\n[DESCRIPTION]\n\n[STEPS TO REPRODUCE]\n\n[IMPACT]",
            "security": "[SECURITY ISSUE]\n\n[AFFECTED COMPONENT]\n\n[REMEDIATION]",
        }
        
        content = templates.get(template_type, "[CUSTOM REPORT]")
        
        return Template(
            template_type=template_type,
            content=content,
            requires_human_edit=True,  # ALWAYS requires human edit
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
