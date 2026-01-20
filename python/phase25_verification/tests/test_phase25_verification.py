"""PHASE 25 TESTS — NON-AUTHORITATIVE VERIFICATION"""
import pytest

class TestVerificationResult:
    def test_always_non_authoritative(self):
        """CRITICAL: All verification results MUST be non-authoritative."""
        from phase25_verification import create_verification_result, VerificationStatus
        result = create_verification_result("test", VerificationStatus.VERIFIED, "Test")
        assert result.is_authoritative is False

class TestVerifyHumanApprovalRecorded:
    def test_verified_with_approval_id(self):
        from phase25_verification import verify_human_approval_recorded, VerificationStatus
        result = verify_human_approval_recorded("approval-123")
        assert result.status == VerificationStatus.VERIFIED

    def test_not_verified_without_approval_id(self):
        from phase25_verification import verify_human_approval_recorded, VerificationStatus
        result = verify_human_approval_recorded(None)
        assert result.status == VerificationStatus.NOT_VERIFIED

class TestVerifyAuditTrailExists:
    def test_verified_with_entries(self):
        from phase25_verification import verify_audit_trail_exists, VerificationStatus
        result = verify_audit_trail_exists(10)
        assert result.status == VerificationStatus.VERIFIED

    def test_not_verified_with_no_entries(self):
        from phase25_verification import verify_audit_trail_exists, VerificationStatus
        result = verify_audit_trail_exists(0)
        assert result.status == VerificationStatus.NOT_VERIFIED

class TestIsVerificationPassed:
    def test_passed_when_verified(self):
        from phase25_verification import create_verification_result, VerificationStatus, is_verification_passed
        result = create_verification_result("test", VerificationStatus.VERIFIED, "OK")
        assert is_verification_passed(result) is True

    def test_not_passed_when_not_verified(self):
        from phase25_verification import create_verification_result, VerificationStatus, is_verification_passed
        result = create_verification_result("test", VerificationStatus.NOT_VERIFIED, "Failed")
        assert is_verification_passed(result) is False

class TestNonAuthoritative:
    def test_all_results_non_authoritative(self):
        """All verification helpers must produce non-authoritative results."""
        from phase25_verification import verify_human_approval_recorded, verify_audit_trail_exists
        
        result1 = verify_human_approval_recorded("test")
        result2 = verify_audit_trail_exists(5)
        
        assert result1.is_authoritative is False
        assert result2.is_authoritative is False
