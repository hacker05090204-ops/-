"""
Phase-9 Human Confirmation Gate

Every assistant output requires explicit human confirmation.

SAFETY CONSTRAINTS (NON-NEGOTIABLE):
- EVERY output requires human confirmation
- NO auto-confirmation
- NO bypass mechanisms
- NO timeout-based auto-approval
- Human MUST click YES or NO

This is the FINAL gate before any output is acted upon.

Phase-9 is ASSISTIVE ONLY. Human always clicks YES/NO.
"""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import uuid

from browser_assistant.types import (
    AssistantOutput,
    HumanConfirmation,
    ConfirmationStatus,
)
from browser_assistant.errors import (
    HumanConfirmationRequired,
    AutomationAttemptError,
)
from browser_assistant.boundaries import Phase9BoundaryGuard


class HumanConfirmationGate:
    """
    Gate that requires human confirmation for all outputs.
    
    SECURITY: This gate ensures that EVERY assistant output
    requires explicit human confirmation. It NEVER:
    - Auto-confirms outputs
    - Bypasses confirmation
    - Times out to auto-approve
    - Allows batch confirmation
    
    Human MUST click YES or NO for each output.
    
    FORBIDDEN METHODS (do not add):
    - auto_confirm()
    - bypass_confirmation()
    - batch_confirm()
    - timeout_approve()
    - skip_confirmation()
    """
    
    # Confirmation expiry time (human must respond within this window)
    CONFIRMATION_EXPIRY = timedelta(hours=24)
    
    def __init__(self):
        """Initialize the confirmation gate."""
        Phase9BoundaryGuard.assert_human_confirmation_required()
        Phase9BoundaryGuard.assert_no_automation()
        
        self._pending_outputs: Dict[str, AssistantOutput] = {}
        self._confirmations: Dict[str, HumanConfirmation] = {}
        self._max_pending = 1000  # Prevent unbounded growth
    
    def register_output(
        self,
        output_type: str,
        content: any,
    ) -> AssistantOutput:
        """
        Register an output that requires human confirmation.
        
        Args:
            output_type: Type of output (hint, draft, etc.).
            content: The actual output content.
            
        Returns:
            AssistantOutput with PENDING confirmation status.
            
        NOTE: The output is NOT acted upon until human confirms.
        """
        # Enforce size limit
        if len(self._pending_outputs) >= self._max_pending:
            # Remove oldest pending
            oldest_id = next(iter(self._pending_outputs))
            del self._pending_outputs[oldest_id]
        
        output = AssistantOutput(
            output_id=str(uuid.uuid4()),
            output_type=output_type,
            content=content,
            timestamp=datetime.now(),
            confirmation_status=ConfirmationStatus.PENDING,
            confirmation_id=None,
            requires_human_confirmation=True,  # Always True
            no_auto_action=True,  # Always True
            is_advisory_only=True,  # Always True
        )
        
        self._pending_outputs[output.output_id] = output
        return output
    
    def request_confirmation(
        self,
        output_id: str,
    ) -> None:
        """
        Request human confirmation for an output.
        
        Args:
            output_id: ID of the output to confirm.
            
        Raises:
            HumanConfirmationRequired: Always raised to signal
                that human must confirm.
        """
        output = self._pending_outputs.get(output_id)
        if not output:
            raise HumanConfirmationRequired(output_id, "unknown")
        
        raise HumanConfirmationRequired(output_id, output.output_type)
    
    def confirm(
        self,
        output_id: str,
        confirmed_by: str,
        approved: bool,
    ) -> HumanConfirmation:
        """
        Record human confirmation for an output.
        
        Args:
            output_id: ID of the output being confirmed.
            confirmed_by: Human identifier.
            approved: True if human clicked YES, False if NO.
            
        Returns:
            HumanConfirmation record.
            
        NOTE: This method is called when human clicks YES or NO.
        It does NOT auto-confirm anything.
        """
        output = self._pending_outputs.get(output_id)
        if not output:
            # Create confirmation for unknown output (may have expired)
            status = ConfirmationStatus.CONFIRMED if approved else ConfirmationStatus.REJECTED
            confirmation = HumanConfirmation(
                confirmation_id=str(uuid.uuid4()),
                output_id=output_id,
                output_type="unknown",
                status=status,
                confirmed_by=confirmed_by,
                confirmed_at=datetime.now(),
                confirmation_hash=HumanConfirmation.compute_hash(
                    output_id=output_id,
                    output_type="unknown",
                    status=status,
                    confirmed_by=confirmed_by,
                    confirmed_at=datetime.now(),
                ),
                is_explicit_human_action=True,
                is_single_use=True,
            )
            self._confirmations[confirmation.confirmation_id] = confirmation
            return confirmation
        
        # Determine status
        status = ConfirmationStatus.CONFIRMED if approved else ConfirmationStatus.REJECTED
        confirmed_at = datetime.now()
        
        # Create confirmation
        confirmation = HumanConfirmation(
            confirmation_id=str(uuid.uuid4()),
            output_id=output_id,
            output_type=output.output_type,
            status=status,
            confirmed_by=confirmed_by,
            confirmed_at=confirmed_at,
            confirmation_hash=HumanConfirmation.compute_hash(
                output_id=output_id,
                output_type=output.output_type,
                status=status,
                confirmed_by=confirmed_by,
                confirmed_at=confirmed_at,
            ),
            is_explicit_human_action=True,  # Always True
            is_single_use=True,  # Always True
        )
        
        # Store confirmation
        self._confirmations[confirmation.confirmation_id] = confirmation
        
        # Remove from pending
        del self._pending_outputs[output_id]
        
        return confirmation
    
    def is_confirmed(self, output_id: str) -> bool:
        """
        Check if an output has been confirmed (YES).
        
        Args:
            output_id: ID of the output.
            
        Returns:
            True if human clicked YES, False otherwise.
        """
        for conf in self._confirmations.values():
            if conf.output_id == output_id:
                return conf.status == ConfirmationStatus.CONFIRMED
        return False
    
    def is_rejected(self, output_id: str) -> bool:
        """
        Check if an output has been rejected (NO).
        
        Args:
            output_id: ID of the output.
            
        Returns:
            True if human clicked NO, False otherwise.
        """
        for conf in self._confirmations.values():
            if conf.output_id == output_id:
                return conf.status == ConfirmationStatus.REJECTED
        return False
    
    def is_pending(self, output_id: str) -> bool:
        """
        Check if an output is pending confirmation.
        
        Args:
            output_id: ID of the output.
            
        Returns:
            True if awaiting human response.
        """
        return output_id in self._pending_outputs
    
    def get_pending_outputs(self) -> List[AssistantOutput]:
        """
        Get all outputs pending confirmation.
        
        Returns:
            List of pending outputs.
        """
        return list(self._pending_outputs.values())
    
    def get_confirmation(
        self,
        confirmation_id: str,
    ) -> Optional[HumanConfirmation]:
        """
        Get a confirmation by ID.
        
        Args:
            confirmation_id: ID of the confirmation.
            
        Returns:
            HumanConfirmation if found, None otherwise.
        """
        return self._confirmations.get(confirmation_id)
    
    def expire_old_pending(self) -> int:
        """
        Expire pending outputs that have exceeded the time limit.
        
        Returns:
            Number of outputs expired.
        """
        now = datetime.now()
        expired_ids = []
        
        for output_id, output in self._pending_outputs.items():
            if now - output.timestamp > self.CONFIRMATION_EXPIRY:
                expired_ids.append(output_id)
        
        for output_id in expired_ids:
            del self._pending_outputs[output_id]
        
        return len(expired_ids)
    
    def clear_all(self) -> tuple[int, int]:
        """
        Clear all pending outputs and confirmations.
        
        Returns:
            Tuple of (pending_cleared, confirmations_cleared).
        """
        pending_count = len(self._pending_outputs)
        conf_count = len(self._confirmations)
        
        self._pending_outputs.clear()
        self._confirmations.clear()
        
        return (pending_count, conf_count)
    
    # ========================================================================
    # FORBIDDEN METHODS - DO NOT IMPLEMENT
    # ========================================================================
    # The following methods are FORBIDDEN and must NEVER be added:
    #
    # - auto_confirm() - Phase-9 NEVER auto-confirms
    # - bypass_confirmation() - Phase-9 NEVER bypasses
    # - batch_confirm() - Phase-9 NEVER batch confirms
    # - timeout_approve() - Phase-9 NEVER timeout approves
    # - skip_confirmation() - Phase-9 NEVER skips
    # - confirm_all() - Phase-9 NEVER confirms all
    # - auto_approve() - Phase-9 NEVER auto-approves
    # - default_approve() - Phase-9 NEVER default approves
    # ========================================================================
