"""
Phase-5 HAR Analyzer Tests

Tests for HAR file analysis.
Validates:
- Property 8: Sensitive Data Detection
- Property 9: Header Misconfiguration Detection
- Property 10: Reflection Detection

All tests use synthetic HAR data (no real Phase-4 artifacts).
"""

import pytest
from hypothesis import given, strategies as st

from artifact_scanner.analyzers.har import HARAnalyzer
from artifact_scanner.loader import HARData, HAREntry
from artifact_scanner.types import SignalType


# =============================================================================
# Test Fixtures
# =============================================================================

def make_har_entry(
    url: str = "https://example.com/api",
    method: str = "GET",
    request_headers: dict = None,
    status: int = 200,
    response_headers: dict = None,
    response_content: str = "",
    mime_type: str = "text/html",
) -> HAREntry:
    """Helper to create HAR entry."""
    return HAREntry(
        request_url=url,
        request_method=method,
        request_headers=request_headers or {},
        response_status=status,
        response_headers=response_headers or {},
        response_content=response_content,
        response_mime_type=mime_type,
    )


def make_har_data(entries: list[HAREntry]) -> HARData:
    """Helper to create HARData."""
    return HARData(entries=entries)


# =============================================================================
# Property 8: Sensitive Data Detection
# =============================================================================

class TestSensitiveDataDetection:
    """Property 8: HAR responses with sensitive patterns produce SensitiveDataSignal."""
    
    def test_detects_api_key_in_response(self):
        """Detect API key pattern in response body."""
        entry = make_har_entry(
            response_content='{"api_key": "sk_live_1234567890abcdef1234567890"}',
        )
        analyzer = HARAnalyzer("test.har")
        
        signals = analyzer.detect_sensitive_data(entry)
        
        assert len(signals) >= 1
        assert any(s.signal_type == SignalType.SENSITIVE_DATA for s in signals)
        assert any("api_key" in s.evidence.get("pattern_type", "") for s in signals)
    
    def test_detects_bearer_token(self):
        """Detect Bearer token in response."""
        entry = make_har_entry(
            response_content='Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test',
        )
        analyzer = HARAnalyzer("test.har")
        
        signals = analyzer.detect_sensitive_data(entry)
        
        assert len(signals) >= 1
        assert any(s.signal_type == SignalType.SENSITIVE_DATA for s in signals)
    
    def test_detects_aws_key(self):
        """Detect AWS access key pattern."""
        entry = make_har_entry(
            response_content='aws_access_key_id = AKIAIOSFODNN7EXAMPLE',
        )
        analyzer = HARAnalyzer("test.har")
        
        signals = analyzer.detect_sensitive_data(entry)
        
        assert len(signals) >= 1
        assert any("aws_key" in s.evidence.get("pattern_type", "") for s in signals)
    
    def test_detects_jwt_token(self):
        """Detect JWT token pattern."""
        entry = make_har_entry(
            response_content='token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U',
        )
        analyzer = HARAnalyzer("test.har")
        
        signals = analyzer.detect_sensitive_data(entry)
        
        assert len(signals) >= 1
        assert any("jwt_token" in s.evidence.get("pattern_type", "") for s in signals)
    
    def test_detects_private_key(self):
        """Detect private key pattern."""
        entry = make_har_entry(
            response_content='-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBg...',
        )
        analyzer = HARAnalyzer("test.har")
        
        signals = analyzer.detect_sensitive_data(entry)
        
        assert len(signals) >= 1
        assert any("private_key" in s.evidence.get("pattern_type", "") for s in signals)
    
    def test_detects_sensitive_data_in_header(self):
        """Detect sensitive data in response headers."""
        entry = make_har_entry(
            response_headers={"X-Auth-Token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"},
        )
        analyzer = HARAnalyzer("test.har")
        
        signals = analyzer.detect_sensitive_data(entry)
        
        assert len(signals) >= 1
        assert any(s.evidence.get("header_name") == "X-Auth-Token" for s in signals)
    
    def test_no_false_positive_on_clean_response(self):
        """No signals for clean response without sensitive data."""
        entry = make_har_entry(
            response_content='{"status": "ok", "message": "Hello World"}',
        )
        analyzer = HARAnalyzer("test.har")
        
        signals = analyzer.detect_sensitive_data(entry)
        
        assert len(signals) == 0
    
    def test_empty_response_no_signals(self):
        """Empty response produces no signals."""
        entry = make_har_entry(response_content="")
        analyzer = HARAnalyzer("test.har")
        
        signals = analyzer.detect_sensitive_data(entry)
        
        assert len(signals) == 0


# =============================================================================
# Property 9: Header Misconfiguration Detection
# =============================================================================

class TestHeaderMisconfigDetection:
    """Property 9: Missing security headers produce HeaderMisconfigSignal."""
    
    def test_detects_missing_csp(self):
        """Detect missing Content-Security-Policy header."""
        entry = make_har_entry(
            response_headers={
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
            },
        )
        analyzer = HARAnalyzer("test.har")
        
        signals = analyzer.detect_header_misconfig(entry)
        
        assert any(
            s.signal_type == SignalType.HEADER_MISCONFIG and
            "CSP" in s.evidence.get("missing_header", "")
            for s in signals
        )
    
    def test_detects_missing_x_content_type_options(self):
        """Detect missing X-Content-Type-Options header."""
        entry = make_har_entry(
            response_headers={
                "Content-Security-Policy": "default-src 'self'",
            },
        )
        analyzer = HARAnalyzer("test.har")
        
        signals = analyzer.detect_header_misconfig(entry)
        
        assert any(
            "X-Content-Type-Options" in s.evidence.get("missing_header", "")
            for s in signals
        )
    
    def test_detects_cors_wildcard(self):
        """Detect CORS wildcard (*) configuration."""
        entry = make_har_entry(
            response_headers={
                "Access-Control-Allow-Origin": "*",
            },
        )
        analyzer = HARAnalyzer("test.har")
        
        signals = analyzer.detect_header_misconfig(entry)
        
        assert any(
            s.signal_type == SignalType.HEADER_MISCONFIG and
            "CORS" in s.description
            for s in signals
        )
    
    def test_detects_unsafe_inline_csp(self):
        """Detect CSP with unsafe-inline."""
        entry = make_har_entry(
            response_headers={
                "Content-Security-Policy": "default-src 'self'; script-src 'unsafe-inline'",
            },
        )
        analyzer = HARAnalyzer("test.har")
        
        signals = analyzer.detect_header_misconfig(entry)
        
        assert any(
            "unsafe-inline" in s.evidence.get("issue", "")
            for s in signals
        )
    
    def test_detects_unsafe_eval_csp(self):
        """Detect CSP with unsafe-eval."""
        entry = make_har_entry(
            response_headers={
                "Content-Security-Policy": "default-src 'self'; script-src 'unsafe-eval'",
            },
        )
        analyzer = HARAnalyzer("test.har")
        
        signals = analyzer.detect_header_misconfig(entry)
        
        assert any(
            "unsafe-eval" in s.evidence.get("issue", "")
            for s in signals
        )
    
    def test_no_signal_for_secure_headers(self):
        """No misconfiguration signals for properly secured response."""
        entry = make_har_entry(
            response_headers={
                "Content-Security-Policy": "default-src 'self'",
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "Strict-Transport-Security": "max-age=31536000",
                "X-XSS-Protection": "1; mode=block",
            },
        )
        analyzer = HARAnalyzer("test.har")
        
        signals = analyzer.detect_header_misconfig(entry)
        
        # Should have no missing header signals
        missing_header_signals = [
            s for s in signals
            if "missing_header" in s.evidence
        ]
        assert len(missing_header_signals) == 0


# =============================================================================
# Property 10: Reflection Detection
# =============================================================================

class TestReflectionDetection:
    """Property 10: User input reflected without encoding produces ReflectionSignal."""
    
    def test_detects_reflected_query_param(self):
        """Detect query parameter reflected in HTML response."""
        entry = make_har_entry(
            url="https://example.com/search?q=testinput123",
            response_content='<html><body>Results for: testinput123</body></html>',
            mime_type="text/html",
        )
        analyzer = HARAnalyzer("test.har")
        
        signal = analyzer.detect_reflection(entry)
        
        assert signal is not None
        assert signal.signal_type == SignalType.REFLECTION
        assert "q" in signal.evidence.get("input_name", "")
    
    def test_no_reflection_for_encoded_input(self):
        """No signal when input is properly encoded."""
        entry = make_har_entry(
            url="https://example.com/search?q=<script>alert(1)</script>",
            response_content='<html><body>Results for: &lt;script&gt;alert(1)&lt;/script&gt;</body></html>',
            mime_type="text/html",
        )
        analyzer = HARAnalyzer("test.har")
        
        signal = analyzer.detect_reflection(entry)
        
        # The raw input is not reflected, only encoded version
        assert signal is None
    
    def test_no_reflection_for_json_response(self):
        """No reflection signal for JSON responses (not HTML context)."""
        entry = make_har_entry(
            url="https://example.com/api?q=testvalue",
            response_content='{"query": "testvalue", "results": []}',
            mime_type="application/json",
        )
        analyzer = HARAnalyzer("test.har")
        
        signal = analyzer.detect_reflection(entry)
        
        # JSON is not HTML context
        assert signal is None
    
    def test_no_reflection_for_short_input(self):
        """No signal for very short inputs (likely false positives)."""
        entry = make_har_entry(
            url="https://example.com/search?q=ab",
            response_content='<html><body>ab is too short</body></html>',
            mime_type="text/html",
        )
        analyzer = HARAnalyzer("test.har")
        
        signal = analyzer.detect_reflection(entry)
        
        assert signal is None
    
    def test_no_reflection_for_empty_response(self):
        """No signal for empty response."""
        entry = make_har_entry(
            url="https://example.com/search?q=test",
            response_content="",
        )
        analyzer = HARAnalyzer("test.har")
        
        signal = analyzer.detect_reflection(entry)
        
        assert signal is None


# =============================================================================
# Full Analysis Tests
# =============================================================================

class TestFullAnalysis:
    """Tests for full HAR analysis pipeline."""
    
    def test_analyze_multiple_entries(self):
        """Analyze HAR with multiple entries."""
        har_data = make_har_data([
            make_har_entry(
                url="https://example.com/api/config",
                response_content='{"api_key": "sk_test_1234567890abcdef"}',
            ),
            make_har_entry(
                url="https://example.com/page",
                response_headers={"Access-Control-Allow-Origin": "*"},
            ),
        ])
        analyzer = HARAnalyzer("test.har")
        
        signals = analyzer.analyze(har_data)
        
        # Should have signals from both entries
        assert len(signals) >= 2
        signal_types = {s.signal_type for s in signals}
        assert SignalType.SENSITIVE_DATA in signal_types
        assert SignalType.HEADER_MISCONFIG in signal_types
    
    def test_analyze_empty_har(self):
        """Analyze empty HAR produces no signals."""
        har_data = make_har_data([])
        analyzer = HARAnalyzer("test.har")
        
        signals = analyzer.analyze(har_data)
        
        assert len(signals) == 0
    
    def test_signals_include_source_artifact(self):
        """All signals include source artifact reference."""
        har_data = make_har_data([
            make_har_entry(
                response_content='{"api_key": "sk_test_1234567890abcdef"}',
            ),
        ])
        analyzer = HARAnalyzer("exec-1/network.har")
        
        signals = analyzer.analyze(har_data)
        
        for signal in signals:
            assert signal.source_artifact == "exec-1/network.har"
    
    def test_signals_include_endpoint(self):
        """Signals include endpoint URL."""
        har_data = make_har_data([
            make_har_entry(
                url="https://api.example.com/v1/users",
                response_content='{"api_key": "sk_test_1234567890abcdef"}',
            ),
        ])
        analyzer = HARAnalyzer("test.har")
        
        signals = analyzer.analyze(har_data)
        
        for signal in signals:
            assert signal.endpoint == "https://api.example.com/v1/users"
    
    def test_signals_have_none_forbidden_fields(self):
        """All signals have None for forbidden fields."""
        har_data = make_har_data([
            make_har_entry(
                response_content='{"api_key": "sk_test_1234567890abcdef"}',
                response_headers={"Access-Control-Allow-Origin": "*"},
            ),
        ])
        analyzer = HARAnalyzer("test.har")
        
        signals = analyzer.analyze(har_data)
        
        for signal in signals:
            assert signal.severity is None
            assert signal.classification is None
            assert signal.confidence is None
