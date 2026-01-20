"""PHASE 06 TESTS — 2026 RE-IMPLEMENTATION"""

import pytest


class TestDecisionTypeEnum:
    def test_exists(self):
        from phase06_decisions import DecisionType
        assert DecisionType is not None

    def test_has_types(self):
        from phase06_decisions import DecisionType
        assert hasattr(DecisionType, 'PROCEED')
        assert hasattr(DecisionType, 'AUTHORIZE')


class TestDecisionOutcomeEnum:
    def test_exists(self):
        from phase06_decisions import DecisionOutcome
        assert DecisionOutcome is not None

    def test_has_outcomes(self):
        from phase06_decisions import DecisionOutcome
        assert hasattr(DecisionOutcome, 'APPROVED')
        assert hasattr(DecisionOutcome, 'REJECTED')


class TestDecisionPoint:
    def test_exists(self):
        from phase06_decisions import DecisionPoint
        assert DecisionPoint is not None

    def test_creation(self):
        from phase06_decisions import DecisionPoint, DecisionType
        point = DecisionPoint(
            point_id="test-001",
            description="Test decision",
            decision_type=DecisionType.CONFIRM
        )
        assert point.point_id == "test-001"


class TestDecisionRecord:
    def test_exists(self):
        from phase06_decisions import DecisionRecord
        assert DecisionRecord is not None

    def test_creation(self):
        from phase06_decisions import DecisionRecord, DecisionOutcome
        record = DecisionRecord(
            record_id="rec-001",
            point_id="point-001",
            actor_id="actor-001",
            outcome=DecisionOutcome.APPROVED
        )
        assert record.outcome == DecisionOutcome.APPROVED


class TestRequiresDecision:
    def test_always_requires_decision(self):
        """All operations MUST require human decision."""
        from phase06_decisions import requires_decision
        assert requires_decision("any_operation") is True
        assert requires_decision("scan") is True
        assert requires_decision("execute") is True


class TestIsDecisionApproved:
    def test_approved(self):
        from phase06_decisions import DecisionRecord, DecisionOutcome, is_decision_approved
        record = DecisionRecord("r-1", "p-1", "a-1", DecisionOutcome.APPROVED)
        assert is_decision_approved(record) is True

    def test_rejected(self):
        from phase06_decisions import DecisionRecord, DecisionOutcome, is_decision_approved
        record = DecisionRecord("r-1", "p-1", "a-1", DecisionOutcome.REJECTED)
        assert is_decision_approved(record) is False


class TestNoScoringInModule:
    """CRITICAL: Verify NO scoring/ranking exists."""
    def test_no_scoring_functions(self):
        from phase06_decisions import decisions
        public_attrs = [a for a in dir(decisions) if not a.startswith('_')]
        for attr in public_attrs:
            assert 'score' not in attr.lower(), f"FORBIDDEN: scoring found in {attr}"
            assert 'rank' not in attr.lower(), f"FORBIDDEN: ranking found in {attr}"
            assert 'priority' not in attr.lower(), f"FORBIDDEN: priority found in {attr}"


class TestPredefinedDecisionPoints:
    def test_scan_start_exists(self):
        from phase06_decisions import DECISION_SCAN_START
        assert DECISION_SCAN_START is not None

    def test_operation_execute_requires_admin(self):
        from phase06_decisions import DECISION_OPERATION_EXECUTE
        assert DECISION_OPERATION_EXECUTE.requires_admin is True


class TestPackageExports:
    def test_all_exports(self):
        from phase06_decisions import (
            DecisionType, DecisionOutcome, DecisionPoint,
            DecisionRecord, requires_decision, is_decision_approved
        )
        assert all([DecisionType, DecisionOutcome, DecisionPoint])
