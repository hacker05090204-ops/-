# PHASE 02 REQUIREMENTS — 2026 RE-IMPLEMENTATION

**Document ID:** GOV-PHASE02-2026-REIMPL-REQ  
**Date:** 2026-01-20  
**Status:** APPROVED  

---

## Functional Requirements

### FR-01: Actor Types
- The module MUST define an `ActorType` enum with values: `HUMAN`, `SYSTEM`, `EXTERNAL`
- All actors MUST have a type
- `SYSTEM` actors are internal processes, but CANNOT make autonomous security decisions

### FR-02: Role Definitions
- The module MUST define a `Role` enum with values: `OPERATOR`, `AUDITOR`, `ADMINISTRATOR`
- `OPERATOR` — Can execute approved operations with human confirmation
- `AUDITOR` — Can read logs and reports, cannot execute
- `ADMINISTRATOR` — Can configure system, cannot bypass human confirmation

### FR-03: Actor Identity
- Each actor MUST have a unique `actor_id` (string)
- Each actor MUST have a `name` (human-readable)
- Each actor MUST have an `actor_type` (ActorType)
- Each actor MUST have a `role` (Role)

### FR-04: Actor Dataclass
- The module MUST provide an immutable `Actor` dataclass
- Actor instances MUST be hashable
- Actor creation MUST validate inputs

### FR-05: Permission Checks
- The module MUST provide `can_execute(actor) -> bool`
- The module MUST provide `can_audit(actor) -> bool`
- The module MUST provide `can_configure(actor) -> bool`
- Permission checks MUST NOT perform scoring or ranking

---

## Non-Functional Requirements

### NFR-01: Immutability
- Actor instances MUST be immutable after creation
- Use `frozen=True` dataclass

### NFR-02: No Automation
- No actor can be granted autonomous decision-making authority
- All security operations require human confirmation

### NFR-03: Type Safety
- All public APIs MUST have complete type hints

---

## Forbidden Behaviors

| Behavior | Status |
|----------|--------|
| Actors making autonomous security decisions | ❌ FORBIDDEN |
| Scoring or ranking actors | ❌ FORBIDDEN |
| Background actor creation | ❌ FORBIDDEN |
| Modifying frozen phases (15-29) | ❌ FORBIDDEN |
| Bypassing human confirmation | ❌ FORBIDDEN |

---

**END OF REQUIREMENTS**
