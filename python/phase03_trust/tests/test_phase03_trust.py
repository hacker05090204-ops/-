"""
PHASE 03 TESTS — 2026 RE-IMPLEMENTATION

Tests for Trust Boundaries module.
"""

import pytest
from enum import Enum
from dataclasses import FrozenInstanceError


class TestTrustZoneEnum:
    """Test TrustZone enum."""

    def test_trust_zone_exists(self):
        from phase03_trust.trust import TrustZone
        assert TrustZone is not None

    def test_trust_zone_is_enum(self):
        from phase03_trust.trust import TrustZone
        assert issubclass(TrustZone, Enum)

    def test_has_untrusted(self):
        from phase03_trust.trust import TrustZone
        assert hasattr(TrustZone, 'UNTRUSTED')

    def test_has_boundary(self):
        from phase03_trust.trust import TrustZone
        assert hasattr(TrustZone, 'BOUNDARY')

    def test_has_internal(self):
        from phase03_trust.trust import TrustZone
        assert hasattr(TrustZone, 'INTERNAL')

    def test_has_privileged(self):
        from phase03_trust.trust import TrustZone
        assert hasattr(TrustZone, 'PRIVILEGED')


class TestTrustBoundaryDataclass:
    """Test TrustBoundary dataclass."""

    def test_trust_boundary_exists(self):
        from phase03_trust.trust import TrustBoundary
        assert TrustBoundary is not None

    def test_trust_boundary_creation(self):
        from phase03_trust.trust import TrustBoundary, TrustZone
        boundary = TrustBoundary(
            name="test_boundary",
            from_zone=TrustZone.UNTRUSTED,
            to_zone=TrustZone.BOUNDARY,
            requires_human_approval=False
        )
        assert boundary.name == "test_boundary"
        assert boundary.from_zone == TrustZone.UNTRUSTED
        assert boundary.to_zone == TrustZone.BOUNDARY
        assert boundary.requires_human_approval is False

    def test_trust_boundary_is_immutable(self):
        from phase03_trust.trust import TrustBoundary, TrustZone
        boundary = TrustBoundary(
            name="test",
            from_zone=TrustZone.UNTRUSTED,
            to_zone=TrustZone.BOUNDARY,
            requires_human_approval=False
        )
        with pytest.raises(FrozenInstanceError):
            boundary.name = "modified"


class TestPredefinedBoundaries:
    """Test predefined boundaries."""

    def test_untrusted_to_boundary_exists(self):
        from phase03_trust.trust import UNTRUSTED_TO_BOUNDARY
        assert UNTRUSTED_TO_BOUNDARY is not None

    def test_boundary_to_internal_exists(self):
        from phase03_trust.trust import BOUNDARY_TO_INTERNAL
        assert BOUNDARY_TO_INTERNAL is not None

    def test_internal_to_privileged_exists(self):
        from phase03_trust.trust import INTERNAL_TO_PRIVILEGED
        assert INTERNAL_TO_PRIVILEGED is not None

    def test_privileged_requires_human_approval(self):
        from phase03_trust.trust import INTERNAL_TO_PRIVILEGED
        assert INTERNAL_TO_PRIVILEGED.requires_human_approval is True


class TestValidateCrossing:
    """Test validate_crossing function."""

    def test_validate_crossing_exists(self):
        from phase03_trust.trust import validate_crossing
        assert callable(validate_crossing)

    def test_operator_can_cross_to_internal(self):
        from phase03_trust.trust import validate_crossing, BOUNDARY_TO_INTERNAL
        from phase02_actors import Actor, ActorType, Role
        actor = Actor("op-001", "Operator", ActorType.HUMAN, Role.OPERATOR)
        assert validate_crossing(actor, BOUNDARY_TO_INTERNAL) is True

    def test_auditor_cannot_cross_to_internal(self):
        from phase03_trust.trust import validate_crossing, BOUNDARY_TO_INTERNAL
        from phase02_actors import Actor, ActorType, Role
        actor = Actor("aud-001", "Auditor", ActorType.HUMAN, Role.AUDITOR)
        assert validate_crossing(actor, BOUNDARY_TO_INTERNAL) is False

    def test_operator_cannot_cross_to_privileged(self):
        from phase03_trust.trust import validate_crossing, INTERNAL_TO_PRIVILEGED
        from phase02_actors import Actor, ActorType, Role
        actor = Actor("op-001", "Operator", ActorType.HUMAN, Role.OPERATOR)
        assert validate_crossing(actor, INTERNAL_TO_PRIVILEGED) is False

    def test_admin_can_cross_to_privileged(self):
        from phase03_trust.trust import validate_crossing, INTERNAL_TO_PRIVILEGED
        from phase02_actors import Actor, ActorType, Role
        actor = Actor("adm-001", "Admin", ActorType.HUMAN, Role.ADMINISTRATOR)
        assert validate_crossing(actor, INTERNAL_TO_PRIVILEGED) is True


class TestCanCrossToPrivileged:
    """Test can_cross_to_privileged function."""

    def test_can_cross_to_privileged_exists(self):
        from phase03_trust.trust import can_cross_to_privileged
        assert callable(can_cross_to_privileged)

    def test_only_admin_can_cross_to_privileged(self):
        from phase03_trust.trust import can_cross_to_privileged
        from phase02_actors import Actor, ActorType, Role
        
        operator = Actor("op-001", "Operator", ActorType.HUMAN, Role.OPERATOR)
        auditor = Actor("aud-001", "Auditor", ActorType.HUMAN, Role.AUDITOR)
        admin = Actor("adm-001", "Admin", ActorType.HUMAN, Role.ADMINISTRATOR)
        
        assert can_cross_to_privileged(operator) is False
        assert can_cross_to_privileged(auditor) is False
        assert can_cross_to_privileged(admin) is True


class TestNoForbiddenBehaviors:
    """Test no forbidden behaviors."""

    def test_no_scoring_in_module(self):
        from phase03_trust import trust
        public_attrs = [a for a in dir(trust) if not a.startswith('_')]
        for attr_name in public_attrs:
            assert 'score' not in attr_name.lower()
            assert 'rank' not in attr_name.lower()


class TestPackageExports:
    """Test package exports."""

    def test_package_exports_all(self):
        from phase03_trust import (
            TrustZone,
            TrustBoundary,
            UNTRUSTED_TO_BOUNDARY,
            BOUNDARY_TO_INTERNAL,
            INTERNAL_TO_PRIVILEGED,
            validate_crossing,
            can_cross_to_privileged,
        )
        assert TrustZone is not None
