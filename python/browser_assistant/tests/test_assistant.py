"""
Phase-9 Browser Assistant Tests

Tests for main assistant orchestrator.
"""

import pytest
from datetime import datetime

from browser_assistant.assistant import BrowserAssistant
from browser_assistant.types import ObservationType, ConfirmationStatus


class TestBrowserAssistant:
    """Test browser assistant functionality."""
    
    def test_initialization(self, browser_assistant):
        """Verify assistant initializes correctly."""
        assert browser_assistant is not None
    
    def test_receive_observation(self, browser_assistant):
        """Verify observations can be received."""
        output = browser_assistant.receive_observation(
            observation_type=ObservationType.URL_NAVIGATION,
            url="https://app.example.com/search?q=test",
            content="Search results page",
        )
        
        assert output.output_id is not None
        assert output.output_type == "observation_hints"
        assert output.confirmation_status == ConfirmationStatus.PENDING
    
    def test_observation_output_requires_confirmation(self, browser_assistant):
        """Verify observation output requires confirmation."""
        output = browser_assistant.receive_observation(
            observation_type=ObservationType.URL_NAVIGATION,
            url="https://app.example.com/page",
            content="Page content",
        )
        
        assert output.requires_human_confirmation is True
        assert output.no_auto_action is True
    
    def test_observation_generates_hints(self, browser_assistant):
        """Verify observation generates hints."""
        output = browser_assistant.receive_observation(
            observation_type=ObservationType.URL_NAVIGATION,
            url="https://app.example.com/search?q=test",
            content="Search results",
        )
        
        content = output.content
        assert "observation" in content
        assert "context_hints" in content
        assert "scope_warning" in content
    
    def test_generate_draft_report(self, browser_assistant):
        """Verify draft reports can be generated."""
        # First add some observations
        browser_assistant.receive_observation(
            observation_type=ObservationType.URL_NAVIGATION,
            url="https://app.example.com/page",
            content="Page content",
        )
        
        output = browser_assistant.generate_draft_report()
        
        assert output.output_id is not None
        assert output.output_type == "draft_report"
        assert output.confirmation_status == ConfirmationStatus.PENDING
    
    def test_draft_requires_confirmation(self, browser_assistant):
        """Verify draft requires confirmation."""
        browser_assistant.receive_observation(
            observation_type=ObservationType.URL_NAVIGATION,
            url="https://app.example.com/page",
            content="Page content",
        )
        
        output = browser_assistant.generate_draft_report()
        
        assert output.requires_human_confirmation is True
    
    def test_confirm_output_approved(self, browser_assistant):
        """Verify output can be confirmed with YES."""
        output = browser_assistant.receive_observation(
            observation_type=ObservationType.URL_NAVIGATION,
            url="https://app.example.com/page",
            content="Page content",
        )
        
        confirmation = browser_assistant.confirm_output(
            output_id=output.output_id,
            confirmed_by="user-001",
            approved=True,
        )
        
        assert confirmation.status == ConfirmationStatus.CONFIRMED
    
    def test_confirm_output_rejected(self, browser_assistant):
        """Verify output can be confirmed with NO."""
        output = browser_assistant.receive_observation(
            observation_type=ObservationType.URL_NAVIGATION,
            url="https://app.example.com/page",
            content="Page content",
        )
        
        confirmation = browser_assistant.confirm_output(
            output_id=output.output_id,
            confirmed_by="user-001",
            approved=False,
        )
        
        assert confirmation.status == ConfirmationStatus.REJECTED
    
    def test_get_pending_confirmations(self, browser_assistant):
        """Verify pending confirmations can be retrieved."""
        for i in range(3):
            browser_assistant.receive_observation(
                observation_type=ObservationType.URL_NAVIGATION,
                url=f"https://app.example.com/page{i}",
                content=f"Content {i}",
            )
        
        pending = browser_assistant.get_pending_confirmations()
        assert len(pending) == 3
    
    def test_get_recent_observations(self, browser_assistant):
        """Verify recent observations can be retrieved."""
        for i in range(5):
            browser_assistant.receive_observation(
                observation_type=ObservationType.URL_NAVIGATION,
                url=f"https://app.example.com/page{i}",
                content=f"Content {i}",
            )
        
        observations = browser_assistant.get_recent_observations(limit=3)
        assert len(observations) == 3
    
    def test_get_scope_summary(self, browser_assistant):
        """Verify scope summary can be retrieved."""
        summary = browser_assistant.get_scope_summary()
        
        assert "example.com" in summary
    
    def test_get_context_summary(self, browser_assistant):
        """Verify context summary can be retrieved."""
        browser_assistant.receive_observation(
            observation_type=ObservationType.URL_NAVIGATION,
            url="https://app.example.com/page",
            content="Page content",
        )
        
        summary = browser_assistant.get_context_summary()
        
        assert "Observed" in summary
    
    def test_register_finding_for_duplicate_check(self, browser_assistant):
        """Verify findings can be registered for duplicate checking."""
        fid = browser_assistant.register_finding_for_duplicate_check(
            url="https://app.example.com/vuln",
            content="XSS vulnerability",
        )
        
        assert fid is not None
    
    def test_add_authorized_domain(self, browser_assistant):
        """Verify domains can be added to scope."""
        browser_assistant.add_authorized_domain("newdomain.com")
        
        output = browser_assistant.receive_observation(
            observation_type=ObservationType.URL_NAVIGATION,
            url="https://newdomain.com/page",
            content="Page content",
        )
        
        scope_warning = output.content["scope_warning"]
        assert scope_warning.scope_status == "in_scope"
    
    def test_add_excluded_path(self, browser_assistant):
        """Verify paths can be added to exclusions."""
        browser_assistant.add_excluded_path("/secret/*")
        
        output = browser_assistant.receive_observation(
            observation_type=ObservationType.URL_NAVIGATION,
            url="https://app.example.com/secret/data",
            content="Secret data",
        )
        
        scope_warning = output.content["scope_warning"]
        assert scope_warning.scope_status == "excluded"
    
    def test_get_drafts(self, browser_assistant):
        """Verify drafts can be retrieved."""
        browser_assistant.receive_observation(
            observation_type=ObservationType.URL_NAVIGATION,
            url="https://app.example.com/page",
            content="Page content",
        )
        
        browser_assistant.generate_draft_report()
        browser_assistant.generate_draft_report()
        
        drafts = browser_assistant.get_drafts()
        assert len(drafts) == 2
    
    def test_clear_session(self, browser_assistant):
        """Verify session can be cleared."""
        for i in range(3):
            browser_assistant.receive_observation(
                observation_type=ObservationType.URL_NAVIGATION,
                url=f"https://app.example.com/page{i}",
                content=f"Content {i}",
            )
        
        browser_assistant.generate_draft_report()
        
        result = browser_assistant.clear_session()
        
        assert result["observations_cleared"] == 3
        assert result["drafts_cleared"] == 1
        
        assert len(browser_assistant.get_recent_observations()) == 0
        assert len(browser_assistant.get_drafts()) == 0


class TestBrowserAssistantNoForbiddenMethods:
    """Verify assistant has no forbidden methods."""
    
    def test_no_execute_payload(self, browser_assistant):
        """Verify execute_payload method does not exist."""
        assert not hasattr(browser_assistant, "execute_payload")
    
    def test_no_inject_traffic(self, browser_assistant):
        """Verify inject_traffic method does not exist."""
        assert not hasattr(browser_assistant, "inject_traffic")
    
    def test_no_modify_request(self, browser_assistant):
        """Verify modify_request method does not exist."""
        assert not hasattr(browser_assistant, "modify_request")
    
    def test_no_classify_bug(self, browser_assistant):
        """Verify classify_bug method does not exist."""
        assert not hasattr(browser_assistant, "classify_bug")
    
    def test_no_assign_severity(self, browser_assistant):
        """Verify assign_severity method does not exist."""
        assert not hasattr(browser_assistant, "assign_severity")
    
    def test_no_submit_report(self, browser_assistant):
        """Verify submit_report method does not exist."""
        assert not hasattr(browser_assistant, "submit_report")
    
    def test_no_auto_confirm(self, browser_assistant):
        """Verify auto_confirm method does not exist."""
        assert not hasattr(browser_assistant, "auto_confirm")
    
    def test_no_bypass_human(self, browser_assistant):
        """Verify bypass_human method does not exist."""
        assert not hasattr(browser_assistant, "bypass_human")
    
    def test_no_generate_poc(self, browser_assistant):
        """Verify generate_poc method does not exist."""
        assert not hasattr(browser_assistant, "generate_poc")
    
    def test_no_record_video(self, browser_assistant):
        """Verify record_video method does not exist."""
        assert not hasattr(browser_assistant, "record_video")
    
    def test_no_chain_findings(self, browser_assistant):
        """Verify chain_findings method does not exist."""
        assert not hasattr(browser_assistant, "chain_findings")
    
    def test_no_send_to_platform(self, browser_assistant):
        """Verify send_to_platform method does not exist."""
        assert not hasattr(browser_assistant, "send_to_platform")
    
    def test_no_execute_script(self, browser_assistant):
        """Verify execute_script method does not exist."""
        assert not hasattr(browser_assistant, "execute_script")
    
    def test_no_navigate_browser(self, browser_assistant):
        """Verify navigate_browser method does not exist."""
        assert not hasattr(browser_assistant, "navigate_browser")
