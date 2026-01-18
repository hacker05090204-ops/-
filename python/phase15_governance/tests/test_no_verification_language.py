"""
Phase-15 No Verification Language Tests

Tests that forbidden verification language does not appear in code.
All tests must FAIL initially until implementation exists.

MANDATORY DECLARATION:
"Phase-15 may ONLY implement enforcement, validation, logging, and blocking."
"""

import pytest
import os
import glob


FORBIDDEN_WORDS = [
    "verify", "verified", "verification",
    "accurate", "accuracy",
    "confidence",
    "correct", "correctness",
    "reliable", "reliability",
    "confirmed", "confirmation",
]


class TestNoVerificationLanguage:
    """Tests that verification language is absent from code."""

    def test_no_forbidden_words_in_enforcer(self) -> None:
        """Test that enforcer has no forbidden words."""
        try:
            from phase15_governance import enforcer
            import inspect
            source = inspect.getsource(enforcer)
            source_lower = source.lower()
            
            for word in FORBIDDEN_WORDS:
                assert word not in source_lower, f"Forbidden word '{word}' in enforcer"
        except ImportError:
            pytest.fail("enforcer module does not exist")

    def test_no_forbidden_words_in_validator(self) -> None:
        """Test that validator has no forbidden words."""
        try:
            from phase15_governance import validator
            import inspect
            source = inspect.getsource(validator)
            source_lower = source.lower()
            
            for word in FORBIDDEN_WORDS:
                assert word not in source_lower, f"Forbidden word '{word}' in validator"
        except ImportError:
            pytest.fail("validator module does not exist")


    def test_no_forbidden_words_in_blocker(self) -> None:
        """Test that blocker has no forbidden words."""
        try:
            from phase15_governance import blocker
            import inspect
            source = inspect.getsource(blocker)
            source_lower = source.lower()
            
            for word in FORBIDDEN_WORDS:
                assert word not in source_lower, f"Forbidden word '{word}' in blocker"
        except ImportError:
            pytest.fail("blocker module does not exist")

    def test_no_forbidden_words_in_audit(self) -> None:
        """Test that audit has no forbidden words."""
        try:
            from phase15_governance import audit
            import inspect
            source = inspect.getsource(audit)
            source_lower = source.lower()
            
            for word in FORBIDDEN_WORDS:
                assert word not in source_lower, f"Forbidden word '{word}' in audit"
        except ImportError:
            pytest.fail("audit module does not exist")


class TestNoVerificationClaims:
    """Tests that no verification claims appear in output."""

    def test_enforcer_output_no_verification_claims(self) -> None:
        """Test that enforcer output has no verification claims."""
        try:
            from phase15_governance.enforcer import enforce_rule
            from phase15_governance.errors import GovernanceBlockedError
            
            rule = {"type": "block_write", "target": "phase13"}
            context = {"action": "write", "target": "phase13", "human_initiated": True}
            
            try:
                enforce_rule(rule=rule, context=context)
            except GovernanceBlockedError as e:
                error_msg = str(e).lower()
                for word in FORBIDDEN_WORDS:
                    assert word not in error_msg, f"Forbidden word '{word}' in error"
        except ImportError:
            pytest.fail("Implementation does not exist")

    def test_validator_output_no_verification_claims(self) -> None:
        """Test that validator output has no verification claims."""
        try:
            from phase15_governance.validator import validate_input
            from phase15_governance.errors import ValidationError
            
            constraint = {"type": "string", "max_length": 5}
            
            try:
                validate_input(value="too long", constraint=constraint)
            except ValidationError as e:
                error_msg = str(e).lower()
                for word in FORBIDDEN_WORDS:
                    assert word not in error_msg, f"Forbidden word '{word}' in error"
        except ImportError:
            pytest.fail("Implementation does not exist")
