"""
Test: No URL Analysis (RISK-B)

GOVERNANCE: URLs are passed through verbatim.
No validation, no parsing, no classification, no reputation checks.
"""

import pytest
import ast
from pathlib import Path

from ..types import URLOpenRequest


class TestNoURLAnalysis:
    """Verify no URL analysis exists."""

    def test_url_passed_verbatim(self):
        """URL MUST be passed through without modification."""
        test_urls = [
            "https://example.com",
            "http://test.local:8080/path?query=value",
            "https://bugcrowd.com/submit",
            "https://hackerone.com/reports/new",
            "ftp://files.example.com",  # Even non-http URLs
            "invalid-url-format",  # Even invalid URLs
        ]
        
        for url in test_urls:
            request = URLOpenRequest(url=url, human_confirmed=True)
            assert request.url == url, f"URL was modified: {url} -> {request.url}"

    def test_no_url_validation(self):
        """No URL validation logic exists."""
        phase19_dir = Path(__file__).parent.parent
        
        forbidden_patterns = [
            "urlparse",
            "urlsplit",
            "validate_url",
            "is_valid_url",
            "check_url",
            "verify_url",
            "url_validator",
            "urllib.parse",
        ]
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text()
            
            for pattern in forbidden_patterns:
                assert pattern not in content, \
                    f"Forbidden URL pattern '{pattern}' in {py_file.name}"

    def test_no_url_classification(self):
        """No URL classification or categorization."""
        phase19_dir = Path(__file__).parent.parent
        
        forbidden_patterns = [
            "classify_url",
            "categorize_url",
            "url_type",
            "platform_type",
            "detect_platform",
            "identify_platform",
        ]
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text()
            
            for pattern in forbidden_patterns:
                assert pattern not in content, \
                    f"Forbidden classification pattern '{pattern}' in {py_file.name}"

    def test_no_url_reputation_checks(self):
        """No URL safety or trust checks."""
        phase19_dir = Path(__file__).parent.parent
        
        forbidden_patterns = [
            "safe_browsing",
            "malware",
            "phishing",
            "blocklist",
        ]
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text()
            tree = ast.parse(content)
            
            # Check function and variable names
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    name_lower = node.name.lower()
                    for pattern in forbidden_patterns:
                        assert pattern not in name_lower, \
                            f"Forbidden function '{node.name}' in {py_file.name}"
                elif isinstance(node, ast.Name):
                    name_lower = node.id.lower()
                    for pattern in forbidden_patterns:
                        assert pattern not in name_lower, \
                            f"Forbidden variable '{node.id}' in {py_file.name}"


class TestNoPlatformSelection:
    """Verify no platform selection logic exists."""

    def test_no_platform_list(self):
        """No list of platforms exists."""
        phase19_dir = Path(__file__).parent.parent
        
        forbidden_patterns = [
            "platforms = [",
            "PLATFORMS = [",
            "platform_list",
            "supported_platforms",
            "bugcrowd",
            "hackerone",
            "synack",
            "intigriti",
        ]
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text()
            
            for pattern in forbidden_patterns:
                assert pattern.lower() not in content.lower(), \
                    f"Forbidden platform pattern '{pattern}' in {py_file.name}"

    def test_no_platform_detection(self):
        """No platform detection from URL."""
        phase19_dir = Path(__file__).parent.parent
        
        forbidden_patterns = [
            "detect_platform",
            "identify_platform",
            "get_platform",
            "platform_from_url",
            "extract_platform",
        ]
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text()
            
            for pattern in forbidden_patterns:
                assert pattern not in content, \
                    f"Forbidden detection pattern '{pattern}' in {py_file.name}"

    def test_no_platform_suggestions(self):
        """No platform suggestions or recommendations."""
        phase19_dir = Path(__file__).parent.parent
        
        forbidden_patterns = [
            "suggest_platform",
            "recommend_platform",
            "best_platform",
            "preferred_platform",
        ]
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text()
            
            for pattern in forbidden_patterns:
                assert pattern not in content, \
                    f"Forbidden suggestion pattern '{pattern}' in {py_file.name}"
