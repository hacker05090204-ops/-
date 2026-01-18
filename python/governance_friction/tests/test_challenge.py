"""
Tests for Phase-10 challenge questions.

Validates:
- Challenge questions are generated
- Answers are validated
- No auto-answer capability exists
"""

import pytest

from governance_friction.challenge import (
    ChallengeQuestionGenerator,
    ChallengeAnswerValidator,
)
from governance_friction.errors import ChallengeNotAnswered


class TestChallengeQuestionGenerator:
    """Test challenge question generation."""
    
    def test_generate_challenge(self, decision_id, context):
        """generate_challenge should create a valid question."""
        generator = ChallengeQuestionGenerator()
        challenge = generator.generate_challenge(decision_id, context)
        
        assert challenge.decision_id == decision_id
        assert challenge.question_id is not None
        assert challenge.question_text is not None
        assert len(challenge.question_text) > 0
        assert challenge.is_answered is False
    
    def test_context_aware_question(self, decision_id):
        """Questions should be context-aware."""
        generator = ChallengeQuestionGenerator()
        
        # Vulnerability context
        vuln_context = {"type": "vulnerability"}
        vuln_challenge = generator.generate_challenge(decision_id, vuln_context)
        assert "vulnerability" in vuln_challenge.question_text.lower()
        
        # Endpoint context
        endpoint_context = {"type": "endpoint"}
        endpoint_challenge = generator.generate_challenge(decision_id, endpoint_context)
        assert "component" in endpoint_challenge.question_text.lower() or "endpoint" in endpoint_challenge.question_text.lower()
    
    def test_question_has_context_summary(self, decision_id, context):
        """Challenge should include context summary."""
        generator = ChallengeQuestionGenerator()
        challenge = generator.generate_challenge(decision_id, context)
        
        assert challenge.context_summary is not None
        assert len(challenge.context_summary) > 0


class TestChallengeAnswerValidator:
    """Test challenge answer validation."""
    
    def test_empty_answer_raises(self, decision_id, context):
        """Empty answer should raise ChallengeNotAnswered."""
        generator = ChallengeQuestionGenerator()
        validator = ChallengeAnswerValidator()
        
        challenge = generator.generate_challenge(decision_id, context)
        
        with pytest.raises(ChallengeNotAnswered) as exc_info:
            validator.validate_answer(challenge, "")
        
        assert exc_info.value.decision_id == decision_id
        assert exc_info.value.question_id == challenge.question_id
    
    def test_whitespace_answer_raises(self, decision_id, context):
        """Whitespace-only answer should raise ChallengeNotAnswered."""
        generator = ChallengeQuestionGenerator()
        validator = ChallengeAnswerValidator()
        
        challenge = generator.generate_challenge(decision_id, context)
        
        with pytest.raises(ChallengeNotAnswered):
            validator.validate_answer(challenge, "   \n\t  ")
    
    def test_short_answer_raises(self, decision_id, context):
        """Too-short answer should raise ChallengeNotAnswered."""
        generator = ChallengeQuestionGenerator()
        validator = ChallengeAnswerValidator()
        
        challenge = generator.generate_challenge(decision_id, context)
        
        # Answer shorter than MIN_ANSWER_LENGTH (10)
        with pytest.raises(ChallengeNotAnswered):
            validator.validate_answer(challenge, "short")
    
    def test_valid_answer_succeeds(self, decision_id, context):
        """Valid answer should succeed."""
        generator = ChallengeQuestionGenerator()
        validator = ChallengeAnswerValidator()
        
        challenge = generator.generate_challenge(decision_id, context)
        
        answered = validator.validate_answer(
            challenge, 
            "This is a valid answer that demonstrates review of the content."
        )
        
        assert answered.is_answered is True
        assert answered.answer is not None
    
    def test_register_and_get_challenge(self, decision_id, context):
        """Challenges can be registered and retrieved."""
        generator = ChallengeQuestionGenerator()
        validator = ChallengeAnswerValidator()
        
        challenge = generator.generate_challenge(decision_id, context)
        validator.register_challenge(challenge)
        
        retrieved = validator.get_pending_challenge(challenge.question_id)
        
        assert retrieved is not None
        assert retrieved.question_id == challenge.question_id
    
    def test_clear_challenge(self, decision_id, context):
        """clear_challenge should remove pending challenge."""
        generator = ChallengeQuestionGenerator()
        validator = ChallengeAnswerValidator()
        
        challenge = generator.generate_challenge(decision_id, context)
        validator.register_challenge(challenge)
        
        validator.clear_challenge(challenge.question_id)
        
        assert validator.get_pending_challenge(challenge.question_id) is None


class TestChallengeNoAutoAnswer:
    """Test that no auto-answer capability exists."""
    
    def test_no_auto_answer_method(self):
        """ChallengeAnswerValidator should not have auto_answer method."""
        validator = ChallengeAnswerValidator()
        
        assert not hasattr(validator, "auto_answer")
        assert not hasattr(validator, "generate_answer")
        assert not hasattr(validator, "bypass_challenge")
        assert not hasattr(validator, "skip_challenge")
    
    def test_no_answer_in_question(self, decision_id, context):
        """Question should not contain the answer."""
        generator = ChallengeQuestionGenerator()
        challenge = generator.generate_challenge(decision_id, context)
        
        # Question should be a question, not contain an answer
        assert "?" in challenge.question_text or challenge.question_text.endswith(".")
        
        # No method to get expected answer
        assert not hasattr(generator, "get_expected_answer")
        assert not hasattr(generator, "get_answer")
