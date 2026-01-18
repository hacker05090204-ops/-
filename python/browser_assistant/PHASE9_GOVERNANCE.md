# Phase-9 Governance Document

## Browser-Integrated Assisted Hunting Layer

**Version**: 1.0.0  
**Status**: ACTIVE  
**Last Updated**: 2025-12-31

---

## 1. Purpose

Phase-9 is an ASSISTIVE layer that reduces human workload to near-negligible effort WITHOUT creating automation, autonomy, or submission authority.

**Core Principle**: Human always clicks YES/NO.

---

## 2. Safety Constraints (NON-NEGOTIABLE)

### 2.1 Forbidden Actions

Phase-9 MUST NEVER:

1. **Execute payloads** - No code execution, no script injection
2. **Inject traffic** - No request modification, no traffic interception
3. **Modify requests** - No tampering with HTTP requests/responses
4. **Classify bugs** - Human decides if something is a vulnerability
5. **Assign severity** - Human assigns severity levels
6. **Submit reports** - Human submits reports manually
7. **Generate PoCs** - No proof-of-concept generation
8. **Record video** - No automated evidence capture
9. **Chain findings** - No automated correlation
10. **Auto-confirm** - Every output requires explicit human confirmation

### 2.2 Allowed Actions

Phase-9 MAY:

1. **Observe** - Passively receive browser activity data
2. **Hint** - Provide contextual reminders and pattern hints
3. **Warn** - Alert about potential duplicates or scope issues
4. **Draft** - Generate editable report templates
5. **Wait** - Require human confirmation for all outputs

---

## 3. Architectural Boundaries

### 3.1 Phase Relationships

| Phase | Access Level | Constraint |
|-------|--------------|------------|
| Phase-4 (Execution Layer) | READ-ONLY | Types only |
| Phase-5 (Artifact Scanner) | READ-ONLY | Types only |
| Phase-6 (Decision Workflow) | READ-ONLY | No writes |
| Phase-7 (Submission Workflow) | READ-ONLY | No writes |
| Phase-8 (Intelligence Layer) | ADVISORY-ONLY | No writes |

### 3.2 Forbidden Imports

```python
# Network execution - PERMANENTLY DISABLED
httpx, requests, aiohttp, socket, urllib.request, urllib3, http.client

# Browser automation - PERMANENTLY DISABLED
selenium, playwright, puppeteer, pyppeteer, splinter, mechanize

# UI automation - PERMANENTLY DISABLED
pyautogui, pynput, keyboard, mouse

# Phase-4 execution modules
execution_layer.controller, execution_layer.actions, execution_layer.browser

# Phase-5 scanner modules
artifact_scanner.scanner, artifact_scanner.analyzers
```

---

## 4. Data Flow

```
Browser Extension → BrowserObserver → ContextAnalyzer → Hints
                                   → DuplicateHintEngine → Warnings
                                   → ScopeChecker → Warnings
                                   → DraftReportGenerator → Drafts
                                   ↓
                         HumanConfirmationGate
                                   ↓
                         Human clicks YES/NO
```

**Critical**: No data flows OUT to external systems. All outputs require human confirmation.

---

## 5. Human Confirmation Requirements

### 5.1 Every Output Requires Confirmation

- Context hints → Human confirms relevance
- Duplicate warnings → Human decides if duplicate
- Scope warnings → Human decides to proceed
- Draft reports → Human reviews, edits, confirms

### 5.2 Confirmation Properties

- **Explicit**: Human must click YES or NO
- **Single-use**: Confirmations cannot be replayed
- **Timestamped**: All confirmations are recorded
- **Hashed**: Integrity verified via SHA-256

---

## 6. Safety Markers

All data models include safety markers that are ALWAYS True:

```python
# BrowserObservation
is_passive_observation = True
no_modification_performed = True

# ContextHint
human_confirmation_required = True
is_advisory_only = True
no_auto_action = True

# DuplicateHint
human_confirmation_required = True
is_heuristic = True
does_not_block = True

# ScopeWarning
human_confirmation_required = True
does_not_block = True
is_advisory_only = True

# DraftReportContent
human_must_review = True
human_must_edit = True
human_must_confirm = True
is_template_only = True
no_auto_submission = True

# AssistantOutput
requires_human_confirmation = True
no_auto_action = True
is_advisory_only = True
```

---

## 7. Compliance Verification

### 7.1 Test Coverage

- 211 tests covering all Phase-9 components
- Forbidden method tests verify no dangerous methods exist
- Safety marker tests verify markers cannot be overridden
- Boundary tests verify forbidden imports/actions are blocked

### 7.2 Audit Requirements

Before any modification to Phase-9:

1. Run full test suite (1330+ tests)
2. Verify no forbidden imports added
3. Verify no forbidden methods added
4. Verify safety markers remain True
5. Document changes in audit log

---

## 8. Modification Policy

### 8.1 Allowed Modifications

- Bug fixes that don't change safety constraints
- Performance improvements
- Additional hint patterns
- UI/UX improvements for human confirmation

### 8.2 Forbidden Modifications

- Adding automation capabilities
- Removing human confirmation requirements
- Adding network execution
- Adding browser control
- Bypassing safety markers

### 8.3 Approval Process

Any modification requires:

1. Code review by security-aware reviewer
2. Full test suite pass
3. Audit report update
4. Governance document update if constraints change

---

## 9. Incident Response

If Phase-9 is found to violate any safety constraint:

1. **IMMEDIATE**: Disable affected functionality
2. **INVESTIGATE**: Determine root cause
3. **FIX**: Implement correction
4. **VERIFY**: Run full test suite
5. **DOCUMENT**: Update audit report
6. **REVIEW**: Assess if governance needs strengthening

---

## 10. Contact

For questions about Phase-9 governance, contact the security team.

**Remember**: Phase-9 is ASSISTIVE ONLY. Human always clicks YES/NO.
