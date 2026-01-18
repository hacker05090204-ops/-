"""
Bounty Pipeline - Main orchestrator for human-in-the-loop submission.

This is the main entry point for the Bounty Pipeline system.
It coordinates all components to process MCP-proven findings
through validation, review, and submission.

CRITICAL: This system assists humans. It does not replace them.
All submissions require human approval. No exceptions.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from bounty_pipeline.errors import (
    BountyPipelineError,
    FindingValidationError,
    ScopeViolationError,
    HumanApprovalRequired,
    ArchitecturalViolationError,
    is_hard_stop,
)
from bounty_pipeline.types import (
    MCPFinding,
    ValidatedFinding,
    SubmissionDraft,
    ApprovalToken,
    AuthorizationDocument,
    SubmissionStatus,
)
from bounty_pipeline.validator import FindingValidator
from bounty_pipeline.scope import LegalScopeValidator
from bounty_pipeline.review import HumanReviewGate, ReviewRequest
from bounty_pipeline.report import ReportGenerator
from bounty_pipeline.audit import AuditTrail
from bounty_pipeline.duplicate import DuplicateDetector


@dataclass
class PipelineResult:
    """Result of pipeline processing."""

    success: bool
    stage: str
    message: str
    draft: Optional[SubmissionDraft] = None
    review_request: Optional[ReviewRequest] = None
    error: Optional[Exception] = None


class BountyPipeline:
    """
    Main orchestrator for human-in-the-loop submission.

    This pipeline:
    1. Validates findings have MCP proof
    2. Validates legal scope
    3. Checks for duplicates
    4. Generates platform-specific reports
    5. Requires human approval
    6. Records all actions in audit trail

    ARCHITECTURAL CONSTRAINTS:
    - NO submission without MCP proof
    - NO submission without human approval
    - NO confidence scoring (MCP's domain)
    - NO auto-earning logic
    """

    def __init__(
        self,
        authorization: AuthorizationDocument,
        platform: str = "generic",
        token_validity_minutes: int = 30,
    ) -> None:
        """
        Initialize the pipeline.

        Args:
            authorization: Legal authorization document
            platform: Target platform (hackerone, bugcrowd, generic)
            token_validity_minutes: How long approval tokens are valid
        """
        self._authorization = authorization
        self._platform = platform

        # Initialize components
        self._validator = FindingValidator()
        self._scope_validator = LegalScopeValidator()
        self._review_gate = HumanReviewGate(token_validity_minutes)
        self._report_generator = ReportGenerator()
        self._audit_trail = AuditTrail()
        self._duplicate_detector = DuplicateDetector()

    def process_finding(self, finding: MCPFinding) -> PipelineResult:
        """
        Process an MCP finding through the pipeline.

        This method:
        1. Validates the finding has MCP proof
        2. Validates legal scope
        3. Checks for duplicates
        4. Generates a report
        5. Requests human review

        Args:
            finding: The MCP finding to process

        Returns:
            PipelineResult with status and next steps
        """
        try:
            # Stage 1: Validate finding
            self._audit_trail.record(
                action_type="validation_start",
                actor="system",
                outcome="started",
                details={"finding_id": finding.finding_id},
                finding_id=finding.finding_id,
            )

            validated = self._validator.validate(finding)

            self._audit_trail.record(
                action_type="validation_complete",
                actor="system",
                outcome="success",
                details={
                    "finding_id": finding.finding_id,
                    "classification": finding.classification.value,
                },
                mcp_proof_link=finding.finding_id,
                finding_id=finding.finding_id,
            )

            # Stage 2: Validate scope
            # Extract target from finding (simplified - in real impl would parse from proof)
            target = self._extract_target(validated)

            self._scope_validator.validate_target(target, self._authorization)

            self._audit_trail.record(
                action_type="scope_validation",
                actor="system",
                outcome="in_scope",
                details={"target": target, "program": self._authorization.program_name},
                finding_id=finding.finding_id,
            )

            # Stage 3: Check for duplicates
            duplicate = self._duplicate_detector.check(validated)
            if duplicate:
                self._audit_trail.record(
                    action_type="duplicate_check",
                    actor="system",
                    outcome="potential_duplicate",
                    details={
                        "similarity": duplicate.similarity_score,
                        "original_id": duplicate.original_finding_id,
                    },
                    finding_id=finding.finding_id,
                )

                # Request human decision
                decision_request = self._duplicate_detector.request_human_decision(
                    validated, duplicate
                )

                return PipelineResult(
                    success=False,
                    stage="duplicate_check",
                    message=f"Potential duplicate detected (similarity: {duplicate.similarity_score:.2f}). "
                    f"Human decision required.",
                )

            self._audit_trail.record(
                action_type="duplicate_check",
                actor="system",
                outcome="no_duplicate",
                details={},
                finding_id=finding.finding_id,
            )

            # Stage 4: Generate report
            draft = self._report_generator.generate(validated, self._platform)

            self._audit_trail.record(
                action_type="report_generation",
                actor="system",
                outcome="success",
                details={"platform": self._platform, "draft_id": draft.draft_id},
                finding_id=finding.finding_id,
            )

            # Stage 5: Request human review
            review_request = self._review_gate.request_review(draft)

            self._audit_trail.record(
                action_type="review_requested",
                actor="system",
                outcome="pending",
                details={"request_id": review_request.request_id},
                finding_id=finding.finding_id,
            )

            return PipelineResult(
                success=True,
                stage="review_pending",
                message="Report generated and awaiting human review.",
                draft=draft,
                review_request=review_request,
            )

        except FindingValidationError as e:
            self._audit_trail.record(
                action_type="validation_failed",
                actor="system",
                outcome="rejected",
                details={"error": str(e)},
                finding_id=finding.finding_id,
            )
            return PipelineResult(
                success=False,
                stage="validation",
                message=f"Finding validation failed: {e}",
                error=e,
            )

        except ScopeViolationError as e:
            self._audit_trail.record(
                action_type="scope_violation",
                actor="system",
                outcome="blocked",
                details={"error": str(e)},
                finding_id=finding.finding_id,
            )
            return PipelineResult(
                success=False,
                stage="scope_validation",
                message=f"Scope violation: {e}",
                error=e,
            )

        except BountyPipelineError as e:
            self._audit_trail.record(
                action_type="pipeline_error",
                actor="system",
                outcome="error",
                details={"error": str(e), "error_type": type(e).__name__},
                finding_id=finding.finding_id,
            )
            return PipelineResult(
                success=False,
                stage="unknown",
                message=f"Pipeline error: {e}",
                error=e,
            )

    def approve_submission(
        self, request_id: str, approver_id: str
    ) -> ApprovalToken:
        """
        Human approves a submission.

        Args:
            request_id: The review request ID
            approver_id: ID of the human approving

        Returns:
            ApprovalToken for submission
        """
        token = self._review_gate.approve(request_id, approver_id)

        self._audit_trail.record(
            action_type="submission_approved",
            actor=approver_id,
            outcome="approved",
            details={"request_id": request_id, "token_id": token.token_id},
        )

        return token

    def reject_submission(
        self, request_id: str, rejector_id: str, reason: str
    ) -> None:
        """
        Human rejects a submission.

        Args:
            request_id: The review request ID
            rejector_id: ID of the human rejecting
            reason: Reason for rejection
        """
        self._review_gate.reject(request_id, rejector_id, reason)

        self._audit_trail.record(
            action_type="submission_rejected",
            actor=rejector_id,
            outcome="rejected",
            details={"request_id": request_id, "reason": reason},
        )

    def _extract_target(self, finding: ValidatedFinding) -> str:
        """Extract target from finding's MCP ProofChain for scope validation.
        
        CRITICAL: Target MUST be extracted from MCP proof, never fabricated.
        
        Args:
            finding: The validated finding with MCP proof
            
        Returns:
            Target URL/domain extracted from proof
            
        Raises:
            FindingValidationError: If target cannot be extracted from proof
        """
        from bounty_pipeline.errors import FindingValidationError
        
        proof_chain = finding.proof_chain
        
        # Extract target from action_sequence in proof chain
        # The action sequence contains the actual requests made
        if proof_chain.action_sequence:
            for action in proof_chain.action_sequence:
                # Look for target/url in action
                if isinstance(action, dict):
                    target = action.get("target") or action.get("url") or action.get("endpoint")
                    if target:
                        return target
        
        # Try to extract from before_state or after_state
        if isinstance(proof_chain.before_state, dict):
            target = proof_chain.before_state.get("target") or proof_chain.before_state.get("url")
            if target:
                return target
        
        if isinstance(proof_chain.after_state, dict):
            target = proof_chain.after_state.get("target") or proof_chain.after_state.get("url")
            if target:
                return target
        
        # Try to extract from replay_instructions
        if proof_chain.replay_instructions:
            for instruction in proof_chain.replay_instructions:
                if isinstance(instruction, dict):
                    target = instruction.get("target") or instruction.get("url")
                    if target:
                        return target
        
        # HARD FAIL: Cannot proceed without valid target from proof
        raise FindingValidationError(
            f"Cannot extract target from MCP ProofChain for finding {finding.finding_id}. "
            "ProofChain must contain target in action_sequence, before_state, after_state, "
            "or replay_instructions. HARD STOP: Cannot validate scope without target."
        )

    @property
    def audit_trail(self) -> AuditTrail:
        """Get the audit trail."""
        return self._audit_trail

    @property
    def review_gate(self) -> HumanReviewGate:
        """Get the review gate."""
        return self._review_gate

    @property
    def duplicate_detector(self) -> DuplicateDetector:
        """Get the duplicate detector."""
        return self._duplicate_detector

    # =========================================================================
    # ARCHITECTURAL BOUNDARY ENFORCEMENT
    # =========================================================================

    def auto_submit(self, *args, **kwargs) -> None:
        """
        FORBIDDEN: Cannot auto-submit reports.

        Raises:
            ArchitecturalViolationError: Always - human approval required
        """
        raise ArchitecturalViolationError(
            "Cannot auto-submit reports. "
            "Human approval is MANDATORY for all submissions. "
            "Use approve_submission() after human review."
        )

    def bypass_validation(self, *args, **kwargs) -> None:
        """
        FORBIDDEN: Cannot bypass validation.

        Raises:
            ArchitecturalViolationError: Always - MCP proof required
        """
        raise ArchitecturalViolationError(
            "Cannot bypass validation. "
            "All findings MUST have MCP proof before submission. "
            "This is a non-negotiable requirement."
        )

    def compute_bounty(self, *args, **kwargs) -> None:
        """
        FORBIDDEN: Cannot compute or predict bounty.

        Raises:
            ArchitecturalViolationError: Always - no auto-earning
        """
        raise ArchitecturalViolationError(
            "Cannot compute or predict bounty amounts. "
            "Bounty Pipeline does not engage in auto-earning logic. "
            "Bounty amounts are determined by the platform."
        )
