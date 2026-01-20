"""PHASE 18 TESTS"""
import pytest

class TestSafetyChecks:
    def test_check_human_approval_is_mandatory(self):
        from phase18_runtime import CHECK_HUMAN_APPROVAL
        assert CHECK_HUMAN_APPROVAL.is_mandatory is True

    def test_run_safety_check_passes(self):
        from phase18_runtime import run_safety_check, CHECK_HUMAN_APPROVAL, SafetyCheckResult
        report = run_safety_check(CHECK_HUMAN_APPROVAL, True)
        assert report.result == SafetyCheckResult.PASSED

    def test_run_safety_check_fails(self):
        from phase18_runtime import run_safety_check, CHECK_HUMAN_APPROVAL, SafetyCheckResult
        report = run_safety_check(CHECK_HUMAN_APPROVAL, False)
        assert report.result == SafetyCheckResult.FAILED

class TestAllSafetyChecksPassed:
    def test_all_passed(self):
        from phase18_runtime import run_mandatory_safety_checks, all_safety_checks_passed
        reports = run_mandatory_safety_checks(True, True, True)
        assert all_safety_checks_passed(reports) is True

    def test_not_all_passed(self):
        from phase18_runtime import run_mandatory_safety_checks, all_safety_checks_passed
        reports = run_mandatory_safety_checks(False, True, True)
        assert all_safety_checks_passed(reports) is False

class TestRunMandatorySafetyChecks:
    def test_returns_three_reports(self):
        from phase18_runtime import run_mandatory_safety_checks
        reports = run_mandatory_safety_checks(True, True, True)
        assert len(reports) == 3

    def test_all_fail_when_all_false(self):
        from phase18_runtime import run_mandatory_safety_checks, SafetyCheckResult
        reports = run_mandatory_safety_checks(False, False, False)
        assert all(r.result == SafetyCheckResult.FAILED for r in reports)
