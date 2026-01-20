# PHASE 01 DESIGN — 2026 RE-IMPLEMENTATION

**Document ID:** GOV-PHASE01-2026-REIMPL-DESIGN  
**Date:** 2026-01-20  
**Status:** APPROVED  

---

## 1. Architecture Overview

Phase-01 provides the foundational constants layer for the entire kali-mcp-toolkit system.

```
┌─────────────────────────────────────────────────────────┐
│                    PHASE-01 CORE                        │
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ System Identity │  │    Invariants   │              │
│  │ - SYSTEM_ID     │  │ - HUMAN_AUTHORITY│             │
│  │ - SYSTEM_NAME   │  │ - NO_AUTO_EXPLOIT│             │
│  │ - REIMPL_DATE   │  │ - AUDIT_REQUIRED │             │
│  └─────────────────┘  │ - NO_SCORING     │             │
│                       └─────────────────┘              │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │    Version      │  │ Security Const  │              │
│  │ - VERSION       │  │ - MAX_TIMEOUT   │              │
│  │ - VERSION_TUPLE │  │ - REQUIRE_HUMAN │              │
│  └─────────────────┘  └─────────────────┘              │
│                                                         │
│  ┌─────────────────────────────────────────┐           │
│  │           Governance Markers            │           │
│  │ - GOVERNANCE_VERSION                    │           │
│  │ - REIMPLEMENTATION_MARKER               │           │
│  └─────────────────────────────────────────┘           │
│                                                         │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
              [CONSUMED BY PHASES 2-14, 18, 25]
```

---

## 2. Module Structure

```
phase01_core/
├── __init__.py              # Re-exports all constants
├── constants.py             # All constant definitions
├── tests/
│   ├── __init__.py
│   └── test_phase01_constants.py
├── PHASE01_GOVERNANCE_OPENING.md
├── PHASE01_REQUIREMENTS.md
├── PHASE01_TASK_LIST.md
├── PHASE01_IMPLEMENTATION_AUTHORIZATION.md
├── PHASE01_DESIGN.md        # (this document)
└── PHASE01_GOVERNANCE_FREEZE.md
```

---

## 3. Data Flow

**Import Flow (Read-Only):**

```
[External Module]
       │
       ▼
from phase01_core import SYSTEM_ID, INVARIANT_HUMAN_AUTHORITY
       │
       ▼
[Read-only access to constants]
       │
       ▼
[NO MUTATION POSSIBLE]
```

---

## 4. Interfaces

### 4.1 Public API

| Constant | Type | Value | Description |
|----------|------|-------|-------------|
| `SYSTEM_ID` | `str` | UUID | Unique system identifier |
| `SYSTEM_NAME` | `str` | "kali-mcp-toolkit" | System name |
| `REIMPLEMENTATION_DATE` | `str` | "2026-01-20" | Re-implementation date |
| `VERSION` | `str` | "1.0.0" | Semantic version |
| `VERSION_TUPLE` | `tuple[int,int,int]` | (1, 0, 0) | Version as tuple |
| `INVARIANT_HUMAN_AUTHORITY` | `bool` | True | Human must authorize |
| `INVARIANT_NO_AUTO_EXPLOIT` | `bool` | True | No auto exploitation |
| `INVARIANT_AUDIT_REQUIRED` | `bool` | True | Audit trail required |
| `INVARIANT_NO_SCORING` | `bool` | True | No scoring/ranking |
| `MAX_OPERATION_TIMEOUT_SECONDS` | `int` | 300 | Max operation timeout |
| `REQUIRE_HUMAN_CONFIRMATION` | `bool` | True | Human confirmation required |
| `GOVERNANCE_VERSION` | `str` | "2026.1" | Governance version |
| `REIMPLEMENTATION_MARKER` | `str` | "REIMPL-2026" | Marker for re-impl |

### 4.2 Type Hints

All constants will use `typing.Final` to enforce immutability at the type level.

---

## 5. Security Assumptions

1. **Import-time Safety:** No code executes on import beyond constant definition
2. **No Secrets:** No secrets, keys, or credentials in constants
3. **Read-Only:** All values are immutable after module load
4. **No External Dependencies:** No third-party libraries required

---

## 6. Failure Modes

| Failure | Mitigation |
|---------|------------|
| Attempt to modify constant | `Final` type hint + tests verify immutability |
| Missing constant | Tests verify all required constants exist |
| Wrong type | Type hints + runtime type checks in tests |
| Import side effects | Tests verify no side effects on import |

---

## 7. Testing Strategy

1. **Existence Tests:** Verify all constants are defined
2. **Value Tests:** Verify constants have correct values
3. **Type Tests:** Verify constants have correct types
4. **Immutability Tests:** Verify constants cannot be modified
5. **No Side Effects:** Verify module import has no side effects
6. **Invariant Tests:** Verify all invariants are True

---

**NO CODE FOLLOWS IN THIS DOCUMENT — IMPLEMENTATION IS SEPARATE**

---

**END OF DESIGN**
