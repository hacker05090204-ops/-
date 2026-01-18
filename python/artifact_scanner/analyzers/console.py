"""
Phase-5 Console Log Analyzer

Analyzes console logs for security signals.

INVARIANTS:
- No JavaScript executed
- No file modifications

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

import re
from typing import Optional

from artifact_scanner.loader import ConsoleLogEntry
from artifact_scanner.types import Signal, SignalType


# Patterns for path disclosure detection
PATH_PATTERNS = [
    re.compile(r'/home/[a-zA-Z0-9_-]+/'),
    re.compile(r'/Users/[a-zA-Z0-9_-]+/'),
    re.compile(r'C:\\Users\\[a-zA-Z0-9_-]+\\'),
    re.compile(r'/var/www/[a-zA-Z0-9_-]+/'),
    re.compile(r'/opt/[a-zA-Z0-9_-]+/'),
    re.compile(r'/etc/[a-zA-Z0-9_-]+'),
    re.compile(r'at\s+[a-zA-Z0-9_]+\s+\([^)]+:[0-9]+:[0-9]+\)'),  # Stack trace
]

# Patterns for DOM errors
DOM_ERROR_PATTERNS = [
    re.compile(r'(?i)cannot\s+read\s+propert(y|ies)\s+.*\s+of\s+(null|undefined)'),
    re.compile(r'(?i)is\s+not\s+a\s+function'),
    re.compile(r'(?i)is\s+not\s+defined'),
    re.compile(r'(?i)failed\s+to\s+execute'),
    re.compile(r'(?i)invalid\s+dom'),
    re.compile(r'(?i)element\s+not\s+found'),
    re.compile(r'(?i)null\s+is\s+not\s+an\s+object'),
]

# CSP violation patterns
CSP_VIOLATION_PATTERNS = [
    re.compile(r'(?i)refused\s+to\s+(load|execute|connect|frame)'),
    re.compile(r'(?i)violates\s+.*content\s+security\s+policy'),
    re.compile(r'(?i)blocked\s+by\s+content\s+security\s+policy'),
    re.compile(r'(?i)csp\s+violation'),
]


class ConsoleAnalyzer:
    """Analyzes console logs for security signals.
    
    INVARIANTS:
    - No JavaScript executed
    - No file modifications
    """
    
    def __init__(self, source_artifact: str) -> None:
        """Initialize analyzer with source artifact path."""
        self._source_artifact = source_artifact
    
    def analyze(self, logs: list[ConsoleLogEntry]) -> list[Signal]:
        """Extract signals from console logs.
        
        Args:
            logs: List of console log entries
        
        Returns:
            List of detected signals
        """
        signals: list[Signal] = []
        
        for log in logs:
            # Only analyze error and warning entries
            if log.level not in ("error", "warning"):
                continue
            
            # Detect path disclosure
            path_signal = self.detect_path_disclosure(log)
            if path_signal:
                signals.append(path_signal)
            
            # Detect DOM errors
            dom_signal = self.detect_dom_errors(log)
            if dom_signal:
                signals.append(dom_signal)
            
            # Detect CSP violations
            csp_signal = self.detect_csp_violations(log)
            if csp_signal:
                signals.append(csp_signal)
        
        return signals
    
    def detect_path_disclosure(self, log: ConsoleLogEntry) -> Optional[Signal]:
        """Detect sensitive paths in stack traces.
        
        Args:
            log: Console log entry
        
        Returns:
            PathDisclosureSignal if detected, None otherwise
        """
        for pattern in PATH_PATTERNS:
            match = pattern.search(log.message)
            if match:
                return Signal.create(
                    signal_type=SignalType.PATH_DISCLOSURE,
                    source_artifact=self._source_artifact,
                    description="Sensitive path disclosed in console log",
                    evidence={
                        "level": log.level,
                        "pattern_matched": match.group(0)[:50],  # Truncate for safety
                        "source": log.source,
                        "line_number": log.line_number,
                    },
                )
        
        return None
    
    def detect_dom_errors(self, log: ConsoleLogEntry) -> Optional[Signal]:
        """Detect DOM manipulation issues.
        
        Args:
            log: Console log entry
        
        Returns:
            DOMErrorSignal if detected, None otherwise
        """
        for pattern in DOM_ERROR_PATTERNS:
            if pattern.search(log.message):
                return Signal.create(
                    signal_type=SignalType.DOM_ERROR,
                    source_artifact=self._source_artifact,
                    description="DOM manipulation error detected",
                    evidence={
                        "level": log.level,
                        "message_preview": log.message[:200],  # Truncate
                        "source": log.source,
                        "line_number": log.line_number,
                    },
                )
        
        return None
    
    def detect_csp_violations(self, log: ConsoleLogEntry) -> Optional[Signal]:
        """Detect CSP violation reports.
        
        Args:
            log: Console log entry
        
        Returns:
            CSPViolationSignal if detected, None otherwise
        """
        for pattern in CSP_VIOLATION_PATTERNS:
            if pattern.search(log.message):
                return Signal.create(
                    signal_type=SignalType.CSP_VIOLATION,
                    source_artifact=self._source_artifact,
                    description="CSP violation detected in console",
                    evidence={
                        "level": log.level,
                        "message_preview": log.message[:200],  # Truncate
                        "source": log.source,
                    },
                )
        
        return None
