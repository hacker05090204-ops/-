"""
PHASE 02 — ACTOR & ROLE MODEL PACKAGE
2026 RE-IMPLEMENTATION

This package provides the actor and role model for the kali-mcp-toolkit system.

⚠️ CRITICAL NOTICE:
    This is a 2026 RE-IMPLEMENTATION.
    This is NOT a recovery of lost code.

Usage:
    from phase02_actors import Actor, Role, ActorType, can_execute
"""

from phase02_actors.actors import (
    # Enums
    ActorType,
    Role,
    # Dataclass
    Actor,
    # Factory
    create_actor,
    # Permission functions
    can_execute,
    can_audit,
    can_configure,
)

__all__ = [
    "ActorType",
    "Role",
    "Actor",
    "create_actor",
    "can_execute",
    "can_audit",
    "can_configure",
]
