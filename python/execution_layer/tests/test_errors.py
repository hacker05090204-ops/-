"""
Test Execution Layer Error Classification

Tests for error hierarchy and classification.

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

import pytest

from execution_layer.errors import (
    ExecutionLayerError,
    ScopeViolationError,
    UnsafeActionError,
    ForbiddenActionError,
    HumanApprovalRequired,
    TokenExpiredError,
    TokenAlreadyUsedError,
    TokenMismatchError,
    ArchitecturalViolationError,
    EvidenceCaptureError,
    BrowserSessionError,
    AuditIntegrityError,
    VideoPoCExistsError,
    StoreAttestationRequired,
    DuplicateExplorationLimitError,
    MCPConnectionError,
    MCPVerificationError,
    BountyPipelineConnectionError,
    BountyPipelineError,
    ThrottleConfigError,
    ThrottleLimitExceededError,
    DiskRetentionError,
    HeadlessOverrideError,
    HARD_STOP_ERRORS,
    BLOCKING_ERRORS,
    RECOVERABLE_ERRORS,
    is_hard_stop,
    is_blocking,
    is_recoverable,
)


class TestErrorHierarchy:
    """Test error class hierarchy."""
    
    def test_all_errors_inherit_from_base(self):
        """All errors should inherit from ExecutionLayerError."""
        error_classes = [
            ScopeViolationError,
            UnsafeActionError,
            ForbiddenActionError,
            HumanApprovalRequired,
            TokenExpiredError,
            TokenAlreadyUsedError,
            TokenMismatchError,
            ArchitecturalViolationError,
            EvidenceCaptureError,
            BrowserSessionError,
            AuditIntegrityError,
            VideoPoCExistsError,
            StoreAttestationRequired,
            DuplicateExplorationLimitError,
        ]
        
        for error_class in error_classes:
            assert issubclass(error_class, ExecutionLayerError)
    
    def test_base_error_inherits_from_exception(self):
        """Base error should inherit from Exception."""
        assert issubclass(ExecutionLayerError, Exception)


class TestHardStopErrors:
    """Test HARD STOP error classification."""
    
    def test_hard_stop_errors_tuple(self):
        """HARD_STOP_ERRORS should contain correct errors."""
        from execution_layer.errors import (
            ConfigurationError,
            ResponseValidationError,
            PartialEvidenceError,
            RetryExhaustedError,
            HashChainVerificationError,
            NavigationFailureError,
            CSPBlockError,
        )
        # Note: BrowserCrashError moved to RECOVERABLE (via BrowserFailure base class)
        expected = (
            ScopeViolationError,
            UnsafeActionError,
            ForbiddenActionError,
            ArchitecturalViolationError,
            AuditIntegrityError,
            StoreAttestationRequired,
            MCPConnectionError,
            BountyPipelineConnectionError,
            ThrottleConfigError,
            ThrottleLimitExceededError,
            DiskRetentionError,
            HeadlessOverrideError,
            # Hardening error types (Phase-4 Hardening)
            ConfigurationError,
            ResponseValidationError,
            PartialEvidenceError,
            RetryExhaustedError,
            HashChainVerificationError,
            # BrowserCrashError moved to RECOVERABLE
            NavigationFailureError,
            CSPBlockError,
        )
        assert HARD_STOP_ERRORS == expected
    
    def test_is_hard_stop_scope_violation(self):
        """ScopeViolationError should be HARD STOP."""
        error = ScopeViolationError("Out of scope")
        assert is_hard_stop(error) is True
    
    def test_is_hard_stop_unsafe_action(self):
        """UnsafeActionError should be HARD STOP."""
        error = UnsafeActionError("Unsafe action")
        assert is_hard_stop(error) is True
    
    def test_is_hard_stop_forbidden_action(self):
        """ForbiddenActionError should be HARD STOP."""
        error = ForbiddenActionError("Forbidden action")
        assert is_hard_stop(error) is True
    
    def test_is_hard_stop_architectural_violation(self):
        """ArchitecturalViolationError should be HARD STOP."""
        error = ArchitecturalViolationError("Boundary violation")
        assert is_hard_stop(error) is True
    
    def test_is_hard_stop_audit_integrity(self):
        """AuditIntegrityError should be HARD STOP."""
        error = AuditIntegrityError("Chain broken")
        assert is_hard_stop(error) is True
    
    def test_is_hard_stop_store_attestation(self):
        """StoreAttestationRequired should be HARD STOP."""
        error = StoreAttestationRequired("Attestation required")
        assert is_hard_stop(error) is True


class TestBlockingErrors:
    """Test blocking error classification."""
    
    def test_blocking_errors_tuple(self):
        """BLOCKING_ERRORS should contain correct errors."""
        from execution_layer.errors import AutomationDetectedError
        expected = (
            HumanApprovalRequired,
            AutomationDetectedError,  # Blocks until human decides
        )
        assert BLOCKING_ERRORS == expected
    
    def test_is_blocking_human_approval(self):
        """HumanApprovalRequired should be blocking."""
        error = HumanApprovalRequired("Approval needed")
        assert is_blocking(error) is True
    
    def test_is_blocking_not_hard_stop(self):
        """Blocking errors should not be HARD STOP."""
        error = HumanApprovalRequired("Approval needed")
        assert is_hard_stop(error) is False


class TestRecoverableErrors:
    """Test recoverable error classification."""
    
    def test_recoverable_errors_tuple(self):
        """RECOVERABLE_ERRORS should contain correct errors."""
        from execution_layer.errors import BrowserFailure
        # BrowserFailure catches all subclasses: BrowserCrashError, BrowserTimeoutError, BrowserDisconnectError
        expected = (
            TokenExpiredError,
            TokenAlreadyUsedError,
            TokenMismatchError,
            EvidenceCaptureError,
            BrowserSessionError,
            VideoPoCExistsError,
            DuplicateExplorationLimitError,
            MCPVerificationError,
            BountyPipelineError,
            # Resilience Layer Errors
            BrowserFailure,  # Catches all subclasses: Crash, Timeout, Disconnect
        )
        assert RECOVERABLE_ERRORS == expected
    
    def test_is_recoverable_token_expired(self):
        """TokenExpiredError should be recoverable."""
        error = TokenExpiredError("Token expired")
        assert is_recoverable(error) is True
    
    def test_is_recoverable_token_used(self):
        """TokenAlreadyUsedError should be recoverable."""
        error = TokenAlreadyUsedError("Token used")
        assert is_recoverable(error) is True
    
    def test_is_recoverable_token_mismatch(self):
        """TokenMismatchError should be recoverable."""
        error = TokenMismatchError("Token mismatch")
        assert is_recoverable(error) is True
    
    def test_is_recoverable_evidence_capture(self):
        """EvidenceCaptureError should be recoverable."""
        error = EvidenceCaptureError("Capture failed")
        assert is_recoverable(error) is True
    
    def test_is_recoverable_browser_session(self):
        """BrowserSessionError should be recoverable."""
        error = BrowserSessionError("Session error")
        assert is_recoverable(error) is True
    
    def test_is_recoverable_video_poc_exists(self):
        """VideoPoCExistsError should be recoverable."""
        error = VideoPoCExistsError("PoC exists")
        assert is_recoverable(error) is True
    
    def test_is_recoverable_duplicate_limit(self):
        """DuplicateExplorationLimitError should be recoverable."""
        error = DuplicateExplorationLimitError("Limit reached")
        assert is_recoverable(error) is True


class TestErrorClassificationMutualExclusion:
    """Test that error classifications are mutually exclusive."""
    
    def test_hard_stop_not_blocking(self):
        """HARD STOP errors should not be blocking."""
        for error_class in HARD_STOP_ERRORS:
            error = error_class("test")
            assert is_blocking(error) is False
    
    def test_hard_stop_not_recoverable(self):
        """HARD STOP errors should not be recoverable."""
        for error_class in HARD_STOP_ERRORS:
            error = error_class("test")
            assert is_recoverable(error) is False
    
    def test_blocking_not_hard_stop(self):
        """Blocking errors should not be HARD STOP."""
        for error_class in BLOCKING_ERRORS:
            error = error_class("test")
            assert is_hard_stop(error) is False
    
    def test_blocking_not_recoverable(self):
        """Blocking errors should not be recoverable."""
        for error_class in BLOCKING_ERRORS:
            error = error_class("test")
            assert is_recoverable(error) is False
    
    def test_recoverable_not_hard_stop(self):
        """Recoverable errors should not be HARD STOP."""
        for error_class in RECOVERABLE_ERRORS:
            error = error_class("test")
            assert is_hard_stop(error) is False
    
    def test_recoverable_not_blocking(self):
        """Recoverable errors should not be blocking."""
        for error_class in RECOVERABLE_ERRORS:
            error = error_class("test")
            assert is_blocking(error) is False


class TestErrorMessages:
    """Test error message formatting."""
    
    def test_scope_violation_message(self):
        """ScopeViolationError should preserve message."""
        msg = "Target 'evil.com' is outside authorized scope"
        error = ScopeViolationError(msg)
        assert str(error) == msg
    
    def test_forbidden_action_message(self):
        """ForbiddenActionError should preserve message."""
        msg = "Action 'login' is forbidden — HARD STOP"
        error = ForbiddenActionError(msg)
        assert str(error) == msg
    
    def test_token_expired_message(self):
        """TokenExpiredError should preserve message."""
        msg = "Token 'abc123' has expired — request new approval"
        error = TokenExpiredError(msg)
        assert str(error) == msg
    
    def test_video_poc_exists_message(self):
        """VideoPoCExistsError should preserve message."""
        msg = "VideoPoC already exists for finding_id 'finding-1'"
        error = VideoPoCExistsError(msg)
        assert str(error) == msg


class TestErrorRaising:
    """Test error raising and catching."""
    
    def test_catch_by_base_class(self):
        """Should catch all errors by base class."""
        errors = [
            ScopeViolationError("test"),
            ForbiddenActionError("test"),
            TokenExpiredError("test"),
            VideoPoCExistsError("test"),
        ]
        
        for error in errors:
            with pytest.raises(ExecutionLayerError):
                raise error
    
    def test_catch_by_specific_class(self):
        """Should catch errors by specific class."""
        with pytest.raises(ScopeViolationError):
            raise ScopeViolationError("Out of scope")
        
        with pytest.raises(ForbiddenActionError):
            raise ForbiddenActionError("Forbidden")
        
        with pytest.raises(TokenExpiredError):
            raise TokenExpiredError("Expired")
    
    def test_error_inheritance_catching(self):
        """Should catch derived errors by parent class."""
        # All should be catchable as ExecutionLayerError
        try:
            raise ScopeViolationError("test")
        except ExecutionLayerError as e:
            assert isinstance(e, ScopeViolationError)
        
        try:
            raise TokenExpiredError("test")
        except ExecutionLayerError as e:
            assert isinstance(e, TokenExpiredError)

