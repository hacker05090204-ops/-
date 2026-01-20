# PHASE 01 REQUIREMENTS — 2026 RE-IMPLEMENTATION

**Document ID:** GOV-PHASE01-2026-REIMPL-REQ  
**Date:** 2026-01-20  
**Status:** APPROVED  

---

## Functional Requirements

### FR-01: System Identity
- The module MUST expose a unique `SYSTEM_ID` constant
- The module MUST expose a `SYSTEM_NAME` constant with value "kali-mcp-toolkit"
- The module MUST expose a `REIMPLEMENTATION_DATE` constant with value "2026-01-20"

### FR-02: Version Information
- The module MUST expose `VERSION` as a semantic version string
- The module MUST expose `VERSION_TUPLE` as a tuple (major, minor, patch)
- Version MUST start at 1.0.0 for this re-implementation

### FR-03: Core Invariants
- The module MUST define `INVARIANT_HUMAN_AUTHORITY` = True
- The module MUST define `INVARIANT_NO_AUTO_EXPLOIT` = True
- The module MUST define `INVARIANT_AUDIT_REQUIRED` = True
- The module MUST define `INVARIANT_NO_SCORING` = True
- All invariants MUST be read-only (cannot be modified at runtime)

### FR-04: Security Constants
- The module MUST define `MAX_OPERATION_TIMEOUT_SECONDS`
- The module MUST define `REQUIRE_HUMAN_CONFIRMATION` = True

---

## Non-Functional Requirements

### NFR-01: Immutability
- All constants MUST be truly immutable (use `Final` type hints)
- Any attempt to modify constants MUST raise an error

### NFR-02: No Side Effects
- Importing the module MUST NOT produce side effects
- No network calls, no file access, no logging on import

### NFR-03: Documentation
- All constants MUST have docstrings explaining their purpose

---

## Forbidden Behaviors

| Behavior | Status |
|----------|--------|
| Automated decision-making | ❌ FORBIDDEN |
| Scoring or ranking | ❌ FORBIDDEN |
| Network access on import | ❌ FORBIDDEN |
| Modifying frozen phases (15-29) | ❌ FORBIDDEN |
| Background execution | ❌ FORBIDDEN |

---

**END OF REQUIREMENTS**
