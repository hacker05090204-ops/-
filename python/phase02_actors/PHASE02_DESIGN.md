# PHASE 02 DESIGN — 2026 RE-IMPLEMENTATION

**Document ID:** GOV-PHASE02-2026-REIMPL-DESIGN  
**Date:** 2026-01-20  
**Status:** APPROVED  

---

## 1. Architecture Overview

Phase-02 provides the actor and role model that defines WHO can interact with the system and WHAT they can do.

```
┌─────────────────────────────────────────────────────────┐
│                    PHASE-02 ACTORS                      │
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │   ActorType     │  │      Role       │              │
│  │ - HUMAN         │  │ - OPERATOR      │              │
│  │ - SYSTEM        │  │ - AUDITOR       │              │
│  │ - EXTERNAL      │  │ - ADMINISTRATOR │              │
│  └─────────────────┘  └─────────────────┘              │
│                                                         │
│  ┌─────────────────────────────────────────┐           │
│  │              Actor (dataclass)          │           │
│  │ - actor_id: str                         │           │
│  │ - name: str                             │           │
│  │ - actor_type: ActorType                 │           │
│  │ - role: Role                            │           │
│  └─────────────────────────────────────────┘           │
│                                                         │
│  ┌─────────────────────────────────────────┐           │
│  │         Permission Functions            │           │
│  │ - can_execute(actor) -> bool            │           │
│  │ - can_audit(actor) -> bool              │           │
│  │ - can_configure(actor) -> bool          │           │
│  └─────────────────────────────────────────┘           │
│                                                         │
└─────────────────────────────────────────────────────────┘
           │                    ▲
           │                    │
           ▼                    │
    [PHASE-01 CORE]     [CONSUMED BY PHASES 3+]
```

---

## 2. Module Structure

```
phase02_actors/
├── __init__.py              # Re-exports public API
├── actors.py                # Actor and Role definitions
├── tests/
│   ├── __init__.py
│   └── test_phase02_actors.py
├── PHASE02_GOVERNANCE_OPENING.md
├── PHASE02_REQUIREMENTS.md
├── PHASE02_TASK_LIST.md
├── PHASE02_IMPLEMENTATION_AUTHORIZATION.md
├── PHASE02_DESIGN.md        # (this document)
└── PHASE02_GOVERNANCE_FREEZE.md
```

---

## 3. Data Model

### ActorType Enum
```python
class ActorType(Enum):
    HUMAN = "human"        # Human operator
    SYSTEM = "system"      # Internal system process
    EXTERNAL = "external"  # External entity
```

### Role Enum
```python
class Role(Enum):
    OPERATOR = "operator"           # Can execute approved operations
    AUDITOR = "auditor"             # Can read, cannot execute
    ADMINISTRATOR = "administrator" # Can configure
```

### Actor Dataclass
```python
@dataclass(frozen=True)
class Actor:
    actor_id: str
    name: str
    actor_type: ActorType
    role: Role
```

---

## 4. Permission Matrix

| Role | can_execute | can_audit | can_configure |
|------|-------------|-----------|---------------|
| OPERATOR | ✅ | ✅ | ❌ |
| AUDITOR | ❌ | ✅ | ❌ |
| ADMINISTRATOR | ✅ | ✅ | ✅ |

**Note:** All execute operations still require human confirmation per Phase-01 invariants.

---

## 5. Security Constraints

1. **No Autonomous Actors:** Even SYSTEM actors cannot make security decisions
2. **Immutable Actors:** Once created, actors cannot be modified
3. **Validated Input:** Actor creation validates all inputs
4. **No Scoring:** Permission checks are binary (yes/no), no scoring

---

## 6. Interfaces

### Public Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `can_execute` | `(actor: Actor) -> bool` | Check if actor can execute |
| `can_audit` | `(actor: Actor) -> bool` | Check if actor can audit |
| `can_configure` | `(actor: Actor) -> bool` | Check if actor can configure |
| `create_actor` | `(actor_id, name, actor_type, role) -> Actor` | Create validated actor |

---

**NO CODE FOLLOWS IN THIS DOCUMENT — IMPLEMENTATION IS SEPARATE**

---

**END OF DESIGN**
