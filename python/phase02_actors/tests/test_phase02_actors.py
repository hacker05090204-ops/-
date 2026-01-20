"""
PHASE 02 TESTS — 2026 RE-IMPLEMENTATION

These tests validate the Actor & Role Model for Phase-02.
All tests are written BEFORE implementation (TDD approach).

Test Categories:
1. Enum Tests - Verify ActorType and Role enums
2. Actor Tests - Verify Actor dataclass
3. Permission Tests - Verify permission functions
4. Forbidden Behavior Tests - Verify no automation/scoring
"""

import pytest
from enum import Enum
from dataclasses import FrozenInstanceError


class TestActorTypeEnum:
    """Test ActorType enum definition."""

    def test_actor_type_exists(self):
        """ActorType enum must exist."""
        from phase02_actors.actors import ActorType
        assert ActorType is not None

    def test_actor_type_is_enum(self):
        """ActorType must be an Enum."""
        from phase02_actors.actors import ActorType
        assert issubclass(ActorType, Enum)

    def test_actor_type_has_human(self):
        """ActorType must have HUMAN value."""
        from phase02_actors.actors import ActorType
        assert hasattr(ActorType, 'HUMAN')
        assert ActorType.HUMAN.value == "human"

    def test_actor_type_has_system(self):
        """ActorType must have SYSTEM value."""
        from phase02_actors.actors import ActorType
        assert hasattr(ActorType, 'SYSTEM')
        assert ActorType.SYSTEM.value == "system"

    def test_actor_type_has_external(self):
        """ActorType must have EXTERNAL value."""
        from phase02_actors.actors import ActorType
        assert hasattr(ActorType, 'EXTERNAL')
        assert ActorType.EXTERNAL.value == "external"


class TestRoleEnum:
    """Test Role enum definition."""

    def test_role_exists(self):
        """Role enum must exist."""
        from phase02_actors.actors import Role
        assert Role is not None

    def test_role_is_enum(self):
        """Role must be an Enum."""
        from phase02_actors.actors import Role
        assert issubclass(Role, Enum)

    def test_role_has_operator(self):
        """Role must have OPERATOR value."""
        from phase02_actors.actors import Role
        assert hasattr(Role, 'OPERATOR')
        assert Role.OPERATOR.value == "operator"

    def test_role_has_auditor(self):
        """Role must have AUDITOR value."""
        from phase02_actors.actors import Role
        assert hasattr(Role, 'AUDITOR')
        assert Role.AUDITOR.value == "auditor"

    def test_role_has_administrator(self):
        """Role must have ADMINISTRATOR value."""
        from phase02_actors.actors import Role
        assert hasattr(Role, 'ADMINISTRATOR')
        assert Role.ADMINISTRATOR.value == "administrator"


class TestActorDataclass:
    """Test Actor dataclass."""

    def test_actor_exists(self):
        """Actor class must exist."""
        from phase02_actors.actors import Actor
        assert Actor is not None

    def test_actor_creation(self):
        """Actor can be created with required fields."""
        from phase02_actors.actors import Actor, ActorType, Role
        actor = Actor(
            actor_id="test-001",
            name="Test User",
            actor_type=ActorType.HUMAN,
            role=Role.OPERATOR
        )
        assert actor.actor_id == "test-001"
        assert actor.name == "Test User"
        assert actor.actor_type == ActorType.HUMAN
        assert actor.role == Role.OPERATOR

    def test_actor_is_immutable(self):
        """Actor must be immutable (frozen)."""
        from phase02_actors.actors import Actor, ActorType, Role
        actor = Actor(
            actor_id="test-001",
            name="Test User",
            actor_type=ActorType.HUMAN,
            role=Role.OPERATOR
        )
        with pytest.raises(FrozenInstanceError):
            actor.name = "Modified Name"

    def test_actor_is_hashable(self):
        """Actor must be hashable."""
        from phase02_actors.actors import Actor, ActorType, Role
        actor = Actor(
            actor_id="test-001",
            name="Test User",
            actor_type=ActorType.HUMAN,
            role=Role.OPERATOR
        )
        # Should not raise
        hash(actor)

    def test_actor_equality(self):
        """Two actors with same fields should be equal."""
        from phase02_actors.actors import Actor, ActorType, Role
        actor1 = Actor(
            actor_id="test-001",
            name="Test User",
            actor_type=ActorType.HUMAN,
            role=Role.OPERATOR
        )
        actor2 = Actor(
            actor_id="test-001",
            name="Test User",
            actor_type=ActorType.HUMAN,
            role=Role.OPERATOR
        )
        assert actor1 == actor2


class TestCreateActorFunction:
    """Test create_actor factory function."""

    def test_create_actor_exists(self):
        """create_actor function must exist."""
        from phase02_actors.actors import create_actor
        assert callable(create_actor)

    def test_create_actor_returns_actor(self):
        """create_actor must return an Actor instance."""
        from phase02_actors.actors import create_actor, Actor, ActorType, Role
        actor = create_actor(
            actor_id="test-001",
            name="Test User",
            actor_type=ActorType.HUMAN,
            role=Role.OPERATOR
        )
        assert isinstance(actor, Actor)

    def test_create_actor_validates_empty_id(self):
        """create_actor must reject empty actor_id."""
        from phase02_actors.actors import create_actor, ActorType, Role
        with pytest.raises(ValueError):
            create_actor(
                actor_id="",
                name="Test User",
                actor_type=ActorType.HUMAN,
                role=Role.OPERATOR
            )

    def test_create_actor_validates_empty_name(self):
        """create_actor must reject empty name."""
        from phase02_actors.actors import create_actor, ActorType, Role
        with pytest.raises(ValueError):
            create_actor(
                actor_id="test-001",
                name="",
                actor_type=ActorType.HUMAN,
                role=Role.OPERATOR
            )


class TestCanExecutePermission:
    """Test can_execute permission function."""

    def test_can_execute_exists(self):
        """can_execute function must exist."""
        from phase02_actors.actors import can_execute
        assert callable(can_execute)

    def test_operator_can_execute(self):
        """OPERATOR role can execute."""
        from phase02_actors.actors import Actor, ActorType, Role, can_execute
        actor = Actor("op-001", "Operator", ActorType.HUMAN, Role.OPERATOR)
        assert can_execute(actor) is True

    def test_auditor_cannot_execute(self):
        """AUDITOR role cannot execute."""
        from phase02_actors.actors import Actor, ActorType, Role, can_execute
        actor = Actor("aud-001", "Auditor", ActorType.HUMAN, Role.AUDITOR)
        assert can_execute(actor) is False

    def test_administrator_can_execute(self):
        """ADMINISTRATOR role can execute."""
        from phase02_actors.actors import Actor, ActorType, Role, can_execute
        actor = Actor("adm-001", "Admin", ActorType.HUMAN, Role.ADMINISTRATOR)
        assert can_execute(actor) is True


class TestCanAuditPermission:
    """Test can_audit permission function."""

    def test_can_audit_exists(self):
        """can_audit function must exist."""
        from phase02_actors.actors import can_audit
        assert callable(can_audit)

    def test_operator_can_audit(self):
        """OPERATOR role can audit."""
        from phase02_actors.actors import Actor, ActorType, Role, can_audit
        actor = Actor("op-001", "Operator", ActorType.HUMAN, Role.OPERATOR)
        assert can_audit(actor) is True

    def test_auditor_can_audit(self):
        """AUDITOR role can audit."""
        from phase02_actors.actors import Actor, ActorType, Role, can_audit
        actor = Actor("aud-001", "Auditor", ActorType.HUMAN, Role.AUDITOR)
        assert can_audit(actor) is True

    def test_administrator_can_audit(self):
        """ADMINISTRATOR role can audit."""
        from phase02_actors.actors import Actor, ActorType, Role, can_audit
        actor = Actor("adm-001", "Admin", ActorType.HUMAN, Role.ADMINISTRATOR)
        assert can_audit(actor) is True


class TestCanConfigurePermission:
    """Test can_configure permission function."""

    def test_can_configure_exists(self):
        """can_configure function must exist."""
        from phase02_actors.actors import can_configure
        assert callable(can_configure)

    def test_operator_cannot_configure(self):
        """OPERATOR role cannot configure."""
        from phase02_actors.actors import Actor, ActorType, Role, can_configure
        actor = Actor("op-001", "Operator", ActorType.HUMAN, Role.OPERATOR)
        assert can_configure(actor) is False

    def test_auditor_cannot_configure(self):
        """AUDITOR role cannot configure."""
        from phase02_actors.actors import Actor, ActorType, Role, can_configure
        actor = Actor("aud-001", "Auditor", ActorType.HUMAN, Role.AUDITOR)
        assert can_configure(actor) is False

    def test_administrator_can_configure(self):
        """ADMINISTRATOR role can configure."""
        from phase02_actors.actors import Actor, ActorType, Role, can_configure
        actor = Actor("adm-001", "Admin", ActorType.HUMAN, Role.ADMINISTRATOR)
        assert can_configure(actor) is True


class TestNoForbiddenBehaviors:
    """Test that module has no forbidden behaviors."""

    def test_permissions_are_binary(self):
        """Permissions must return bool, not scores."""
        from phase02_actors.actors import (
            Actor, ActorType, Role,
            can_execute, can_audit, can_configure
        )
        actor = Actor("test-001", "Test", ActorType.HUMAN, Role.OPERATOR)
        
        # All permission checks must return exactly True or False
        assert can_execute(actor) in (True, False)
        assert can_audit(actor) in (True, False)
        assert can_configure(actor) in (True, False)

    def test_no_scoring_in_module(self):
        """Module should have no scoring/ranking functions."""
        from phase02_actors import actors
        public_attrs = [a for a in dir(actors) if not a.startswith('_')]
        
        # No attribute should contain 'score', 'rank', 'priority'
        for attr_name in public_attrs:
            assert 'score' not in attr_name.lower(), f"Found scoring: {attr_name}"
            assert 'rank' not in attr_name.lower(), f"Found ranking: {attr_name}"
            assert 'priority' not in attr_name.lower(), f"Found priority: {attr_name}"


class TestPackageExports:
    """Test that __init__.py re-exports all public API."""

    def test_package_exports_actortype(self):
        """Package must export ActorType."""
        from phase02_actors import ActorType
        assert ActorType is not None

    def test_package_exports_role(self):
        """Package must export Role."""
        from phase02_actors import Role
        assert Role is not None

    def test_package_exports_actor(self):
        """Package must export Actor."""
        from phase02_actors import Actor
        assert Actor is not None

    def test_package_exports_create_actor(self):
        """Package must export create_actor."""
        from phase02_actors import create_actor
        assert callable(create_actor)

    def test_package_exports_permissions(self):
        """Package must export permission functions."""
        from phase02_actors import can_execute, can_audit, can_configure
        assert callable(can_execute)
        assert callable(can_audit)
        assert callable(can_configure)
