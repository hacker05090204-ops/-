"""
Phase-8 Test Configuration

Provides fixtures and strategies for testing the Intelligence Layer.
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any
from hypothesis import settings, Phase

from intelligence_layer.data_access import DataAccessLayer
from intelligence_layer.duplicate import DuplicateDetector
from intelligence_layer.acceptance import AcceptanceTracker
from intelligence_layer.target import TargetProfiler
from intelligence_layer.performance import PerformanceAnalyzer
from intelligence_layer.patterns import PatternEngine


# Configure Hypothesis for Phase-8 tests
settings.register_profile(
    "phase8",
    max_examples=100,
    phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.shrink],
    deadline=None,
)
settings.load_profile("phase8")


# ============================================================================
# Sample Data Factories
# ============================================================================

def create_sample_decision(
    decision_id: str = "dec-001",
    finding_id: str = "find-001",
    reviewer_id: str = "reviewer-001",
    decision_type: str = "approve",
    severity: str = "high",
    timestamp: datetime = None,
    target_id: str = "target-001",
    content: str = "Sample finding content",
    vulnerability_type: str = "xss",
) -> Dict[str, Any]:
    """Create a sample decision dictionary."""
    return {
        "decision_id": decision_id,
        "finding_id": finding_id,
        "reviewer_id": reviewer_id,
        "decision_type": decision_type,
        "severity": severity,
        "timestamp": timestamp or datetime.now(),
        "target_id": target_id,
        "content": content,
        "vulnerability_type": vulnerability_type,
    }


def create_sample_submission(
    submission_id: str = "sub-001",
    decision_id: str = "dec-001",
    platform: str = "hackerone",
    status: str = "acknowledged",
    submitted_at: datetime = None,
    responded_at: datetime = None,
    severity: str = "high",
    vulnerability_type: str = "xss",
) -> Dict[str, Any]:
    """Create a sample submission dictionary."""
    submitted = submitted_at or datetime.now()
    return {
        "submission_id": submission_id,
        "decision_id": decision_id,
        "platform": platform,
        "status": status,
        "submitted_at": submitted,
        "responded_at": responded_at or (submitted + timedelta(days=7)),
        "severity": severity,
        "vulnerability_type": vulnerability_type,
    }


def create_sample_session(
    session_id: str = "sess-001",
    reviewer_id: str = "reviewer-001",
    start_time: datetime = None,
    end_time: datetime = None,
) -> Dict[str, Any]:
    """Create a sample review session dictionary."""
    start = start_time or datetime.now()
    return {
        "session_id": session_id,
        "reviewer_id": reviewer_id,
        "start_time": start,
        "end_time": end_time or (start + timedelta(hours=2)),
    }


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def empty_data_access() -> DataAccessLayer:
    """Create an empty data access layer."""
    return DataAccessLayer(
        decisions=[],
        submissions=[],
        review_sessions=[],
    )


@pytest.fixture
def sample_decisions() -> List[Dict[str, Any]]:
    """Create sample decisions for testing."""
    base_time = datetime(2025, 1, 1, 10, 0, 0)
    return [
        create_sample_decision(
            decision_id=f"dec-{i:03d}",
            finding_id=f"find-{i:03d}",
            reviewer_id=f"reviewer-{(i % 3) + 1:03d}",
            decision_type=["approve", "reject", "defer"][i % 3],
            severity=["critical", "high", "medium", "low"][i % 4],
            timestamp=base_time + timedelta(days=i),
            target_id=f"target-{(i % 2) + 1:03d}",
            content=f"Finding content {i}",
            vulnerability_type=["xss", "sqli", "csrf"][i % 3],
        )
        for i in range(20)
    ]


@pytest.fixture
def sample_submissions() -> List[Dict[str, Any]]:
    """Create sample submissions for testing."""
    base_time = datetime(2025, 1, 1, 10, 0, 0)
    return [
        create_sample_submission(
            submission_id=f"sub-{i:03d}",
            decision_id=f"dec-{i:03d}",
            platform=["hackerone", "bugcrowd", "generic"][i % 3],
            status=["acknowledged", "rejected", "pending"][i % 3],
            submitted_at=base_time + timedelta(days=i),
            severity=["critical", "high", "medium", "low"][i % 4],
            vulnerability_type=["xss", "sqli", "csrf"][i % 3],
        )
        for i in range(15)
    ]


@pytest.fixture
def sample_sessions() -> List[Dict[str, Any]]:
    """Create sample review sessions for testing."""
    base_time = datetime(2025, 1, 1, 10, 0, 0)
    return [
        create_sample_session(
            session_id=f"sess-{i:03d}",
            reviewer_id=f"reviewer-{(i % 3) + 1:03d}",
            start_time=base_time + timedelta(days=i),
        )
        for i in range(10)
    ]


@pytest.fixture
def populated_data_access(
    sample_decisions,
    sample_submissions,
    sample_sessions,
) -> DataAccessLayer:
    """Create a populated data access layer."""
    return DataAccessLayer(
        decisions=sample_decisions,
        submissions=sample_submissions,
        review_sessions=sample_sessions,
    )


@pytest.fixture
def duplicate_detector(populated_data_access) -> DuplicateDetector:
    """Create a duplicate detector with sample data."""
    return DuplicateDetector(populated_data_access)


@pytest.fixture
def acceptance_tracker(populated_data_access) -> AcceptanceTracker:
    """Create an acceptance tracker with sample data."""
    return AcceptanceTracker(populated_data_access)


@pytest.fixture
def target_profiler(populated_data_access) -> TargetProfiler:
    """Create a target profiler with sample data."""
    return TargetProfiler(populated_data_access)


@pytest.fixture
def performance_analyzer(populated_data_access) -> PerformanceAnalyzer:
    """Create a performance analyzer with sample data."""
    return PerformanceAnalyzer(populated_data_access)


@pytest.fixture
def pattern_engine(populated_data_access) -> PatternEngine:
    """Create a pattern engine with sample data."""
    return PatternEngine(populated_data_access)
