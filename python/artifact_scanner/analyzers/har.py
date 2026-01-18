"""
Phase-5 HAR Analyzer

Analyzes HAR files for security signals.

INVARIANTS:
- No network requests made
- HAR file not modified
- No JavaScript execution

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

import re
from typing import Optional

from artifact_scanner.loader import HARData, HAREntry
from artifact_scanner.types import Signal, SignalType


# Patterns for sensitive data detection
SENSITIVE_PATTERNS = {
    "api_key": re.compile(
        r'(?i)(api[_-]?key|apikey)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{16,})',
        re.IGNORECASE,
    ),
    "bearer_token": re.compile(
        r'(?i)bearer\s+([a-zA-Z0-9_\-\.]+)',
        re.IGNORECASE,
    ),
    "aws_key": re.compile(
        r'(?:AKIA|ABIA|ACCA|ASIA)[A-Z0-9]{16}',
    ),
    "private_key": re.compile(
        r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----',
    ),
    "password_field": re.compile(
        r'(?i)(password|passwd|pwd)["\']?\s*[:=]\s*["\']?([^"\'&\s]{4,})',
    ),
    "jwt_token": re.compile(
        r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*',
    ),
    "basic_auth": re.compile(
        r'(?i)basic\s+([a-zA-Z0-9+/=]{10,})',
    ),
}

# Security headers to check
SECURITY_HEADERS = {
    "content-security-policy": "CSP",
    "x-content-type-options": "X-Content-Type-Options",
    "x-frame-options": "X-Frame-Options",
    "strict-transport-security": "HSTS",
    "x-xss-protection": "X-XSS-Protection",
}

# CORS misconfiguration patterns
CORS_WILDCARD_PATTERN = re.compile(r'^\*$')


class HARAnalyzer:
    """Analyzes HAR files for security signals.
    
    INVARIANTS:
    - No network requests made
    - HAR file not modified
    - No JavaScript execution
    """
    
    def __init__(self, source_artifact: str) -> None:
        """Initialize analyzer with source artifact path."""
        self._source_artifact = source_artifact
    
    def analyze(self, har_data: HARData) -> list[Signal]:
        """Extract signals from HAR data.
        
        Args:
            har_data: Parsed HAR data
        
        Returns:
            List of detected signals
        """
        signals: list[Signal] = []
        
        for entry in har_data.entries:
            # Detect sensitive data in responses
            signals.extend(self.detect_sensitive_data(entry))
            
            # Detect header misconfigurations
            signals.extend(self.detect_header_misconfig(entry))
            
            # Detect reflection
            reflection_signal = self.detect_reflection(entry)
            if reflection_signal:
                signals.append(reflection_signal)
        
        return signals
    
    def detect_sensitive_data(self, entry: HAREntry) -> list[Signal]:
        """Detect API keys, tokens, credentials in responses.
        
        Args:
            entry: HAR entry to analyze
        
        Returns:
            List of SensitiveDataSignal instances
        """
        signals: list[Signal] = []
        content = entry.response_content
        
        # Check response body for sensitive data
        if content:
            for pattern_name, pattern in SENSITIVE_PATTERNS.items():
                matches = pattern.findall(content)
                if matches:
                    # Redact actual values for safety
                    signals.append(Signal.create(
                        signal_type=SignalType.SENSITIVE_DATA,
                        source_artifact=self._source_artifact,
                        description=f"Potential {pattern_name} detected in response",
                        evidence={
                            "pattern_type": pattern_name,
                            "match_count": len(matches),
                            "url": entry.request_url,
                            "status": entry.response_status,
                            # Don't include actual matches for security
                        },
                        endpoint=entry.request_url,
                    ))
        
        # Also check response headers for sensitive data
        for header_name, header_value in entry.response_headers.items():
            for pattern_name, pattern in SENSITIVE_PATTERNS.items():
                if pattern.search(header_value):
                    signals.append(Signal.create(
                        signal_type=SignalType.SENSITIVE_DATA,
                        source_artifact=self._source_artifact,
                        description=f"Potential {pattern_name} in response header: {header_name}",
                        evidence={
                            "pattern_type": pattern_name,
                            "header_name": header_name,
                            "url": entry.request_url,
                        },
                        endpoint=entry.request_url,
                    ))
        
        return signals
    
    def detect_header_misconfig(self, entry: HAREntry) -> list[Signal]:
        """Detect missing CSP, CORS wildcard, etc.
        
        Args:
            entry: HAR entry to analyze
        
        Returns:
            List of HeaderMisconfigSignal instances
        """
        signals: list[Signal] = []
        
        # Normalize header names to lowercase for comparison
        headers_lower = {k.lower(): v for k, v in entry.response_headers.items()}
        
        # Check for missing security headers
        for header_key, header_name in SECURITY_HEADERS.items():
            if header_key not in headers_lower:
                signals.append(Signal.create(
                    signal_type=SignalType.HEADER_MISCONFIG,
                    source_artifact=self._source_artifact,
                    description=f"Missing security header: {header_name}",
                    evidence={
                        "missing_header": header_name,
                        "url": entry.request_url,
                        "status": entry.response_status,
                    },
                    endpoint=entry.request_url,
                ))
        
        # Check for CORS wildcard
        cors_header = headers_lower.get("access-control-allow-origin", "")
        if CORS_WILDCARD_PATTERN.match(cors_header):
            signals.append(Signal.create(
                signal_type=SignalType.HEADER_MISCONFIG,
                source_artifact=self._source_artifact,
                description="CORS wildcard (*) allows any origin",
                evidence={
                    "header": "Access-Control-Allow-Origin",
                    "value": "*",
                    "url": entry.request_url,
                },
                endpoint=entry.request_url,
            ))
        
        # Check for permissive CSP
        csp = headers_lower.get("content-security-policy", "")
        if csp:
            if "unsafe-inline" in csp:
                signals.append(Signal.create(
                    signal_type=SignalType.HEADER_MISCONFIG,
                    source_artifact=self._source_artifact,
                    description="CSP allows unsafe-inline",
                    evidence={
                        "header": "Content-Security-Policy",
                        "issue": "unsafe-inline",
                        "url": entry.request_url,
                    },
                    endpoint=entry.request_url,
                ))
            if "unsafe-eval" in csp:
                signals.append(Signal.create(
                    signal_type=SignalType.HEADER_MISCONFIG,
                    source_artifact=self._source_artifact,
                    description="CSP allows unsafe-eval",
                    evidence={
                        "header": "Content-Security-Policy",
                        "issue": "unsafe-eval",
                        "url": entry.request_url,
                    },
                    endpoint=entry.request_url,
                ))
        
        return signals
    
    def detect_reflection(self, entry: HAREntry) -> Optional[Signal]:
        """Detect user input reflected without encoding.
        
        Args:
            entry: HAR entry to analyze
        
        Returns:
            ReflectionSignal if detected, None otherwise
        """
        # Extract potential user inputs from request
        user_inputs = self._extract_user_inputs(entry)
        
        if not user_inputs or not entry.response_content:
            return None
        
        # Check if any input is reflected in response
        for input_name, input_value in user_inputs.items():
            if len(input_value) < 3:  # Skip very short values
                continue
            
            # Check for unencoded reflection
            if input_value in entry.response_content:
                # Check if it's in HTML context (potential XSS)
                if self._is_html_context(entry.response_content, input_value):
                    return Signal.create(
                        signal_type=SignalType.REFLECTION,
                        source_artifact=self._source_artifact,
                        description=f"User input '{input_name}' reflected in HTML response without encoding",
                        evidence={
                            "input_name": input_name,
                            "input_length": len(input_value),
                            "url": entry.request_url,
                            "response_type": entry.response_mime_type,
                        },
                        endpoint=entry.request_url,
                    )
        
        return None
    
    def _extract_user_inputs(self, entry: HAREntry) -> dict[str, str]:
        """Extract potential user inputs from request.
        
        Args:
            entry: HAR entry
        
        Returns:
            Dict of input name -> value
        """
        inputs: dict[str, str] = {}
        
        # Extract from URL query parameters
        url = entry.request_url
        if "?" in url:
            query_string = url.split("?", 1)[1]
            for param in query_string.split("&"):
                if "=" in param:
                    name, value = param.split("=", 1)
                    inputs[name] = value
        
        return inputs
    
    def _is_html_context(self, content: str, value: str) -> bool:
        """Check if value appears in HTML context.
        
        Args:
            content: Response content
            value: Value to check
        
        Returns:
            True if value is in HTML context
        """
        # Simple heuristic: check if content looks like HTML
        # and value appears outside of script/style tags
        content_lower = content.lower()
        if "<html" in content_lower or "<!doctype" in content_lower:
            # Check if value appears in a potentially dangerous context
            idx = content.find(value)
            if idx >= 0:
                # Check surrounding context
                before = content[max(0, idx - 50):idx]
                if "<" in before and ">" not in before:
                    # Inside a tag - potential attribute injection
                    return True
                if not any(tag in before.lower() for tag in ["<script", "<style"]):
                    # Not inside script/style - potential HTML injection
                    return True
        
        return False
