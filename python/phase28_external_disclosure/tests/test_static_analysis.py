"""
Phase-28 Static Analysis Tests

NO AUTHORITY / PRESENTATION ONLY

Tests that verify Phase-28 code does NOT contain forbidden patterns.
These tests scan source code for prohibited imports and patterns.
"""

import pytest
import ast
import os
from pathlib import Path


def get_phase28_source_files():
    """Get all Python source files in phase28_external_disclosure."""
    phase28_dir = Path(__file__).parent.parent
    source_files = []
    for py_file in phase28_dir.glob("*.py"):
        if py_file.name != "__pycache__":
            source_files.append(py_file)
    return source_files


def read_source(filepath: Path) -> str:
    """Read source code from file."""
    return filepath.read_text()


class TestNoNetworkImports:
    """Tests that no network libraries are imported."""

    def test_no_requests_import(self):
        """Phase-28 MUST NOT import requests."""
        for source_file in get_phase28_source_files():
            source = read_source(source_file)
            assert "import requests" not in source, f"Found 'import requests' in {source_file}"
            assert "from requests" not in source, f"Found 'from requests' in {source_file}"

    def test_no_urllib_import(self):
        """Phase-28 MUST NOT import urllib for network access."""
        for source_file in get_phase28_source_files():
            source = read_source(source_file)
            # urllib.request is for network, urllib.parse is OK
            assert "urllib.request" not in source, f"Found 'urllib.request' in {source_file}"
            assert "from urllib import request" not in source, f"Found urllib request import in {source_file}"

    def test_no_httpx_import(self):
        """Phase-28 MUST NOT import httpx."""
        for source_file in get_phase28_source_files():
            source = read_source(source_file)
            assert "import httpx" not in source, f"Found 'import httpx' in {source_file}"
            assert "from httpx" not in source, f"Found 'from httpx' in {source_file}"

    def test_no_socket_import(self):
        """Phase-28 MUST NOT import socket."""
        for source_file in get_phase28_source_files():
            source = read_source(source_file)
            assert "import socket" not in source, f"Found 'import socket' in {source_file}"
            assert "from socket" not in source, f"Found 'from socket' in {source_file}"

    def test_no_aiohttp_import(self):
        """Phase-28 MUST NOT import aiohttp."""
        for source_file in get_phase28_source_files():
            source = read_source(source_file)
            assert "import aiohttp" not in source, f"Found 'import aiohttp' in {source_file}"
            assert "from aiohttp" not in source, f"Found 'from aiohttp' in {source_file}"


class TestNoPlatformDetection:
    """Tests that no platform detection patterns exist."""

    def test_no_platform_detection(self):
        """Phase-28 MUST NOT detect platforms."""
        forbidden_patterns = [
            "detect_platform",
            "platform_detection",
            "hackerone",
            "bugcrowd",
            "synack",
            "intigriti",
        ]
        
        for source_file in get_phase28_source_files():
            source = read_source(source_file).lower()
            for pattern in forbidden_patterns:
                assert pattern not in source, f"Found '{pattern}' in {source_file}"


class TestNoAutoSharePatterns:
    """Tests that no auto-share patterns exist."""

    def test_no_auto_share_patterns(self):
        """Phase-28 MUST NOT auto-share."""
        forbidden_patterns = [
            "auto_share",
            "auto_submit",
            "submit_to_platform",
            "send_to_",
            "post_to_",
            "upload_to_",
        ]
        
        for source_file in get_phase28_source_files():
            source = read_source(source_file).lower()
            for pattern in forbidden_patterns:
                assert pattern not in source, f"Found '{pattern}' in {source_file}"


class TestNoBackgroundTaskPatterns:
    """Tests that no background task patterns exist."""

    def test_no_background_task_patterns(self):
        """Phase-28 MUST NOT run background tasks."""
        forbidden_patterns = [
            "threading.Thread",
            "multiprocessing.Process",
            "schedule.every",
            "celery",
            "background_task",
            "daemon=True",
        ]
        
        for source_file in get_phase28_source_files():
            source = read_source(source_file)
            for pattern in forbidden_patterns:
                assert pattern not in source, f"Found '{pattern}' in {source_file}"


class TestNoScoringPatterns:
    """Tests that no scoring patterns exist."""

    def test_no_scoring_patterns(self):
        """Phase-28 MUST NOT score or rank."""
        forbidden_patterns = [
            "def score",
            "def rank",
            "def prioritize",
            "def classify",
            "severity_score",
            "risk_score",
            "priority_score",
        ]
        
        for source_file in get_phase28_source_files():
            source = read_source(source_file).lower()
            for pattern in forbidden_patterns:
                assert pattern not in source, f"Found '{pattern}' in {source_file}"


class TestNoRecommendationPatterns:
    """Tests that no recommendation patterns exist."""

    def test_no_recommendation_patterns(self):
        """Phase-28 MUST NOT recommend."""
        forbidden_patterns = [
            "def recommend",
            "def suggest",
            "recommendation",
            "suggested_action",
        ]
        
        for source_file in get_phase28_source_files():
            source = read_source(source_file).lower()
            for pattern in forbidden_patterns:
                # Allow "NO recommendation" in disclaimers
                if "no " + pattern.replace("def ", "") not in source:
                    assert pattern not in source, f"Found '{pattern}' in {source_file}"


class TestNoInterpretationPatterns:
    """Tests that no interpretation patterns exist."""

    def test_no_interpretation_patterns(self):
        """Phase-28 MUST NOT interpret or analyze."""
        forbidden_patterns = [
            "def analyze",
            "def interpret",
            "def judge",
            "def evaluate",
            "analysis_result",
            "interpretation_result",
        ]
        
        for source_file in get_phase28_source_files():
            source = read_source(source_file).lower()
            for pattern in forbidden_patterns:
                assert pattern not in source, f"Found '{pattern}' in {source_file}"


class TestDisclaimerPresence:
    """Tests that disclaimers are present in all modules."""

    def test_disclaimer_in_all_modules(self):
        """All modules MUST contain disclaimer."""
        for source_file in get_phase28_source_files():
            if source_file.name == "__init__.py" or source_file.name.endswith(".py"):
                source = read_source(source_file)
                assert "NO AUTHORITY" in source or "PRESENTATION ONLY" in source, \
                    f"Missing disclaimer in {source_file}"
