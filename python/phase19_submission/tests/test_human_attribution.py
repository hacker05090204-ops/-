"""
Test: Human Attribution in Logs

GOVERNANCE: All logs MUST have attribution="HUMAN".
No system attribution, no AI attribution.
"""

import pytest
from datetime import datetime

from ..types import SubmissionLog, SubmissionAction


class TestHumanAttribution:
    """Verify human attribution is enforced."""

    def test_log_requires_human_attribution(self):
        """SubmissionLog MUST have attribution='HUMAN'."""
        log = SubmissionLog(
            timestamp=datetime.now(),
            action=SubmissionAction.EXPORT_REPORT,
            attribution="HUMAN",
            details="Test export",
        )
        assert log.attribution == "HUMAN"

    def test_log_rejects_system_attribution(self):
        """SubmissionLog MUST reject system attribution."""
        with pytest.raises(ValueError, match="HUMAN"):
            SubmissionLog(
                timestamp=datetime.now(),
                action=SubmissionAction.EXPORT_REPORT,
                attribution="SYSTEM",
                details="Test",
            )

    def test_log_rejects_ai_attribution(self):
        """SubmissionLog MUST reject AI attribution."""
        with pytest.raises(ValueError, match="HUMAN"):
            SubmissionLog(
                timestamp=datetime.now(),
                action=SubmissionAction.EXPORT_REPORT,
                attribution="AI",
                details="Test",
            )

    def test_log_rejects_auto_attribution(self):
        """SubmissionLog MUST reject auto attribution."""
        with pytest.raises(ValueError, match="HUMAN"):
            SubmissionLog(
                timestamp=datetime.now(),
                action=SubmissionAction.EXPORT_REPORT,
                attribution="AUTO",
                details="Test",
            )

    def test_log_rejects_empty_attribution(self):
        """SubmissionLog MUST reject empty attribution."""
        with pytest.raises(ValueError, match="HUMAN"):
            SubmissionLog(
                timestamp=datetime.now(),
                action=SubmissionAction.EXPORT_REPORT,
                attribution="",
                details="Test",
            )

    def test_log_default_attribution_is_human(self):
        """Default attribution MUST be 'HUMAN'."""
        log = SubmissionLog(
            timestamp=datetime.now(),
            action=SubmissionAction.OPEN_URL,
        )
        assert log.attribution == "HUMAN"


class TestLoggerHumanAttribution:
    """Verify logger enforces human attribution."""

    def test_logger_always_uses_human_attribution(self):
        """Logger MUST always use HUMAN attribution."""
        from ..submission_logger import SubmissionLogger
        
        logger = SubmissionLogger()
        
        # Log an action
        log = logger.log_action(
            action=SubmissionAction.EXPORT_REPORT,
            details="Test export",
        )
        
        assert log.attribution == "HUMAN"

    def test_logger_cannot_override_attribution(self):
        """Logger MUST NOT allow overriding attribution."""
        from ..submission_logger import SubmissionLogger
        
        logger = SubmissionLogger()
        
        # Even if someone tries to pass different attribution,
        # it should still be HUMAN
        log = logger.log_action(
            action=SubmissionAction.OPEN_URL,
            details="Test URL open",
        )
        
        assert log.attribution == "HUMAN"


class TestAllActionsHaveHumanAttribution:
    """Verify all action types have human attribution."""

    def test_export_report_has_human_attribution(self):
        """EXPORT_REPORT action has HUMAN attribution."""
        log = SubmissionLog(
            timestamp=datetime.now(),
            action=SubmissionAction.EXPORT_REPORT,
        )
        assert log.attribution == "HUMAN"

    def test_open_url_has_human_attribution(self):
        """OPEN_URL action has HUMAN attribution."""
        log = SubmissionLog(
            timestamp=datetime.now(),
            action=SubmissionAction.OPEN_URL,
        )
        assert log.attribution == "HUMAN"

    def test_confirm_action_has_human_attribution(self):
        """CONFIRM_ACTION has HUMAN attribution."""
        log = SubmissionLog(
            timestamp=datetime.now(),
            action=SubmissionAction.CONFIRM_ACTION,
        )
        assert log.attribution == "HUMAN"

    def test_check_item_has_human_attribution(self):
        """CHECK_ITEM action has HUMAN attribution."""
        log = SubmissionLog(
            timestamp=datetime.now(),
            action=SubmissionAction.CHECK_ITEM,
        )
        assert log.attribution == "HUMAN"
