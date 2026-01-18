"""
Phase-5 Console Analyzer Tests

Tests for console log analysis.
All tests use synthetic data (no real Phase-4 artifacts).
"""

import pytest
from datetime import datetime, timezone

from artifact_scanner.analyzers.console import ConsoleAnalyzer
from artifact_scanner.loader import ConsoleLogEntry
from artifact_scanner.types import SignalType


# =============================================================================
# Test Fixtures
# =============================================================================

def make_log_entry(
    level: str = "error",
    message: str = "Test error",
    source: str = None,
    line_number: int = None,
) -> ConsoleLogEntry:
    """Helper to create console log entry."""
    return ConsoleLogEntry(
        level=level,
        message=message,
        timestamp=datetime.now(timezone.utc),
        source=source,
        line_number=line_number,
    )


# =============================================================================
# Path Disclosure Detection Tests
# =============================================================================

class TestPathDisclosureDetection:
    """Tests for path disclosure detection."""
    
    def test_detects_home_path(self):
        """Detect /home/user/ path in error."""
        log = make_log_entry(
            message="Error at /home/developer/app/src/index.js:42",
        )
        analyzer = ConsoleAnalyzer("console.json")
        
        signal = analyzer.detect_path_disclosure(log)
        
        assert signal is not None
        assert signal.signal_type == SignalType.PATH_DISCLOSURE
    
    def test_detects_users_path(self):
        """Detect /Users/user/ path (macOS)."""
        log = make_log_entry(
            message="Error at /Users/admin/project/app.js:10",
        )
        analyzer = ConsoleAnalyzer("console.json")
        
        signal = analyzer.detect_path_disclosure(log)
        
        assert signal is not None
        assert signal.signal_type == SignalType.PATH_DISCLOSURE
    
    def test_detects_windows_path(self):
        """Detect Windows user path."""
        log = make_log_entry(
            message="Error at C:\\Users\\developer\\project\\app.js:10",
        )
        analyzer = ConsoleAnalyzer("console.json")
        
        signal = analyzer.detect_path_disclosure(log)
        
        assert signal is not None
        assert signal.signal_type == SignalType.PATH_DISCLOSURE
    
    def test_detects_stack_trace(self):
        """Detect stack trace with file paths."""
        log = make_log_entry(
            message="at processRequest (server.js:42:15)",
        )
        analyzer = ConsoleAnalyzer("console.json")
        
        signal = analyzer.detect_path_disclosure(log)
        
        assert signal is not None
    
    def test_no_signal_for_clean_message(self):
        """No signal for message without paths."""
        log = make_log_entry(
            message="Connection refused",
        )
        analyzer = ConsoleAnalyzer("console.json")
        
        signal = analyzer.detect_path_disclosure(log)
        
        assert signal is None


# =============================================================================
# DOM Error Detection Tests
# =============================================================================

class TestDOMErrorDetection:
    """Tests for DOM error detection."""
    
    def test_detects_null_property_error(self):
        """Detect 'cannot read property of null' error."""
        log = make_log_entry(
            message="TypeError: Cannot read property 'value' of null",
        )
        analyzer = ConsoleAnalyzer("console.json")
        
        signal = analyzer.detect_dom_errors(log)
        
        assert signal is not None
        assert signal.signal_type == SignalType.DOM_ERROR
    
    def test_detects_undefined_property_error(self):
        """Detect 'cannot read property of undefined' error."""
        log = make_log_entry(
            message="TypeError: Cannot read property 'map' of undefined",
        )
        analyzer = ConsoleAnalyzer("console.json")
        
        signal = analyzer.detect_dom_errors(log)
        
        assert signal is not None
    
    def test_detects_not_a_function_error(self):
        """Detect 'is not a function' error."""
        log = make_log_entry(
            message="TypeError: element.click is not a function",
        )
        analyzer = ConsoleAnalyzer("console.json")
        
        signal = analyzer.detect_dom_errors(log)
        
        assert signal is not None
    
    def test_detects_not_defined_error(self):
        """Detect 'is not defined' error."""
        log = make_log_entry(
            message="ReferenceError: myVariable is not defined",
        )
        analyzer = ConsoleAnalyzer("console.json")
        
        signal = analyzer.detect_dom_errors(log)
        
        assert signal is not None
    
    def test_no_signal_for_non_dom_error(self):
        """No signal for non-DOM error."""
        log = make_log_entry(
            message="Network request failed",
        )
        analyzer = ConsoleAnalyzer("console.json")
        
        signal = analyzer.detect_dom_errors(log)
        
        assert signal is None


# =============================================================================
# CSP Violation Detection Tests
# =============================================================================

class TestCSPViolationDetection:
    """Tests for CSP violation detection."""
    
    def test_detects_refused_to_load(self):
        """Detect 'refused to load' CSP violation."""
        log = make_log_entry(
            message="Refused to load the script 'https://evil.com/script.js' because it violates the following Content Security Policy directive",
        )
        analyzer = ConsoleAnalyzer("console.json")
        
        signal = analyzer.detect_csp_violations(log)
        
        assert signal is not None
        assert signal.signal_type == SignalType.CSP_VIOLATION
    
    def test_detects_refused_to_execute(self):
        """Detect 'refused to execute' CSP violation."""
        log = make_log_entry(
            message="Refused to execute inline script because it violates the following Content Security Policy directive",
        )
        analyzer = ConsoleAnalyzer("console.json")
        
        signal = analyzer.detect_csp_violations(log)
        
        assert signal is not None
    
    def test_detects_blocked_by_csp(self):
        """Detect 'blocked by content security policy' message."""
        log = make_log_entry(
            message="The resource was blocked by Content Security Policy",
        )
        analyzer = ConsoleAnalyzer("console.json")
        
        signal = analyzer.detect_csp_violations(log)
        
        assert signal is not None
    
    def test_no_signal_for_non_csp_message(self):
        """No signal for non-CSP message."""
        log = make_log_entry(
            message="Script loaded successfully",
        )
        analyzer = ConsoleAnalyzer("console.json")
        
        signal = analyzer.detect_csp_violations(log)
        
        assert signal is None


# =============================================================================
# Full Analysis Tests
# =============================================================================

class TestFullAnalysis:
    """Tests for full console log analysis."""
    
    def test_analyze_multiple_logs(self):
        """Analyze multiple log entries."""
        logs = [
            make_log_entry(level="error", message="Error at /home/user/app.js:10"),
            make_log_entry(level="warning", message="Cannot read property 'x' of null"),
            make_log_entry(level="log", message="Info message"),  # Should be skipped
        ]
        analyzer = ConsoleAnalyzer("console.json")
        
        signals = analyzer.analyze(logs)
        
        # Should have signals from error and warning, not log
        assert len(signals) >= 2
    
    def test_skips_info_and_log_levels(self):
        """Only analyze error and warning levels."""
        logs = [
            make_log_entry(level="log", message="Error at /home/user/app.js:10"),
            make_log_entry(level="info", message="Cannot read property 'x' of null"),
        ]
        analyzer = ConsoleAnalyzer("console.json")
        
        signals = analyzer.analyze(logs)
        
        assert len(signals) == 0
    
    def test_signals_include_source_artifact(self):
        """All signals include source artifact reference."""
        logs = [
            make_log_entry(level="error", message="Error at /home/user/app.js:10"),
        ]
        analyzer = ConsoleAnalyzer("exec-1/console.json")
        
        signals = analyzer.analyze(logs)
        
        for signal in signals:
            assert signal.source_artifact == "exec-1/console.json"
    
    def test_signals_have_none_forbidden_fields(self):
        """All signals have None for forbidden fields."""
        logs = [
            make_log_entry(level="error", message="Error at /home/user/app.js:10"),
        ]
        analyzer = ConsoleAnalyzer("console.json")
        
        signals = analyzer.analyze(logs)
        
        for signal in signals:
            assert signal.severity is None
            assert signal.classification is None
            assert signal.confidence is None
