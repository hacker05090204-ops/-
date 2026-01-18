# Phase-6 Architecture Document

## Overview

Phase-6 provides a human-in-the-loop decision interface for reviewing Phase-5 scanner signals and MCP classifications. The system captures human decisions with full audit logging, enforces role-based access control (Operator vs Reviewer), and maintains strict architectural boundaries that prevent any automation of decision-making.

## Design Principles

1. **Human Authority** — All decisions require explicit human action
2. **Immutability** — Input data (Phase-5, MCP) is read-only; audit log is append-only
3. **Role Separation** — Operators triage, Reviewers approve/reject
4. **Audit Everything** — Every action logged with cryptographic chain integrity
5. **Fail Safe** — Audit failures cause HARD STOP; no silent errors

## System Boundary Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PHASE-6 BOUNDARY                                  │
│                      (Human Decision Workflow)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   Session   │    │   Review    │    │  Decision   │    │   Audit     │  │
│  │   Manager   │───>│   Queue     │───>│   Capture   │───>│   Logger    │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│        │                  │                  │                  │           │
│        │                  │                  │                  │           │
│        ▼                  ▼                  ▼                  ▼           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │    Role     │    │   Finding   │    │   Human     │    │   Audit     │  │
│  │  Enforcer   │    │  Presenter  │    │  Decision   │    │   Entry     │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  INPUTS (READ-ONLY):                                                        │
│  ├── Phase-5 ScanResult (signals, finding candidates)                       │
│  └── MCP Classifications (vulnerability types, confidence scores)           │
│                                                                             │
│  OUTPUTS (APPEND-ONLY):                                                     │
│  ├── HumanDecision records                                                  │
│  ├── AuditEntry chain                                                       │
│  └── DecisionReport exports                                                 │
│                                                                             │
│  FORBIDDEN (raises ArchitecturalViolationError):                            │
│  ├── auto_classify(), auto_severity(), auto_submit()                        │
│  ├── trigger_execution(), trigger_scan()                                    │
│  └── make_network_request()                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Module Structure

```
decision_workflow/
├── __init__.py          # Public exports
├── types.py             # Frozen dataclasses, enums
├── errors.py            # Error hierarchy
├── roles.py             # RoleEnforcer
├── audit.py             # AuditLogger with hash chain
├── session.py           # SessionManager
├── queue.py             # ReviewQueue
├── decisions.py         # DecisionCapture
├── boundaries.py        # BoundaryGuard
└── tests/               # Test suite
```

## Components

### 1. SessionManager (`session.py`)

Handles authentication and session lifecycle.

```python
class SessionManager:
    def authenticate(credentials: Credentials) -> ReviewSession
    def validate_session(session: ReviewSession) -> bool
    def require_valid_session(session: ReviewSession) -> None
    def end_session(session: ReviewSession) -> None
```

**Key Invariants:**
- Session lifecycle is derived from audit events, not stored
- Sessions are immutable (frozen dataclass)
- Session expiry checked against audit log timestamps

### 2. RoleEnforcer (`roles.py`)

Enforces Operator vs Reviewer permissions.

```python
class RoleEnforcer:
    def check_permission(session: ReviewSession, action: Action) -> None
    def get_allowed_actions(role: Role) -> set[Action]
    def can_perform(session: ReviewSession, action: Action) -> bool
```

**Role Permissions:**

| Action | Operator | Reviewer |
|--------|----------|----------|
| VIEW_FINDINGS | ✅ | ✅ |
| MARK_REVIEWED | ✅ | ✅ |
| ADD_NOTE | ✅ | ✅ |
| DEFER | ✅ | ✅ |
| ESCALATE | ✅ | ✅ |
| ASSIGN_SEVERITY | ❌ | ✅ |
| APPROVE | ❌ | ✅ |
| REJECT | ❌ | ✅ |

### 3. AuditLogger (`audit.py`)

Maintains immutable, hash-chained audit trail.

```python
class AuditLogger:
    def log(entry: AuditEntry) -> AuditEntry
    def get_chain() -> list[AuditEntry]
    def verify_integrity() -> bool
```

**Key Invariants:**
- Append-only: No updates or deletes
- Hash chain: Each entry contains SHA-256 hash of previous entry
- HARD STOP on failure: AuditLogFailure halts all operations

### 4. ReviewQueue (`queue.py`)

Presents pending findings for human review.

```python
class ReviewQueue:
    def get_pending() -> list[QueueItem]
    def get_item(finding_id: str) -> Optional[QueueItem]
```

**Key Invariants:**
- Phase-5 and MCP data are read-only
- Missing MCP data treated as None (graceful handling)
- QueueItem status derived from audit history

### 5. DecisionCapture (`decisions.py`)

Records human decisions with validation.

```python
class DecisionCapture:
    def make_decision(finding_id: str, decision: DecisionInput) -> HumanDecision
    def export_report() -> DecisionReport
```

**Validation Rules:**
- APPROVE requires severity
- REJECT requires rationale
- DEFER requires defer_reason
- ESCALATE requires escalation_target
- ADD_NOTE requires note
- CVSS score must be in [0.0, 10.0]

### 6. BoundaryGuard (`boundaries.py`)

Enforces architectural constraints via forbidden method stubs.

```python
class BoundaryGuard:
    def auto_classify() -> NoReturn      # FORBIDDEN
    def auto_severity() -> NoReturn      # FORBIDDEN
    def auto_submit() -> NoReturn        # FORBIDDEN
    def trigger_execution() -> NoReturn  # FORBIDDEN
    def trigger_scan() -> NoReturn       # FORBIDDEN
    def make_network_request() -> NoReturn  # FORBIDDEN
```

## Data Models

All data models use `@dataclass(frozen=True)` for immutability.

### Core Types

```python
class Role(Enum):
    OPERATOR = "operator"
    REVIEWER = "reviewer"

class DecisionType(Enum):
    APPROVE, REJECT, DEFER, ESCALATE, MARK_REVIEWED, ADD_NOTE

class Severity(Enum):
    CRITICAL, HIGH, MEDIUM, LOW, INFORMATIONAL

class Action(Enum):
    VIEW_FINDINGS, MARK_REVIEWED, ADD_NOTE, DEFER, ESCALATE,
    ASSIGN_SEVERITY, APPROVE, REJECT
```

### Session and Credentials

```python
@dataclass(frozen=True)
class Credentials:
    user_id: str
    role: Role

@dataclass(frozen=True)
class ReviewSession:
    session_id: str
    reviewer_id: str
    role: Role
    start_time: datetime
    # Note: lifecycle derived from audit events
```

### Decision Records

```python
@dataclass(frozen=True)
class DecisionInput:
    decision_type: DecisionType
    severity: Optional[Severity]
    cvss_score: Optional[float]
    rationale: Optional[str]
    defer_reason: Optional[str]
    escalation_target: Optional[str]
    note: Optional[str]

@dataclass(frozen=True)
class HumanDecision:
    decision_id: str
    finding_id: str
    session_id: str
    reviewer_id: str
    role: Role
    decision_type: DecisionType
    timestamp: datetime
    # ... optional fields
```

### Audit Entry

```python
@dataclass(frozen=True)
class AuditEntry:
    entry_id: str
    timestamp: datetime
    session_id: str
    reviewer_id: str
    role: Role
    action: str
    # ... optional fields
    previous_hash: Optional[str]
    entry_hash: Optional[str]
    
    def compute_hash() -> str  # SHA-256
```

## Error Hierarchy

```python
DecisionWorkflowError (base)
├── AuthenticationError
├── SessionExpiredError
├── InsufficientPermissionError
├── ValidationError
├── AuditLogFailure (HARD STOP)
└── ArchitecturalViolationError (HARD STOP)
```

### Error Handling Strategy

| Error Type | Behavior | Audit Logged |
|------------|----------|--------------|
| AuthenticationError | Return error to user | Yes |
| SessionExpiredError | Require re-auth | Yes |
| InsufficientPermissionError | Block action, return error | Yes |
| ValidationError | Block action, return error | No |
| AuditLogFailure | HARD STOP | N/A |
| ArchitecturalViolationError | HARD STOP | Yes |

## Import Restrictions

The following imports are FORBIDDEN in decision_workflow:

```python
# FORBIDDEN - raises ArchitecturalViolationError at import time
import execution_layer  # Phase-4
import httpx            # Network
import requests         # Network
import aiohttp          # Network
```

## Safety Invariants

### Phase-6 Remains Safe and Bounded

✅ **No Automation** — All decisions require explicit human action
✅ **No Execution** — Cannot trigger Phase-4 browser actions
✅ **No Scanning** — Cannot trigger Phase-5 artifact scans
✅ **No Network** — No network libraries imported
✅ **No Classification** — MCP is sole authority
✅ **No Severity Auto-Assignment** — Human must manually select
✅ **Immutable Inputs** — Phase-5 and MCP data are read-only
✅ **Immutable Audit** — Append-only with hash chain integrity
✅ **Role Separation** — Operator cannot approve/reject
✅ **Fail Safe** — Audit failure causes HARD STOP

### Scope Boundaries

Phase-6 is LIMITED to:
1. Presenting Phase-5 signals and MCP classifications to humans
2. Capturing human decisions with validation
3. Enforcing role-based permissions
4. Maintaining immutable audit trail
5. Exporting decision reports (no auto-submission)

Phase-6 does NOT:
1. Execute browser actions (Phase-4's responsibility)
2. Scan artifacts (Phase-5's responsibility)
3. Classify vulnerabilities (MCP's responsibility)
4. Compute confidence scores (MCP's responsibility)
5. Auto-assign severity (Human's responsibility)
6. Auto-submit reports (Human's responsibility)
7. Make network requests (FORBIDDEN)
