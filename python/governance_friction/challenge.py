"""
Phase-10: Governance & Friction Layer - Challenge Questions

Presents verification questions before final approval.
Questions require human judgment and cannot be auto-answered.
"""

import hashlib
import uuid
from typing import Dict, Optional

from governance_friction.types import ChallengeQuestion
from governance_friction.errors import ChallengeNotAnswered


class ChallengeQuestionGenerator:
    """
    Generates challenge questions requiring human judgment.
    
    SECURITY: This generator creates questions that:
    - Require recall of specific content
    - Cannot be auto-answered
    - Do not provide answers in the question
    """
    
    # Question templates for different contexts
    QUESTION_TEMPLATES = [
        "What is the primary vulnerability type identified in this report?",
        "What is the affected component or endpoint?",
        "What is the potential impact of this vulnerability?",
        "What remediation step is recommended?",
        "What evidence supports this finding?",
    ]
    
    def generate_challenge(
        self, 
        decision_id: str, 
        context: Dict[str, str]
    ) -> ChallengeQuestion:
        """
        Generate a challenge question for a decision.
        
        Args:
            decision_id: Unique identifier for the decision
            context: Context information for generating the question
            
        Returns:
            ChallengeQuestion requiring human judgment
        """
        # Extract context summary
        context_summary = self._extract_context_summary(context)
        
        # Select appropriate question based on context
        question_text = self._select_question(context)
        
        return ChallengeQuestion(
            question_id=str(uuid.uuid4()),
            decision_id=decision_id,
            question_text=question_text,
            context_summary=context_summary,
            expected_answer_type="explanation",
        )
    
    def _extract_context_summary(self, context: Dict[str, str]) -> str:
        """Extract a summary from the context."""
        if "summary" in context:
            return context["summary"]
        if "title" in context:
            return context["title"]
        if "description" in context:
            return context["description"][:200]
        return "Decision context"
    
    def _select_question(self, context: Dict[str, str]) -> str:
        """Select an appropriate question based on context."""
        # Use context to select relevant question
        context_type = context.get("type", "").lower()
        
        if "vulnerability" in context_type or "vuln" in context_type:
            return self.QUESTION_TEMPLATES[0]
        if "endpoint" in context_type or "api" in context_type:
            return self.QUESTION_TEMPLATES[1]
        if "impact" in context_type or "risk" in context_type:
            return self.QUESTION_TEMPLATES[2]
        if "remediation" in context_type or "fix" in context_type:
            return self.QUESTION_TEMPLATES[3]
        
        # Default to evidence question
        return self.QUESTION_TEMPLATES[4]


class ChallengeAnswerValidator:
    """
    Validates answers to challenge questions.
    
    SECURITY: This validator ensures:
    - Answers are not empty
    - Answers demonstrate human review
    - No auto-answer capability exists
    """
    
    # Minimum answer length to be considered valid
    MIN_ANSWER_LENGTH = 10
    
    def __init__(self):
        """Initialize the answer validator."""
        self._pending_challenges: Dict[str, ChallengeQuestion] = {}
    
    def register_challenge(self, challenge: ChallengeQuestion) -> None:
        """
        Register a challenge for validation.
        
        Args:
            challenge: The challenge question to register
        """
        self._pending_challenges[challenge.question_id] = challenge
    
    def validate_answer(
        self, 
        challenge: ChallengeQuestion, 
        answer: str
    ) -> ChallengeQuestion:
        """
        Validate an answer to a challenge question.
        
        Args:
            challenge: The challenge question
            answer: The human's answer
            
        Returns:
            Updated ChallengeQuestion with answer
            
        Raises:
            ChallengeNotAnswered: If answer is invalid
        """
        # Check for empty answer
        if not answer or not answer.strip():
            raise ChallengeNotAnswered(
                decision_id=challenge.decision_id,
                question_id=challenge.question_id,
            )
        
        # Check for minimum length
        stripped_answer = answer.strip()
        if len(stripped_answer) < self.MIN_ANSWER_LENGTH:
            raise ChallengeNotAnswered(
                decision_id=challenge.decision_id,
                question_id=challenge.question_id,
            )
        
        # Create answered challenge
        return challenge.with_answer(stripped_answer)
    
    def get_pending_challenge(self, question_id: str) -> Optional[ChallengeQuestion]:
        """
        Get a pending challenge by ID.
        
        Args:
            question_id: The question ID
            
        Returns:
            The challenge or None if not found
        """
        return self._pending_challenges.get(question_id)
    
    def clear_challenge(self, question_id: str) -> None:
        """
        Clear a pending challenge.
        
        Args:
            question_id: The question ID to clear
        """
        self._pending_challenges.pop(question_id, None)
