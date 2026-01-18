"""
Phase-9 Test Fixtures

Shared fixtures for browser assistant tests.
"""

import pytest
from datetime import datetime

from browser_assistant.types import (
    BrowserObservation,
    ObservationType,
    ContextHint,
    HintType,
    HintSeverity,
    DuplicateHint,
    ScopeWarning,
    DraftReportContent,
    HumanConfirmation,
    ConfirmationStatus,
    AssistantOutput,
)
from browser_assistant.observer import BrowserObserver
from browser_assistant.context import ContextAnalyzer
from browser_assistant.duplicate_hint import DuplicateHintEngine
from browser_assistant.scope_check import ScopeChecker
from browser_assistant.draft_generator import DraftReportGenerator
from browser_assistant.confirmation import HumanConfirmationGate
from browser_assistant.assistant import BrowserAssistant


@pytest.fixture
def browser_observer():
    """Create a fresh browser observer."""
    return BrowserObserver()


@pytest.fixture
def context_analyzer():
    """Create a fresh context analyzer."""
    return ContextAnalyzer()


@pytest.fixture
def duplicate_engine():
    """Create a fresh duplicate hint engine."""
    return DuplicateHintEngine(similarity_threshold=0.7)


@pytest.fixture
def scope_checker():
    """Create a scope checker with test domains."""
    return ScopeChecker(
        authorized_domains=["*.example.com", "test.local"],
        authorized_ip_ranges=["10.0.0.0/8", "192.168.1.0/24"],
        excluded_paths=["/admin/*", "/internal/*"],
    )


@pytest.fixture
def draft_generator():
    """Create a fresh draft generator."""
    return DraftReportGenerator()


@pytest.fixture
def confirmation_gate():
    """Create a fresh confirmation gate."""
    return HumanConfirmationGate()


@pytest.fixture
def browser_assistant():
    """Create a fully configured browser assistant."""
    return BrowserAssistant(
        authorized_domains=["*.example.com", "test.local"],
        authorized_ip_ranges=["10.0.0.0/8"],
        excluded_paths=["/admin/*"],
        duplicate_threshold=0.7,
    )


@pytest.fixture
def sample_observation():
    """Create a sample browser observation."""
    return BrowserObservation(
        observation_id="obs-001",
        observation_type=ObservationType.URL_NAVIGATION,
        timestamp=datetime.now(),
        url="https://app.example.com/search?q=test",
        content="Search results page",
        metadata=(("referrer", "https://example.com"),),
        is_passive_observation=True,
        no_modification_performed=True,
    )


@pytest.fixture
def sample_observations():
    """Create multiple sample observations."""
    return [
        BrowserObservation(
            observation_id=f"obs-{i:03d}",
            observation_type=ObservationType.URL_NAVIGATION,
            timestamp=datetime.now(),
            url=f"https://app.example.com/page{i}?id={i}",
            content=f"Page {i} content",
            metadata=(),
            is_passive_observation=True,
            no_modification_performed=True,
        )
        for i in range(5)
    ]
