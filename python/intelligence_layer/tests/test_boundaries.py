"""
Tests for Phase-8 Boundary Guard

Verifies that:
- Forbidden imports are detected
- Network access is blocked
- Forbidden actions raise errors
"""

import pytest

from intelligence_layer.boundaries import BoundaryGuard
from intelligence_layer.errors import (
    ArchitecturalViolationError,
    NetworkAccessAttemptError,
)


class TestForbiddenImports:
    """Tests for forbidden import detection."""
    
    def test_execution_layer_import_forbidden(self):
        """Verify execution_layer import raises error."""
        with pytest.raises(ArchitecturalViolationError) as exc_info:
            BoundaryGuard.check_import("execution_layer")
        
        assert "execution_layer" in str(exc_info.value)
    
    def test_artifact_scanner_import_forbidden(self):
        """Verify artifact_scanner import raises error."""
        with pytest.raises(ArchitecturalViolationError) as exc_info:
            BoundaryGuard.check_import("artifact_scanner")
        
        assert "artifact_scanner" in str(exc_info.value)
    
    def test_httpx_import_forbidden(self):
        """Verify httpx import raises NetworkAccessAttemptError."""
        with pytest.raises(NetworkAccessAttemptError) as exc_info:
            BoundaryGuard.check_import("httpx")
        
        assert "httpx" in str(exc_info.value)
    
    def test_requests_import_forbidden(self):
        """Verify requests import raises NetworkAccessAttemptError."""
        with pytest.raises(NetworkAccessAttemptError) as exc_info:
            BoundaryGuard.check_import("requests")
        
        assert "requests" in str(exc_info.value)
    
    def test_aiohttp_import_forbidden(self):
        """Verify aiohttp import raises NetworkAccessAttemptError."""
        with pytest.raises(NetworkAccessAttemptError) as exc_info:
            BoundaryGuard.check_import("aiohttp")
        
        assert "aiohttp" in str(exc_info.value)
    
    def test_socket_import_forbidden(self):
        """Verify socket import raises NetworkAccessAttemptError."""
        with pytest.raises(NetworkAccessAttemptError) as exc_info:
            BoundaryGuard.check_import("socket")
        
        assert "socket" in str(exc_info.value)
    
    def test_urllib_request_import_forbidden(self):
        """Verify urllib.request import raises NetworkAccessAttemptError."""
        with pytest.raises(NetworkAccessAttemptError) as exc_info:
            BoundaryGuard.check_import("urllib.request")
        
        assert "urllib.request" in str(exc_info.value)
    
    def test_allowed_import_does_not_raise(self):
        """Verify allowed imports do not raise errors."""
        # These should not raise
        BoundaryGuard.check_import("datetime")
        BoundaryGuard.check_import("typing")
        BoundaryGuard.check_import("dataclasses")


class TestNetworkAccessProhibition:
    """Tests for network access prohibition."""
    
    def test_check_network_import_httpx(self):
        """Verify httpx is blocked as network module."""
        with pytest.raises(NetworkAccessAttemptError):
            BoundaryGuard.check_network_import("httpx")
    
    def test_check_network_import_requests(self):
        """Verify requests is blocked as network module."""
        with pytest.raises(NetworkAccessAttemptError):
            BoundaryGuard.check_network_import("requests")
    
    def test_check_network_import_aiohttp(self):
        """Verify aiohttp is blocked as network module."""
        with pytest.raises(NetworkAccessAttemptError):
            BoundaryGuard.check_network_import("aiohttp")
    
    def test_check_network_import_socket(self):
        """Verify socket is blocked as network module."""
        with pytest.raises(NetworkAccessAttemptError):
            BoundaryGuard.check_network_import("socket")
    
    def test_check_network_import_urllib3(self):
        """Verify urllib3 is blocked as network module."""
        with pytest.raises(NetworkAccessAttemptError):
            BoundaryGuard.check_network_import("urllib3")
    
    def test_check_network_import_http_client(self):
        """Verify http.client is blocked as network module."""
        with pytest.raises(NetworkAccessAttemptError):
            BoundaryGuard.check_network_import("http.client")
    
    def test_non_network_module_allowed(self):
        """Verify non-network modules are allowed."""
        # Should not raise
        BoundaryGuard.check_network_import("json")
        BoundaryGuard.check_network_import("os")


class TestForbiddenActions:
    """Tests for forbidden action detection."""
    
    def test_validate_bug_forbidden(self):
        """Verify validate_bug action is forbidden."""
        with pytest.raises(ArchitecturalViolationError):
            BoundaryGuard.check_forbidden_action("validate_bug")
    
    def test_is_true_positive_forbidden(self):
        """Verify is_true_positive action is forbidden."""
        with pytest.raises(ArchitecturalViolationError):
            BoundaryGuard.check_forbidden_action("is_true_positive")
    
    def test_generate_poc_forbidden(self):
        """Verify generate_poc action is forbidden."""
        with pytest.raises(ArchitecturalViolationError):
            BoundaryGuard.check_forbidden_action("generate_poc")
    
    def test_generate_exploit_forbidden(self):
        """Verify generate_exploit action is forbidden."""
        with pytest.raises(ArchitecturalViolationError):
            BoundaryGuard.check_forbidden_action("generate_exploit")
    
    def test_determine_cve_forbidden(self):
        """Verify determine_cve action is forbidden."""
        with pytest.raises(ArchitecturalViolationError):
            BoundaryGuard.check_forbidden_action("determine_cve")
    
    def test_guarantee_accuracy_forbidden(self):
        """Verify guarantee_accuracy action is forbidden."""
        with pytest.raises(ArchitecturalViolationError):
            BoundaryGuard.check_forbidden_action("guarantee_accuracy")
    
    def test_auto_submit_forbidden(self):
        """Verify auto_submit action is forbidden."""
        with pytest.raises(ArchitecturalViolationError):
            BoundaryGuard.check_forbidden_action("auto_submit")
    
    def test_recommend_forbidden(self):
        """Verify recommend action is forbidden."""
        with pytest.raises(ArchitecturalViolationError):
            BoundaryGuard.check_forbidden_action("recommend")
    
    def test_predict_forbidden(self):
        """Verify predict action is forbidden."""
        with pytest.raises(ArchitecturalViolationError):
            BoundaryGuard.check_forbidden_action("predict")
    
    def test_prioritize_forbidden(self):
        """Verify prioritize action is forbidden."""
        with pytest.raises(ArchitecturalViolationError):
            BoundaryGuard.check_forbidden_action("prioritize")
    
    def test_rank_forbidden(self):
        """Verify rank action is forbidden."""
        with pytest.raises(ArchitecturalViolationError):
            BoundaryGuard.check_forbidden_action("rank")
    
    def test_compare_reviewers_forbidden(self):
        """Verify compare_reviewers action is forbidden."""
        with pytest.raises(ArchitecturalViolationError):
            BoundaryGuard.check_forbidden_action("compare_reviewers")
    
    def test_write_decision_forbidden(self):
        """Verify write_decision action is forbidden."""
        with pytest.raises(ArchitecturalViolationError):
            BoundaryGuard.check_forbidden_action("write_decision")
    
    def test_modify_audit_forbidden(self):
        """Verify modify_audit action is forbidden."""
        with pytest.raises(ArchitecturalViolationError):
            BoundaryGuard.check_forbidden_action("modify_audit")
    
    def test_allowed_action_does_not_raise(self):
        """Verify allowed actions do not raise errors."""
        # These should not raise
        BoundaryGuard.check_forbidden_action("get_decisions")
        BoundaryGuard.check_forbidden_action("compute_similarity")
        BoundaryGuard.check_forbidden_action("check_duplicates")


class TestAssertionMethods:
    """Tests for assertion methods."""
    
    def test_assert_read_only_does_not_raise(self):
        """Verify assert_read_only does not raise."""
        # Should not raise
        BoundaryGuard.assert_read_only()
    
    def test_assert_no_network_does_not_raise(self):
        """Verify assert_no_network does not raise."""
        # Should not raise
        BoundaryGuard.assert_no_network()
    
    def test_assert_human_authority_does_not_raise(self):
        """Verify assert_human_authority does not raise."""
        # Should not raise
        BoundaryGuard.assert_human_authority()


class TestForbiddenImportSets:
    """Tests for forbidden import sets."""
    
    def test_forbidden_imports_contains_execution_layer(self):
        """Verify FORBIDDEN_IMPORTS contains execution_layer."""
        assert "execution_layer" in BoundaryGuard.FORBIDDEN_IMPORTS
    
    def test_forbidden_imports_contains_artifact_scanner(self):
        """Verify FORBIDDEN_IMPORTS contains artifact_scanner."""
        assert "artifact_scanner" in BoundaryGuard.FORBIDDEN_IMPORTS
    
    def test_forbidden_imports_contains_network_modules(self):
        """Verify FORBIDDEN_IMPORTS contains network modules."""
        assert "httpx" in BoundaryGuard.FORBIDDEN_IMPORTS
        assert "requests" in BoundaryGuard.FORBIDDEN_IMPORTS
        assert "aiohttp" in BoundaryGuard.FORBIDDEN_IMPORTS
        assert "socket" in BoundaryGuard.FORBIDDEN_IMPORTS
    
    def test_network_modules_set(self):
        """Verify NETWORK_MODULES set is correct."""
        assert "httpx" in BoundaryGuard.NETWORK_MODULES
        assert "requests" in BoundaryGuard.NETWORK_MODULES
        assert "aiohttp" in BoundaryGuard.NETWORK_MODULES
        assert "socket" in BoundaryGuard.NETWORK_MODULES
        assert "urllib.request" in BoundaryGuard.NETWORK_MODULES
        assert "urllib3" in BoundaryGuard.NETWORK_MODULES
        assert "http.client" in BoundaryGuard.NETWORK_MODULES
    
    def test_forbidden_actions_set(self):
        """Verify FORBIDDEN_ACTIONS set contains key actions."""
        assert "validate_bug" in BoundaryGuard.FORBIDDEN_ACTIONS
        assert "generate_poc" in BoundaryGuard.FORBIDDEN_ACTIONS
        assert "determine_cve" in BoundaryGuard.FORBIDDEN_ACTIONS
        assert "auto_submit" in BoundaryGuard.FORBIDDEN_ACTIONS
        assert "recommend" in BoundaryGuard.FORBIDDEN_ACTIONS
        assert "predict" in BoundaryGuard.FORBIDDEN_ACTIONS
        assert "compare_reviewers" in BoundaryGuard.FORBIDDEN_ACTIONS
