# Phase Governance Document

**Authority:** System Architect & Governance Authority  
**Date:** 2025-12-30  
**Document Version:** 1.1

**Revision History:**
| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2025-12-30 | Initial governance document |
| 1.1 | 2025-12-30 | Added Section 6 (Amendment Log) and Section 7 (Human Role Separation) |

---

## 1. PHASE-5 CLOSURE CONFIRMATION

### Status: CLOSED & FROZEN

**Effective Date:** 2025-12-30

### Final State

| Component | Status | Evidence |
|-----------|--------|----------|
| artifact_scanner/ | FROZEN | 138/138 tests passing |
| PHASE5_FREEZE.md | CREATED | Implementation freeze declared |
| ARCHITECTURE.md | CREATED | Boundaries documented |
| Independent Audit | PASSED | Red-team verification complete |

### Immutable Constraints (PERMANENT)

1. **Phase-5 is READ-ONLY** — No artifact modification permitted
2. **Phase-5 is OFFLINE** — No network capabilities exist
3. **Phase-5 is PASSIVE** — No execution, replay, or automation
4. **Phase-5 outputs SIGNALS ONLY** — No severity, classification, or confidence
5. **Phase-4 remains UNTOUCHED** — Execution layer is frozen
6. **MCP remains SOLE TRUTH ENGINE** — Classification authority unchanged

### Forbidden Actions (ENFORCED BY CODE)

The following actions raise `ArchitecturalViolationError`:
- `classify_vulnerability()` — MCP's responsibility
- `assign_severity()` — Human's responsibility
- `compute_confidence()` — MCP's responsibility
- `submit_report()` — Human's responsibility
- `trigger_execution()` — Phase-4's responsibility
- `generate_proof()` — MCP's responsibility

### No Further Features Allowed

Phase-5 is **FEATURE-COMPLETE**. Any enhancement requests MUST be:
1. Rejected if they violate read-only/offline/passive constraints
2. Deferred to a future phase if they require new capabilities
3. Documented as out-of-scope in this governance record

---

## 2. PHASE-6 SCOPE DEFINITION

### Name: Human Decision Workflow

### Purpose

Phase-6 provides a **human-in-the-loop decision interface** that:
- Presents Phase-5 signals and MCP classifications to human reviewers
- Captures human decisions (approve, reject, defer, escalate)
- Logs all decisions with timestamps and rationale for audit
- Does NOT automate any decision-making

### Input Sources

| Source | Data Type | Phase-6 Action |
|--------|-----------|----------------|
| Phase-5 Scanner | `ScanResult` (signals, finding candidates) | Display for review |
| MCP | Classifications, confidence scores | Display for review |
| Human | Decisions, severity assignments, rationale | Capture and log |

### Output

| Output | Destination | Purpose |
|--------|-------------|---------|
| `HumanDecision` | Audit log | Immutable record of human judgment |
| `ReviewSession` | Database | Track review progress |
| `DecisionReport` | Export | Human-readable summary |

### Core Capabilities

1. **Review Queue** — Present pending findings for human review
2. **Decision Capture** — Record approve/reject/defer/escalate with rationale
3. **Severity Assignment** — Human assigns severity (NOT automated)
4. **Audit Trail** — Immutable log of all decisions with timestamps
5. **Session Management** — Track reviewer identity and session state

---

## 3. PHASE-6 NON-GOALS (FORBIDDEN)

### Execution & Automation

| Forbidden Action | Reason |
|------------------|--------|
| Trigger browser actions | Phase-4's responsibility |
| Replay attack sequences | Phase-4's responsibility |
| Execute JavaScript | Phase-4's responsibility |
| Make network requests | Offline principle |
| Modify artifacts | Immutability principle |

### Classification & Scoring

| Forbidden Action | Reason |
|------------------|--------|
| Auto-assign severity | Human's responsibility |
| Auto-classify vulnerabilities | MCP's responsibility |
| Compute confidence scores | MCP's responsibility |
| Generate risk scores | Human's responsibility |
| Prioritize findings automatically | Human's responsibility |

### Submission & Reporting

| Forbidden Action | Reason |
|------------------|--------|
| Auto-submit to bug bounty platforms | Human's responsibility |
| Generate proof-of-concept | MCP's responsibility |
| Create exploit code | FORBIDDEN (safety) |
| Send notifications without human approval | Human's responsibility |

### Scanning & Analysis

| Forbidden Action | Reason |
|------------------|--------|
| Scan artifacts | Phase-5's responsibility |
| Analyze HAR files | Phase-5's responsibility |
| Detect patterns | Phase-5's responsibility |
| Parse console logs | Phase-5's responsibility |

---

## 4. PHASE-6 RISK BOUNDARIES

### Architectural Boundaries

```
┌─────────────────────────────────────────────────────────────────┐
│                        PHASE-6 BOUNDARY                         │
│                   (Human Decision Workflow)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  INPUTS (READ-ONLY):                                           │
│  ├── Phase-5 ScanResult (signals, finding candidates)          │
│  ├── MCP Classifications (vulnerability types)                  │
│  └── MCP Confidence Scores (probability estimates)             │
│                                                                 │
│  HUMAN ACTIONS (CAPTURED):                                     │
│  ├── Approve finding                                           │
│  ├── Reject finding (with rationale)                           │
│  ├── Defer finding (with reason)                               │
│  ├── Escalate finding (to senior reviewer)                     │
│  ├── Assign severity (CVSS or custom)                          │
│  └── Add notes/comments                                        │
│                                                                 │
│  OUTPUTS (AUDIT LOG):                                          │
│  ├── HumanDecision records                                     │
│  ├── ReviewSession metadata                                    │
│  └── DecisionReport exports                                    │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  FORBIDDEN (raises ArchitecturalViolationError):               │
│  ├── auto_classify()                                           │
│  ├── auto_severity()                                           │
│  ├── auto_submit()                                             │
│  ├── trigger_scan()                                            │
│  ├── trigger_execution()                                       │
│  └── make_network_request()                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow Constraints

```
Phase-4 (FROZEN)     Phase-5 (FROZEN)      Phase-6 (NEW)         Human
     │                    │                    │                   │
     │  artifacts         │                    │                   │
     ├───────────────────>│                    │                   │
     │                    │  ScanResult        │                   │
     │                    ├───────────────────>│                   │
     │                    │                    │  Present findings │
     │                    │                    ├──────────────────>│
     │                    │                    │                   │
     │                    │                    │  Human decision   │
     │                    │                    │<──────────────────┤
     │                    │                    │                   │
     │                    │                    │  Log decision     │
     │                    │                    ├──────────────────>│
     │                    │                    │  (audit trail)    │
     │                    │                    │                   │
     X                    X                    │                   │
  NO WRITES           NO WRITES            WRITES TO             FINAL
  TO PHASE-4          TO PHASE-5           AUDIT LOG             AUTHORITY
```

### Safety Invariants

1. **Human is FINAL AUTHORITY** — No automated decision can override human judgment
2. **All decisions are LOGGED** — Immutable audit trail with timestamps
3. **No execution capability** — Phase-6 cannot trigger Phase-4 actions
4. **No scanning capability** — Phase-6 cannot trigger Phase-5 scans
5. **No network capability** — Phase-6 is offline (except audit log persistence)
6. **No classification capability** — Phase-6 displays MCP results, does not generate them

### Error Handling

| Error Type | Behavior |
|------------|----------|
| `DecisionRequiredError` | Block until human provides decision |
| `AuditLogFailure` | HARD STOP — refuse to proceed without audit |
| `SessionExpiredError` | Require re-authentication |
| `ArchitecturalViolationError` | HARD STOP — log violation, alert admin |

---

## 5. AUTHORIZATION

### Phase-5 Closure

I hereby confirm that **Phase-5 (Artifact Scanner)** is:
- ✅ COMPLETE — All 138 tests passing
- ✅ AUDITED — Independent red-team verification passed
- ✅ FROZEN — No further features permitted
- ✅ SAFE — Read-only, offline, passive by design

### Phase-6 Authorization

I hereby authorize the design and implementation of **Phase-6 (Human Decision Workflow)** under the following conditions:

1. **Scope is LIMITED** to human-in-the-loop decision capture
2. **No automation** of severity, classification, or submission
3. **All decisions MUST be logged** with immutable audit trail
4. **Forbidden methods MUST raise** `ArchitecturalViolationError`
5. **Phase-4 and Phase-5 remain FROZEN** and unchanged

### Signatures

```
Authority: System Architect & Governance Authority
Date: 2025-12-30
Decision: PHASE-5 CLOSED, PHASE-6 AUTHORIZED
```

---

## 6. AMENDMENT LOG

| Date | Amendment | Rationale |
|------|-----------|-----------|
| 2025-12-30 | Added Human Role Separation (Section 7) | Reduce human error risk via separation of duties |

### Amendment: Human Role Separation

**Effective Date:** 2025-12-30

**Change Summary:**
- Added Operator role (triage and review)
- Added Reviewer role (severity assignment and final approval)
- Updated Responsibility Matrix to reflect role-based permissions

**Impact Assessment:**
- ✅ No automation introduced
- ✅ No code changes required to Phase-4 or Phase-5
- ✅ Phase-6 scope unchanged (human-in-the-loop only)
- ✅ Reduces human error risk through separation of duties

---

## 7. HUMAN ROLE SEPARATION

### Purpose

To reduce human error risk and enforce separation of duties, Phase-6 defines two distinct human roles with non-overlapping critical permissions.

### Role Definitions

#### Operator Role

| Attribute | Value |
|-----------|-------|
| **Identity** | Authenticated user with `role=operator` |
| **Purpose** | Initial triage and review of findings |
| **Session Type** | Standard review session |

**Permissions:**
- ✅ View pending findings in review queue
- ✅ View Phase-5 signals and MCP classifications
- ✅ Mark findings as "reviewed" (triage complete)
- ✅ Add notes and comments to findings
- ✅ Defer findings (with reason)
- ✅ Escalate findings to Reviewer
- ❌ Assign severity (FORBIDDEN)
- ❌ Approve findings for submission (FORBIDDEN)
- ❌ Reject findings permanently (FORBIDDEN)

#### Reviewer Role

| Attribute | Value |
|-----------|-------|
| **Identity** | Authenticated user with `role=reviewer` |
| **Purpose** | Final authority on severity and approval |
| **Session Type** | Elevated review session |

**Permissions:**
- ✅ All Operator permissions
- ✅ Assign severity (Critical, High, Medium, Low, Informational)
- ✅ Approve findings for submission
- ✅ Reject findings permanently (with rationale)
- ✅ Override Operator decisions (logged)
- ❌ Auto-assign severity (FORBIDDEN — must be manual)
- ❌ Auto-approve findings (FORBIDDEN — must be manual)

### Role Permission Matrix

| Action | Operator | Reviewer | Automation |
|--------|----------|----------|------------|
| View findings | ✅ | ✅ | ❌ |
| View signals/classifications | ✅ | ✅ | ❌ |
| Mark as reviewed | ✅ | ✅ | ❌ |
| Add notes/comments | ✅ | ✅ | ❌ |
| Defer finding | ✅ | ✅ | ❌ |
| Escalate to Reviewer | ✅ | N/A | ❌ |
| Assign severity | ❌ | ✅ | ❌ |
| Approve finding | ❌ | ✅ | ❌ |
| Reject finding | ❌ | ✅ | ❌ |
| Override decisions | ❌ | ✅ | ❌ |

### Enforcement

1. **Role Check on Action** — Each action validates the user's role before execution
2. **InsufficientPermissionError** — Raised when Operator attempts Reviewer-only action
3. **Audit Log Entry** — All role-based denials are logged with timestamp and user identity
4. **No Role Escalation** — Users cannot self-assign Reviewer role

### Risk Reduction

This role separation reduces human error risk by:

1. **Preventing accidental severity assignment** — Operators cannot accidentally assign severity during triage
2. **Requiring deliberate approval** — Only Reviewers can approve, ensuring a second pair of eyes
3. **Enforcing escalation workflow** — Complex findings must be escalated to qualified Reviewers
4. **Creating accountability** — Audit trail shows which role made each decision
5. **Reducing cognitive load** — Operators focus on triage, Reviewers focus on judgment

### No Automation Introduced

This role separation is **documentation and enforcement only**:
- ❌ No automated role assignment
- ❌ No automated severity suggestion
- ❌ No automated approval workflow
- ❌ No automated escalation rules
- ✅ Human assigns roles manually
- ✅ Human makes all decisions manually
- ✅ Human escalates manually when needed

---

## 8. APPENDIX: PHASE SUMMARY

| Phase | Name | Status | Responsibility |
|-------|------|--------|----------------|
| Phase-4 | Execution Layer | FROZEN | Browser automation, artifact generation |
| Phase-5 | Artifact Scanner | FROZEN | Read-only signal extraction |
| Phase-6 | Human Decision Workflow | AUTHORIZED | Human review and decision capture |
| MCP | Truth Engine | ACTIVE | Classification, confidence, proof generation |

### Responsibility Matrix (Updated with Roles)

| Action | Phase-4 | Phase-5 | Phase-6 | MCP | Operator | Reviewer |
|--------|---------|---------|---------|-----|----------|----------|
| Execute browser actions | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Generate artifacts | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Scan artifacts | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Extract signals | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Classify vulnerabilities | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Compute confidence | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Generate proofs | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Present findings | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Capture decisions | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| View/triage findings | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Mark as reviewed | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Defer/escalate | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Assign severity | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Approve/reject findings | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Submit reports | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

---

**END OF GOVERNANCE DOCUMENT**
