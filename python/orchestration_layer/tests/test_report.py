# PHASE-12 GOVERNANCE COMPLIANCE
# This module is part of Phase-12 (Runtime Orchestration Implementation)
#
# FORBIDDEN CAPABILITIES:
# - NO execution logic
# - NO decision logic
# - NO submission logic
# - NO network access
# - NO browser automation
# - NO friction wiring or execution
# - NO auto-approval
# - NO frozen phase modification
#
# MANDATORY DECLARATION:
# Phase-12 implements orchestration without altering execution,
# human authority, governance friction, or audit invariants.

"""
Phase-12 Track 5 Integration Report Tests

TEST CATEGORY: Per-Track Tests - Track 5 (Priority: MEDIUM)
EXECUTION ORDER: 4 (After Property Tests)

Test IDs:
- TEST-T5-001: Reports are NOT auto-submitted
- TEST-T5-002: auto_submit_allowed is always False
- TEST-T5-003: Human confirmation required for export
- TEST-T5-004: Export does NOT auto-submit
- TEST-T5-005: No network imports in report module
"""

import ast
import inspect
import pytest

from orchestration_layer.report import (
    generate_report,
    export_report,
    get_report_status,
)
from orchestration_layer.errors import (
    AutomationAttemptError,
    NoSubmissionCapabilityError,
)
from orchestration_layer.types import IntegrationReport


@pytest.mark.track5
class TestReportNoAutoSubmit:
    """Test IDs: TEST-T5-001, TEST-T5-002 - Requirement: REQ-3.5.3"""
    
    def test_reports_not_auto_submitted(self):
        """TEST-T5-001: Verify reports are NOT auto-submitted."""
        # Generate a report
        report = generate_report(
            workflow_id="workflow_123",
            phase_summaries={
                "phase_4": "Execution completed",
                "phase_5": "Decision recorded",
            },
            correlation_ids=["corr_abc", "corr_def"],
        )
        
        # Verify report is immutable (frozen dataclass)
        assert isinstance(report, IntegrationReport)
        
        # Verify report is NOT auto-submitted
        assert report.auto_submit_allowed is False
        
        # Verify human confirmation is required
        assert report.human_confirmation_required is True
        
        # Verify no auto action
        assert report.no_auto_action is True
        
        # Verify attempting to modify raises error
        with pytest.raises(AttributeError):
            report.auto_submit_allowed = True
    
    def test_auto_submit_allowed_always_false(self):
        """TEST-T5-002: Verify auto_submit_allowed is always False."""
        # Generate multiple reports with different inputs
        reports = [
            generate_report("wf_1", {}, []),
            generate_report("wf_2", {"phase_1": "summary"}, []),
            generate_report("wf_3", {"p1": "s1", "p2": "s2"}, ["c1", "c2"]),
        ]
        
        # ALL reports must have auto_submit_allowed=False
        for report in reports:
            assert report.auto_submit_allowed is False
            assert report.human_confirmation_required is True
            assert report.no_auto_action is True
    
    def test_report_generation_validates_inputs(self):
        """Verify report generation validates inputs."""
        # Invalid workflow_id
        with pytest.raises(AutomationAttemptError):
            generate_report("", {}, [])
        
        with pytest.raises(AutomationAttemptError):
            generate_report("   ", {}, [])
        
        with pytest.raises(AutomationAttemptError):
            generate_report(123, {}, [])  # type: ignore
        
        # Invalid phase_summaries
        with pytest.raises(AutomationAttemptError):
            generate_report("wf_1", "not_a_dict", [])  # type: ignore
        
        # Invalid correlation_ids
        with pytest.raises(AutomationAttemptError):
            generate_report("wf_1", {}, "not_a_list")  # type: ignore


@pytest.mark.track5
class TestReportExport:
    """Test IDs: TEST-T5-003, TEST-T5-004 - Requirement: REQ-4.4.2"""
    
    def test_export_requires_human_confirmation(self):
        """TEST-T5-003: Verify export requires human confirmation."""
        report = generate_report(
            workflow_id="workflow_456",
            phase_summaries={"phase_1": "Complete"},
            correlation_ids=["corr_1"],
        )
        
        # Valid export with human confirmation
        exported = export_report(report, "human_token_abc123")
        
        assert exported["report_id"] == report.report_id
        assert exported["workflow_id"] == report.workflow_id
        assert exported["human_confirmation_required"] is True
        assert exported["export_metadata"]["human_confirmed"] is True
        
        # Invalid: empty token
        with pytest.raises(AutomationAttemptError):
            export_report(report, "")
        
        # Invalid: whitespace token
        with pytest.raises(AutomationAttemptError):
            export_report(report, "   ")
        
        # Invalid: non-string token
        with pytest.raises(AutomationAttemptError):
            export_report(report, 12345)  # type: ignore
        
        # Invalid: not a report
        with pytest.raises(AutomationAttemptError):
            export_report("not_a_report", "token")  # type: ignore
    
    def test_export_does_not_auto_submit(self):
        """TEST-T5-004: Verify export does NOT auto-submit."""
        report = generate_report(
            workflow_id="workflow_789",
            phase_summaries={"phase_2": "Done"},
            correlation_ids=[],
        )
        
        exported = export_report(report, "human_confirmation_token")
        
        # Verify export metadata confirms NO auto-submit
        assert exported["auto_submit_allowed"] is False
        assert exported["export_metadata"]["auto_submitted"] is False
        assert exported["export_metadata"]["network_transmitted"] is False
        
        # Verify no_auto_action is preserved
        assert exported["no_auto_action"] is True
    
    def test_get_report_status(self):
        """Verify get_report_status returns correct information."""
        report = generate_report(
            workflow_id="workflow_status",
            phase_summaries={"p1": "s1", "p2": "s2", "p3": "s3"},
            correlation_ids=["c1", "c2"],
        )
        
        status = get_report_status(report)
        
        assert status["report_id"] == report.report_id
        assert status["workflow_id"] == "workflow_status"
        assert status["human_confirmation_required"] is True
        assert status["no_auto_action"] is True
        assert status["auto_submit_allowed"] is False
        assert status["phase_count"] == 3
        assert status["correlation_count"] == 2
        
        # Invalid: not a report
        with pytest.raises(AutomationAttemptError):
            get_report_status("not_a_report")  # type: ignore


@pytest.mark.track5
class TestReportNoNetworkImports:
    """Test ID: TEST-T5-005 - Requirement: Section 6.5"""
    
    def test_no_network_imports_in_report_module(self):
        """TEST-T5-005: Verify no network imports in report module."""
        import orchestration_layer.report as report_module
        
        # Get the source code
        source = inspect.getsource(report_module)
        
        # Parse the AST
        tree = ast.parse(source)
        
        # Forbidden network-related imports
        forbidden_imports = {
            "httpx", "requests", "aiohttp", "urllib", "urllib3",
            "socket", "ssl", "http", "http.client", "ftplib",
            "smtplib", "poplib", "imaplib", "nntplib", "telnetlib",
            "asyncio",  # Could be used for network
        }
        
        # Check all imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split(".")[0]
                    assert module_name not in forbidden_imports, \
                        f"Forbidden import found: {alias.name}"
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module.split(".")[0]
                    assert module_name not in forbidden_imports, \
                        f"Forbidden import found: from {node.module}"
    
    def test_no_submit_functions_in_report_module(self):
        """Verify no submit functions exist in report module."""
        import orchestration_layer.report as report_module
        
        # Get all public functions
        public_functions = [
            name for name in dir(report_module)
            if not name.startswith("_") and callable(getattr(report_module, name))
        ]
        
        # Forbidden function name patterns
        forbidden_patterns = [
            "submit", "send", "transmit", "post", "upload",
            "execute", "decide", "auto_", "bypass",
        ]
        
        for func_name in public_functions:
            for pattern in forbidden_patterns:
                assert pattern not in func_name.lower(), \
                    f"Forbidden function pattern '{pattern}' found in: {func_name}"
