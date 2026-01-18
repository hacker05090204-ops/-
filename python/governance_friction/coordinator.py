"""
Phase-10: Governance & Friction Layer - Friction Coordinator

Main orchestrator that coordinates all friction mechanisms.
Enforces order: deliberation → edit → challenge → cooldown → audit check
"""

from typing import Dict, Optional

from governance_friction.types import (
    FrictionState,
    DeliberationRecord,
    ChallengeQuestion,
    RubberStampWarning,
    CooldownState,
    AuditCompleteness,
    FrictionAction,
)
from governance_friction.errors import (
    DeliberationTimeViolation,
    ForcedEditViolation,
    ChallengeNotAnswered,
    CooldownViolation,
    AuditIncomplete,
)
from governance_friction.deliberation import DeliberationTimer
from governance_friction.edit_checker import ForcedEditChecker
from governance_friction.challenge import ChallengeQuestionGenerator, ChallengeAnswerValidator
from governance_friction.rubber_stamp import RubberStampDetector
from governance_friction.cooldown import CooldownEnforcer
from governance_friction.audit_completeness import AuditCompletenessChecker
from governance_friction.audit import FrictionAuditLogger
from governance_friction.boundaries import Phase10BoundaryGuard


class FrictionCoordinator:
    """
    Main orchestrator for Phase-10 Friction Layer.
    
    SECURITY: This coordinator:
    - Enforces ALL friction mechanisms in order
    - NEVER bypasses any mechanism
    - NEVER auto-approves anything
    - NEVER reduces friction
    
    Flow: deliberation → edit → challenge → cooldown → audit check
    """
    
    def __init__(self):
        """Initialize the friction coordinator."""
        # Validate boundaries on initialization
        Phase10BoundaryGuard.validate_all()
        
        # Initialize components
        self._deliberation = DeliberationTimer()
        self._edit_checker = ForcedEditChecker()
        self._challenge_generator = ChallengeQuestionGenerator()
        self._challenge_validator = ChallengeAnswerValidator()
        self._rubber_stamp = RubberStampDetector()
        self._cooldown = CooldownEnforcer()
        self._audit_checker = AuditCompletenessChecker()
        self._audit_logger = FrictionAuditLogger()
        
        # Track friction state per decision
        self._friction_states: Dict[str, FrictionState] = {}
    
    def start_friction(
        self,
        decision_id: str,
        original_content: str,
        context: Dict[str, str],
    ) -> FrictionState:
        """
        Start the friction flow for a decision.
        
        Args:
            decision_id: Unique identifier for the decision
            original_content: Original content to be reviewed
            context: Context for challenge question generation
            
        Returns:
            Initial FrictionState
        """
        # Initialize audit tracking
        self._audit_checker.initialize_audit(decision_id)
        
        # Start deliberation
        deliberation = self._deliberation.start_deliberation(decision_id)
        self._audit_logger.log_action(
            FrictionAction.DELIBERATION_START,
            decision_id,
            {"start_monotonic": deliberation.start_monotonic},
        )
        
        # Register content for edit checking
        self._edit_checker.register_content(decision_id, original_content)
        self._audit_logger.log_action(
            FrictionAction.EDIT_REQUIRED,
            decision_id,
            {"content_length": len(original_content)},
        )
        
        # Generate challenge question
        challenge = self._challenge_generator.generate_challenge(decision_id, context)
        self._challenge_validator.register_challenge(challenge)
        self._audit_logger.log_action(
            FrictionAction.CHALLENGE_PRESENTED,
            decision_id,
            {"question_id": challenge.question_id},
        )
        
        # Create initial state
        state = FrictionState(
            decision_id=decision_id,
            deliberation=deliberation,
            challenge=challenge,
        )
        self._friction_states[decision_id] = state
        
        return state
    
    def submit_edit(
        self,
        decision_id: str,
        edited_content: str,
    ) -> FrictionState:
        """
        Submit edited content for validation.
        
        Args:
            decision_id: Unique identifier for the decision
            edited_content: The edited content
            
        Returns:
            Updated FrictionState
            
        Raises:
            ForcedEditViolation: If no meaningful edit was made
        """
        state = self._friction_states.get(decision_id)
        if state is None:
            raise KeyError(f"No friction flow for decision: {decision_id}")
        
        # Validate edit
        self._edit_checker.require_edit(decision_id, edited_content)
        
        # Record in audit
        self._audit_checker.record_item(decision_id, "edit")
        self._audit_logger.log_action(
            FrictionAction.EDIT_VERIFIED,
            decision_id,
            {"edit_verified": True},
        )
        
        # Update state
        state = FrictionState(
            decision_id=state.decision_id,
            deliberation=state.deliberation,
            edit_verified=True,
            challenge=state.challenge,
            rubber_stamp_warning=state.rubber_stamp_warning,
            cooldown=state.cooldown,
            audit_completeness=state.audit_completeness,
            is_friction_complete=state.is_friction_complete,
        )
        self._friction_states[decision_id] = state
        
        return state
    
    def submit_challenge_answer(
        self,
        decision_id: str,
        answer: str,
    ) -> FrictionState:
        """
        Submit answer to challenge question.
        
        Args:
            decision_id: Unique identifier for the decision
            answer: The human's answer
            
        Returns:
            Updated FrictionState
            
        Raises:
            ChallengeNotAnswered: If answer is invalid
        """
        state = self._friction_states.get(decision_id)
        if state is None:
            raise KeyError(f"No friction flow for decision: {decision_id}")
        
        if state.challenge is None:
            raise KeyError(f"No challenge for decision: {decision_id}")
        
        # Validate answer
        answered_challenge = self._challenge_validator.validate_answer(
            state.challenge, answer
        )
        
        # Record in audit
        self._audit_checker.record_item(decision_id, "challenge")
        self._audit_logger.log_action(
            FrictionAction.CHALLENGE_ANSWERED,
            decision_id,
            {"question_id": answered_challenge.question_id},
        )
        
        # Update state
        state = FrictionState(
            decision_id=state.decision_id,
            deliberation=state.deliberation,
            edit_verified=state.edit_verified,
            challenge=answered_challenge,
            rubber_stamp_warning=state.rubber_stamp_warning,
            cooldown=state.cooldown,
            audit_completeness=state.audit_completeness,
            is_friction_complete=state.is_friction_complete,
        )
        self._friction_states[decision_id] = state
        
        return state
    
    def complete_deliberation(
        self,
        decision_id: str,
        reviewer_id: str,
    ) -> FrictionState:
        """
        Complete deliberation and start cooldown.
        
        Args:
            decision_id: Unique identifier for the decision
            reviewer_id: ID of the reviewer
            
        Returns:
            Updated FrictionState
            
        Raises:
            DeliberationTimeViolation: If minimum time not met
        """
        state = self._friction_states.get(decision_id)
        if state is None:
            raise KeyError(f"No friction flow for decision: {decision_id}")
        
        # End deliberation (validates timing)
        completed_deliberation = self._deliberation.end_deliberation(decision_id)
        
        # Record in audit
        self._audit_checker.record_item(decision_id, "deliberation")
        self._audit_logger.log_action(
            FrictionAction.DELIBERATION_END,
            decision_id,
            {"elapsed_seconds": completed_deliberation.elapsed_seconds},
        )
        
        # Analyze rubber-stamp patterns (advisory only)
        self._rubber_stamp.record_confirmation(
            reviewer_id,
            decision_id,
            completed_deliberation.elapsed_seconds,
        )
        warning = self._rubber_stamp.analyze_pattern(reviewer_id)
        self._audit_logger.log_action(
            FrictionAction.RUBBER_STAMP_ANALYZED,
            decision_id,
            {"warning_level": warning.warning_level.name},
        )
        
        # Start cooldown
        cooldown = self._cooldown.start_cooldown(decision_id)
        self._audit_logger.log_action(
            FrictionAction.COOLDOWN_START,
            decision_id,
            {"duration_seconds": cooldown.duration_seconds},
        )
        
        # Update state
        state = FrictionState(
            decision_id=state.decision_id,
            deliberation=completed_deliberation,
            edit_verified=state.edit_verified,
            challenge=state.challenge,
            rubber_stamp_warning=warning,
            cooldown=cooldown,
            audit_completeness=state.audit_completeness,
            is_friction_complete=state.is_friction_complete,
        )
        self._friction_states[decision_id] = state
        
        return state
    
    def complete_friction(
        self,
        decision_id: str,
    ) -> FrictionState:
        """
        Complete the friction flow and validate all requirements.
        
        Args:
            decision_id: Unique identifier for the decision
            
        Returns:
            Final FrictionState
            
        Raises:
            CooldownViolation: If cooldown not complete
            AuditIncomplete: If audit trail incomplete
        """
        state = self._friction_states.get(decision_id)
        if state is None:
            raise KeyError(f"No friction flow for decision: {decision_id}")
        
        # End cooldown (validates timing)
        completed_cooldown = self._cooldown.end_cooldown(decision_id)
        
        # Record in audit
        self._audit_checker.record_item(decision_id, "cooldown")
        self._audit_logger.log_action(
            FrictionAction.COOLDOWN_END,
            decision_id,
            {"is_complete": completed_cooldown.is_complete},
        )
        
        # Check audit completeness
        audit_completeness = self._audit_checker.require_completeness(decision_id)
        self._audit_logger.log_action(
            FrictionAction.AUDIT_COMPLETENESS_CHECK,
            decision_id,
            {"is_complete": audit_completeness.is_complete},
        )
        
        # Log friction complete
        self._audit_logger.log_action(
            FrictionAction.FRICTION_COMPLETE,
            decision_id,
            {},
        )
        
        # Create final state
        state = FrictionState(
            decision_id=state.decision_id,
            deliberation=state.deliberation,
            edit_verified=state.edit_verified,
            challenge=state.challenge,
            rubber_stamp_warning=state.rubber_stamp_warning,
            cooldown=completed_cooldown,
            audit_completeness=audit_completeness,
            is_friction_complete=True,
        )
        self._friction_states[decision_id] = state
        
        return state
    
    def get_state(self, decision_id: str) -> Optional[FrictionState]:
        """
        Get current friction state for a decision.
        
        Args:
            decision_id: Unique identifier for the decision
            
        Returns:
            Current FrictionState or None
        """
        return self._friction_states.get(decision_id)
    
    def get_audit_entries(self, decision_id: str):
        """
        Get audit entries for a decision.
        
        Args:
            decision_id: Unique identifier for the decision
            
        Returns:
            List of AuditEntry
        """
        return self._audit_logger.get_entries(decision_id)
    
    def verify_audit_chain(self) -> bool:
        """
        Verify the integrity of the audit chain.
        
        Returns:
            True if chain is valid
        """
        return self._audit_logger.verify_chain()
