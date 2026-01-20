"""
PHASE 02 — ACTOR & ROLE MODEL
2026 RE-IMPLEMENTATION

This module defines actors (entities that interact with the system) and
roles (permissions and responsibilities).

⚠️ CRITICAL NOTICE:
    This is a 2026 RE-IMPLEMENTATION.
    This is NOT a recovery of lost code.
    This is NOT a claim of historical behavior.

Document ID: GOV-PHASE02-2026-REIMPL-CODE
Date: 2026-01-20
Status: IMPLEMENTED
"""

from dataclasses import dataclass
from enum import Enum
from typing import Final


# =============================================================================
# ACTOR TYPE ENUM
# =============================================================================

class ActorType(Enum):
    """
    Type of actor interacting with the system.
    
    HUMAN: A human operator (primary actor type)
    SYSTEM: Internal system process (cannot make security decisions)
    EXTERNAL: External entity (e.g., API consumer)
    """
    HUMAN = "human"
    SYSTEM = "system"
    EXTERNAL = "external"


# =============================================================================
# ROLE ENUM
# =============================================================================

class Role(Enum):
    """
    Role defining permissions and responsibilities.
    
    OPERATOR: Can execute approved operations (with human confirmation)
    AUDITOR: Can read logs and reports, cannot execute
    ADMINISTRATOR: Can configure system, cannot bypass human confirmation
    """
    OPERATOR = "operator"
    AUDITOR = "auditor"
    ADMINISTRATOR = "administrator"


# =============================================================================
# ACTOR DATACLASS
# =============================================================================

@dataclass(frozen=True)
class Actor:
    """
    Immutable representation of an actor in the system.
    
    Attributes:
        actor_id: Unique identifier for this actor
        name: Human-readable name
        actor_type: Type of actor (HUMAN, SYSTEM, EXTERNAL)
        role: Role defining permissions (OPERATOR, AUDITOR, ADMINISTRATOR)
    
    Note:
        Actors are immutable after creation.
        Even SYSTEM actors cannot make autonomous security decisions.
    """
    actor_id: str
    name: str
    actor_type: ActorType
    role: Role


# =============================================================================
# ACTOR FACTORY
# =============================================================================

def create_actor(
    actor_id: str,
    name: str,
    actor_type: ActorType,
    role: Role
) -> Actor:
    """
    Create a validated Actor instance.
    
    Args:
        actor_id: Unique identifier for the actor (non-empty)
        name: Human-readable name (non-empty)
        actor_type: Type of actor
        role: Role defining permissions
    
    Returns:
        Actor: Validated actor instance
    
    Raises:
        ValueError: If actor_id or name is empty
    """
    if not actor_id or not actor_id.strip():
        raise ValueError("actor_id cannot be empty")
    if not name or not name.strip():
        raise ValueError("name cannot be empty")
    
    return Actor(
        actor_id=actor_id.strip(),
        name=name.strip(),
        actor_type=actor_type,
        role=role
    )


# =============================================================================
# PERMISSION FUNCTIONS
# =============================================================================

def can_execute(actor: Actor) -> bool:
    """
    Check if an actor can execute operations.
    
    Operators and Administrators can execute.
    Auditors cannot execute.
    
    Note:
        This only checks role permission. All executions still require
        human confirmation per INVARIANT_HUMAN_AUTHORITY.
    
    Args:
        actor: The actor to check
    
    Returns:
        bool: True if actor can execute, False otherwise
    """
    return actor.role in (Role.OPERATOR, Role.ADMINISTRATOR)


def can_audit(actor: Actor) -> bool:
    """
    Check if an actor can audit (read logs and reports).
    
    All roles can audit.
    
    Args:
        actor: The actor to check
    
    Returns:
        bool: True if actor can audit, False otherwise
    """
    return actor.role in (Role.OPERATOR, Role.AUDITOR, Role.ADMINISTRATOR)


def can_configure(actor: Actor) -> bool:
    """
    Check if an actor can configure the system.
    
    Only Administrators can configure.
    
    Note:
        Configuration changes do NOT bypass human confirmation requirements.
    
    Args:
        actor: The actor to check
    
    Returns:
        bool: True if actor can configure, False otherwise
    """
    return actor.role == Role.ADMINISTRATOR


# =============================================================================
# END OF PHASE-02 ACTORS
# =============================================================================
