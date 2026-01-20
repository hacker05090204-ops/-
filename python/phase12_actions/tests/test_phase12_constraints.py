"""PHASE 12 TESTS"""
import pytest

class TestConstraintType:
    def test_exists(self):
        from phase12_actions import ConstraintType
        assert hasattr(ConstraintType, 'REQUIRES_APPROVAL')

class TestMandatoryConstraints:
    def test_human_approval_is_mandatory(self):
        from phase12_actions import CONSTRAINT_HUMAN_APPROVAL
        assert CONSTRAINT_HUMAN_APPROVAL.is_mandatory is True

    def test_no_auto_exploit_is_mandatory(self):
        from phase12_actions import CONSTRAINT_NO_AUTO_EXPLOIT
        assert CONSTRAINT_NO_AUTO_EXPLOIT.is_mandatory is True

class TestIsConstraintSatisfied:
    def test_requires_approval_without_approval(self):
        from phase12_actions import CONSTRAINT_HUMAN_APPROVAL, is_constraint_satisfied
        assert is_constraint_satisfied(CONSTRAINT_HUMAN_APPROVAL, has_approval=False) is False

    def test_requires_approval_with_approval(self):
        from phase12_actions import CONSTRAINT_HUMAN_APPROVAL, is_constraint_satisfied
        assert is_constraint_satisfied(CONSTRAINT_HUMAN_APPROVAL, has_approval=True) is True

class TestGetMandatoryConstraints:
    def test_returns_mandatory(self):
        from phase12_actions import get_mandatory_constraints, CONSTRAINT_HUMAN_APPROVAL
        constraints = get_mandatory_constraints()
        assert len(constraints) >= 2
        assert CONSTRAINT_HUMAN_APPROVAL in constraints
