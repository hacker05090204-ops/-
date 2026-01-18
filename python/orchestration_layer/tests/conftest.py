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
Phase-12 Test Configuration and Shared Fixtures

This module provides pytest configuration and shared fixtures for
all Phase-12 tests. No implementation logic - fixtures only.
"""

import pytest
from pathlib import Path


# =============================================================================
# TEST MARKERS
# =============================================================================

def pytest_configure(config):
    """Register custom markers for Phase-12 tests."""
    config.addinivalue_line("markers", "critical: Critical tests that must pass first")
    config.addinivalue_line("markers", "invariant: Tests that verify invariants hold")
    config.addinivalue_line("markers", "property: Property-based tests using Hypothesis")
    config.addinivalue_line("markers", "static: Static analysis tests using AST")
    config.addinivalue_line("markers", "boundary: Phase boundary enforcement tests")
    config.addinivalue_line("markers", "track1: Track 1 (Types and Errors) tests")
    config.addinivalue_line("markers", "track2: Track 2 (Audit Layer) tests")
    config.addinivalue_line("markers", "track3: Track 3 (Workflow State) tests")
    config.addinivalue_line("markers", "track4: Track 4 (Cross-Phase Correlation) tests")
    config.addinivalue_line("markers", "track5: Track 5 (Integration Report) tests")
    config.addinivalue_line("markers", "track6: Track 6 (Orchestrator) tests")
    config.addinivalue_line("markers", "forbidden: Forbidden capability tests")


# =============================================================================
# PATH FIXTURES
# =============================================================================

@pytest.fixture
def orchestration_layer_path() -> Path:
    """Return the path to the orchestration_layer package."""
    # TODO: Implement when Track 1 begins
    return Path(__file__).parent.parent


@pytest.fixture
def orchestration_layer_source_files(orchestration_layer_path: Path) -> list:
    """Return list of all .py source files in orchestration_layer."""
    # TODO: Implement when Track 1 begins
    return []


# =============================================================================
# FORBIDDEN IMPORTS LIST
# =============================================================================

FORBIDDEN_IMPORTS = {
    # Network
    'httpx', 'requests', 'aiohttp', 'socket',
    'urllib.request', 'urllib3', 'http.client',
    # Browser
    'selenium', 'playwright', 'puppeteer',
    'pyppeteer', 'splinter', 'mechanize',
    # UI Automation
    'pyautogui', 'pynput', 'keyboard', 'mouse'
}


FORBIDDEN_METHODS = {
    # Execution
    'execute_browser_action', 'trigger_scan', 'run_action',
    'perform_execution', 'start_browser', 'navigate_to', 'click_element',
    # Decision
    'make_decision', 'infer_decision', 'suggest_action',
    'recommend_approval', 'decide_for_human',
    # Auto-approval
    'auto_approve', 'auto_submit', 'auto_confirm', 'auto_execute',
    'approve_without_human', 'confirm_without_human',
    # Policy enforcement
    'enforce_friction', 'wire_friction', 'execute_deliberation',
    'execute_challenge', 'execute_cooldown', 'configure_friction',
    'bypass_friction',
    # Background tasks
    'start_background_task', 'schedule_task', 'run_async_job',
    'spawn_worker', 'create_thread', 'start_process'
}


@pytest.fixture
def forbidden_imports() -> set:
    """Return set of forbidden import names."""
    return FORBIDDEN_IMPORTS


@pytest.fixture
def forbidden_methods() -> set:
    """Return set of forbidden method names."""
    return FORBIDDEN_METHODS


# =============================================================================
# GOVERNANCE HEADER FIXTURE
# =============================================================================

GOVERNANCE_HEADER = """# PHASE-12 GOVERNANCE COMPLIANCE
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
# human authority, governance friction, or audit invariants."""


@pytest.fixture
def governance_header() -> str:
    """Return the required governance header."""
    return GOVERNANCE_HEADER
