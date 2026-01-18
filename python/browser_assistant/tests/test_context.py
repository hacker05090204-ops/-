"""
Phase-9 Context Analyzer Tests

Tests for context analysis and hint generation.
"""

import pytest
from datetime import datetime

from browser_assistant.context import ContextAnalyzer
from browser_assistant.types import (
    BrowserObservation,
    ObservationType,
    HintType,
    HintSeverity,
)


class TestContextAnalyzer:
    """Test context analyzer functionality."""
    
    def test_analyze_url_with_parameters(self, context_analyzer):
        """Verify URL parameters generate hints."""
        obs = BrowserObservation(
            observation_id="test-001",
            observation_type=ObservationType.URL_NAVIGATION,
            timestamp=datetime.now(),
            url="https://example.com/search?q=test&page=1",
            content="Search results",
            metadata=(),
        )
        
        hints = context_analyzer.analyze_observation(obs)
        
        # Should have parameter-related hint
        param_hints = [h for h in hints if "parameter" in h.title.lower()]
        assert len(param_hints) > 0
    
    def test_analyze_form_content(self, context_analyzer):
        """Verify form content generates hints."""
        obs = BrowserObservation(
            observation_id="test-001",
            observation_type=ObservationType.DOM_CONTENT,
            timestamp=datetime.now(),
            url="https://example.com/login",
            content='<form action="/login" method="POST"><input type="hidden" name="csrf"></form>',
            metadata=(),
        )
        
        hints = context_analyzer.analyze_observation(obs)
        
        # Should have form-related hints
        form_hints = [h for h in hints if "form" in h.title.lower()]
        assert len(form_hints) > 0
    
    def test_analyze_error_message(self, context_analyzer):
        """Verify error messages generate hints."""
        obs = BrowserObservation(
            observation_id="test-001",
            observation_type=ObservationType.ERROR_MESSAGE,
            timestamp=datetime.now(),
            url="https://example.com/api",
            content="Error: Invalid request. Exception occurred.",
            metadata=(),
        )
        
        hints = context_analyzer.analyze_observation(obs)
        
        # Should have error-related hint
        error_hints = [h for h in hints if "error" in h.title.lower()]
        assert len(error_hints) > 0
    
    def test_analyze_redirect_parameter(self, context_analyzer):
        """Verify redirect parameters generate hints."""
        obs = BrowserObservation(
            observation_id="test-001",
            observation_type=ObservationType.URL_NAVIGATION,
            timestamp=datetime.now(),
            url="https://example.com/login?redirect=https://evil.com",
            content="Login page",
            metadata=(),
        )
        
        hints = context_analyzer.analyze_observation(obs)
        
        # Should have redirect-related hint
        redirect_hints = [h for h in hints if "redirect" in h.title.lower()]
        assert len(redirect_hints) > 0
    
    def test_analyze_api_endpoint(self, context_analyzer):
        """Verify API endpoints generate hints."""
        obs = BrowserObservation(
            observation_id="test-001",
            observation_type=ObservationType.URL_NAVIGATION,
            timestamp=datetime.now(),
            url="https://example.com/api/v1/users",
            content="API response",
            metadata=(),
        )
        
        hints = context_analyzer.analyze_observation(obs)
        
        # Should have API-related hint
        api_hints = [h for h in hints if "api" in h.title.lower()]
        assert len(api_hints) > 0
    
    def test_analyze_auth_endpoint(self, context_analyzer):
        """Verify auth endpoints generate hints."""
        obs = BrowserObservation(
            observation_id="test-001",
            observation_type=ObservationType.URL_NAVIGATION,
            timestamp=datetime.now(),
            url="https://example.com/oauth/authorize",
            content="OAuth page",
            metadata=(),
        )
        
        hints = context_analyzer.analyze_observation(obs)
        
        # Should have auth-related hint
        auth_hints = [h for h in hints if "auth" in h.title.lower()]
        assert len(auth_hints) > 0
    
    def test_analyze_admin_path(self, context_analyzer):
        """Verify admin paths generate hints."""
        obs = BrowserObservation(
            observation_id="test-001",
            observation_type=ObservationType.URL_NAVIGATION,
            timestamp=datetime.now(),
            url="https://example.com/admin/dashboard",
            content="Admin dashboard",
            metadata=(),
        )
        
        hints = context_analyzer.analyze_observation(obs)
        
        # Should have admin-related hint
        admin_hints = [h for h in hints if "admin" in h.title.lower()]
        assert len(admin_hints) > 0
    
    def test_hints_are_advisory_only(self, context_analyzer):
        """Verify all hints are marked as advisory."""
        obs = BrowserObservation(
            observation_id="test-001",
            observation_type=ObservationType.URL_NAVIGATION,
            timestamp=datetime.now(),
            url="https://example.com/search?q=test",
            content="Search results",
            metadata=(),
        )
        
        hints = context_analyzer.analyze_observation(obs)
        
        for hint in hints:
            assert hint.human_confirmation_required is True
            assert hint.is_advisory_only is True
            assert hint.no_auto_action is True
    
    def test_hints_have_observation_reference(self, context_analyzer):
        """Verify hints reference the observation."""
        obs = BrowserObservation(
            observation_id="test-001",
            observation_type=ObservationType.URL_NAVIGATION,
            timestamp=datetime.now(),
            url="https://example.com/search?q=test",
            content="Search results",
            metadata=(),
        )
        
        hints = context_analyzer.analyze_observation(obs)
        
        for hint in hints:
            assert hint.related_observation_id == "test-001"
    
    def test_get_context_summary(self, context_analyzer, sample_observations):
        """Verify context summary generation."""
        summary = context_analyzer.get_context_summary(sample_observations)
        
        assert "Observed" in summary
        assert "events" in summary
        assert "URLs" in summary
    
    def test_get_context_summary_empty(self, context_analyzer):
        """Verify empty observation list handling."""
        summary = context_analyzer.get_context_summary([])
        
        assert "No observations" in summary


class TestContextAnalyzerNoForbiddenMethods:
    """Verify analyzer has no forbidden methods."""
    
    def test_no_classify_vulnerability(self, context_analyzer):
        """Verify classify_vulnerability method does not exist."""
        assert not hasattr(context_analyzer, "classify_vulnerability")
    
    def test_no_is_vulnerability(self, context_analyzer):
        """Verify is_vulnerability method does not exist."""
        assert not hasattr(context_analyzer, "is_vulnerability")
    
    def test_no_determine_severity(self, context_analyzer):
        """Verify determine_severity method does not exist."""
        assert not hasattr(context_analyzer, "determine_severity")
    
    def test_no_recommend_action(self, context_analyzer):
        """Verify recommend_action method does not exist."""
        assert not hasattr(context_analyzer, "recommend_action")
    
    def test_no_should_report(self, context_analyzer):
        """Verify should_report method does not exist."""
        assert not hasattr(context_analyzer, "should_report")
    
    def test_no_is_exploitable(self, context_analyzer):
        """Verify is_exploitable method does not exist."""
        assert not hasattr(context_analyzer, "is_exploitable")
    
    def test_no_calculate_risk(self, context_analyzer):
        """Verify calculate_risk method does not exist."""
        assert not hasattr(context_analyzer, "calculate_risk")
    
    def test_no_generate_poc(self, context_analyzer):
        """Verify generate_poc method does not exist."""
        assert not hasattr(context_analyzer, "generate_poc")
