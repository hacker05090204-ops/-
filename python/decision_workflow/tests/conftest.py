"""
Pytest fixtures and hypothesis strategies for Phase-6 tests.
"""

import pytest
from datetime import datetime, timedelta
from hypothesis import strategies as st
from typing import Optional

from decision_workflow.types import (
    Role,
    DecisionType,
    Severity,
    Action,
    Credentials,
    ReviewSession,
    DecisionInput,
    HumanDecision,
    AuditEntry,
)


# ============================================================================
# Hypothesis Strategies
# ============================================================================

@st.composite
def credentials_strategy(draw) -> Credentials:
    """Generate random valid credentials."""
    user_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N"))))
    role = draw(st.sampled_from(Role))
    return Credentials(user_id=user_id, role=role)


@st.composite
def review_session_strategy(draw) -> ReviewSession:
    """Generate random valid review session."""
    session_id = draw(st.uuids().map(str))
    reviewer_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N"))))
    role = draw(st.sampled_from(Role))
    start_time = draw(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 12, 31)))
    return ReviewSession(
        session_id=session_id,
        reviewer_id=reviewer_id,
        role=role,
        start_time=start_time,
    )


@st.composite
def decision_input_strategy(draw, decision_type: Optional[DecisionType] = None) -> DecisionInput:
    """Generate random decision input, optionally for a specific type."""
    if decision_type is None:
        decision_type = draw(st.sampled_from(DecisionType))
    
    severity = None
    cvss_score = None
    rationale = None
    defer_reason = None
    escalation_target = None
    note = None
    
    if decision_type == DecisionType.APPROVE:
        severity = draw(st.sampled_from(Severity))
        cvss_score = draw(st.one_of(st.none(), st.floats(min_value=0.0, max_value=10.0)))
    elif decision_type == DecisionType.REJECT:
        rationale = draw(st.text(min_size=1, max_size=500))
    elif decision_type == DecisionType.DEFER:
        defer_reason = draw(st.text(min_size=1, max_size=500))
    elif decision_type == DecisionType.ESCALATE:
        escalation_target = draw(st.text(min_size=1, max_size=100))
    elif decision_type == DecisionType.ADD_NOTE:
        note = draw(st.text(min_size=1, max_size=1000))
    
    return DecisionInput(
        decision_type=decision_type,
        severity=severity,
        cvss_score=cvss_score,
        rationale=rationale,
        defer_reason=defer_reason,
        escalation_target=escalation_target,
        note=note,
    )


@st.composite
def cvss_score_strategy(draw) -> float:
    """Generate valid CVSS scores (0.0 to 10.0)."""
    return draw(st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False))


@st.composite
def invalid_cvss_score_strategy(draw) -> float:
    """Generate invalid CVSS scores (outside 0.0 to 10.0)."""
    return draw(st.one_of(
        st.floats(max_value=-0.1, allow_nan=False, allow_infinity=False),
        st.floats(min_value=10.1, allow_nan=False, allow_infinity=False),
    ))


# ============================================================================
# Pytest Fixtures
# ============================================================================

@pytest.fixture
def operator_credentials() -> Credentials:
    """Create operator credentials."""
    return Credentials(user_id="operator_user", role=Role.OPERATOR)


@pytest.fixture
def reviewer_credentials() -> Credentials:
    """Create reviewer credentials."""
    return Credentials(user_id="reviewer_user", role=Role.REVIEWER)


@pytest.fixture
def operator_session() -> ReviewSession:
    """Create an operator session."""
    return ReviewSession(
        session_id="op-session-001",
        reviewer_id="operator_user",
        role=Role.OPERATOR,
        start_time=datetime.now(),
    )


@pytest.fixture
def reviewer_session() -> ReviewSession:
    """Create a reviewer session."""
    return ReviewSession(
        session_id="rev-session-001",
        reviewer_id="reviewer_user",
        role=Role.REVIEWER,
        start_time=datetime.now(),
    )


@pytest.fixture
def approve_decision_input() -> DecisionInput:
    """Create a valid approve decision input."""
    return DecisionInput(
        decision_type=DecisionType.APPROVE,
        severity=Severity.HIGH,
        cvss_score=7.5,
    )


@pytest.fixture
def reject_decision_input() -> DecisionInput:
    """Create a valid reject decision input."""
    return DecisionInput(
        decision_type=DecisionType.REJECT,
        rationale="False positive - not exploitable in this context",
    )


@pytest.fixture
def defer_decision_input() -> DecisionInput:
    """Create a valid defer decision input."""
    return DecisionInput(
        decision_type=DecisionType.DEFER,
        defer_reason="Need more information from development team",
    )


@pytest.fixture
def escalate_decision_input() -> DecisionInput:
    """Create a valid escalate decision input."""
    return DecisionInput(
        decision_type=DecisionType.ESCALATE,
        escalation_target="senior_reviewer_001",
    )
