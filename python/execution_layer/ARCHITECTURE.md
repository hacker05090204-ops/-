# Execution Layer Architecture Guard

## CRITICAL: This System Assists Humans. It Does Not Autonomously Hunt, Judge, or Earn.

**Phase-1 (MCP - Truth Engine)**: READ-ONLY - DO NOT MODIFY
- Location: `kali-mcp-toolkit/python/kali_mcp/`
- Location: `kali-mcp-toolkit/src/` (Rust core)
- Status: FROZEN

**Phase-2 (Cyfer Brain - Exploration Engine)**: READ-ONLY - DO NOT MODIFY
- Location: `kali-mcp-toolkit/python/cyfer_brain/`
- Status: FROZEN

**Phase-3 (Bounty Pipeline - Submission Engine)**: READ-ONLY - DO NOT MODIFY
- Location: `kali-mcp-toolkit/python/bounty_pipeline/`
- Status: FROZEN

**Phase-4 (Execution Layer - This Module)**: FROZEN
- Location: `kali-mcp-toolkit/python/execution_layer/`
- Status: FROZEN (Hardening v1 FINAL)

## Architectural Boundaries

### Execution Layer MUST NOT:
1. Classify vulnerabilities (MCP's responsibility)
2. Generate proofs (MCP's responsibility)
3. Compute confidence scores (MCP's responsibility)
4. Submit reports (human's responsibility)
5. Bypass human approval
6. Execute forbidden actions (auth bypass, CAPTCHA bypass, etc.)
7. Modify any file in `kali_mcp/`, `cyfer_brain/`, `bounty_pipeline/`, or `src/`

### Execution Layer CAN:
1. Execute SAFE actions with human approval
2. Capture evidence (HAR, screenshots, logs, trace)
3. Record video PoC for MCP-confirmed BUG only
4. Send evidence to MCP for verification (read-only)
5. Create draft reports via Bounty Pipeline (draft only)
6. Maintain execution audit log

## Safe Action Allow-List

Only these actions are allowed:
- `NAVIGATE` - Navigate to URL
- `CLICK` - Click element
- `INPUT_TEXT` - Input non-sensitive text
- `SCROLL` - Scroll page
- `WAIT` - Wait for element/time
- `SCREENSHOT` - Capture screenshot
- `GET_TEXT` - Get element text
- `GET_ATTRIBUTE` - Get element attribute
- `HOVER` - Hover over element
- `SELECT_OPTION` - Select dropdown option

## Forbidden Action List (HARD STOP)

These actions cause immediate HARD STOP:
- `LOGIN` / `AUTHENTICATE` - No auth automation
- `CREATE_ACCOUNT` / `DELETE_ACCOUNT` - No account automation
- `MODIFY_DATA` / `DELETE_DATA` - No data modification
- `BYPASS_CAPTCHA` / `BYPASS_AUTH` - No bypass attempts
- `SUBMIT_FORM` - Could modify data
- `UPLOAD_FILE` / `DOWNLOAD_FILE` - File operations
- `EXECUTE_SCRIPT` - Arbitrary code execution
- `IMPERSONATE` - No impersonation
- `ACCESS_ADMIN` - No admin access
- `PAYMENT` / `CHECKOUT` - No payment operations

## Human Approval Requirements

### MANDATORY Human Approval Points:
1. Before ANY action execution
2. For store ownership attestation (Shopify)
3. For duplicate confirmation decisions
4. For video PoC generation escalation

### ExecutionToken Rules:
- Tokens are ONE-TIME USE only
- Tokens EXPIRE after 15 minutes (single) or 30 minutes (batch)
- Tokens are TIED to specific action(s) via hash
- Modified actions require NEW approval
- Batch tokens allow multiple pre-approved safe actions

## Evidence Capture Requirements

### MANDATORY Evidence (Always Captured):
- HAR file of all network traffic
- Screenshots at key steps
- Console logs
- Execution trace

### OPTIONAL Evidence (Off by Default):
- Video recording
  - Enabled ONLY for MCP-confirmed BUG
  - Enabled ONLY for human escalation request

## Video PoC Idempotency Guard

- Only ONE VideoPoC per finding_id
- Attempting to create duplicate raises `VideoPoCExistsError`
- Video recording is OFF by default
- Enable only on MCP BUG or human escalation

## Store Ownership Attestation (Shopify)

- REQUIRED before testing any Shopify store
- Human must attest they own/control the store
- Attestations expire after 30 days
- Missing attestation raises `StoreAttestationRequired`

## Duplicate Exploration STOP Conditions

- `max_depth`: Maximum exploration depth (default: 3)
- `max_hypotheses`: Maximum hypotheses to generate (default: 5)
- `max_total_actions`: Maximum total actions (default: 20)
- Exceeding any limit raises `DuplicateExplorationLimitError`

## Audit Trail Requirements

### Every Action MUST Be Recorded:
- Timestamp
- Action type
- Actor (human approver ID)
- Action details
- Outcome
- Evidence bundle ID
- Approval token ID

### Audit Trail Properties:
- APPEND-ONLY (no deletions)
- HASH-CHAINED (tamper-evident)
- IMMUTABLE (no modifications)

## Error Handling

### HARD STOP Errors (Refuse to Proceed):
- `ScopeViolationError` - Outside legal scope
- `UnsafeActionError` - Not in SAFE_ACTIONS
- `ForbiddenActionError` - In FORBIDDEN_ACTIONS
- `ArchitecturalViolationError` - Boundary violation
- `AuditIntegrityError` - Audit tampering detected
- `StoreAttestationRequired` - Missing store attestation

### Blocking Errors (Wait for Human):
- `HumanApprovalRequired` - Awaiting approval

### Recoverable Errors (Retry/Request New):
- `TokenExpiredError` - Request new approval
- `TokenAlreadyUsedError` - Request new approval
- `TokenMismatchError` - Request new approval
- `EvidenceCaptureError` - Retry capture
- `BrowserSessionError` - Retry with new session
- `VideoPoCExistsError` - Use existing PoC
- `DuplicateExplorationLimitError` - Stop exploration

## Test Policy

### Required Test Coverage:
- HARD FAIL execution without human approval
- HARD FAIL forbidden actions
- HARD FAIL scope violations
- HARD FAIL store attestation missing
- Verify token single-use enforcement
- Verify token expiry
- Verify batch approval logic
- Verify video idempotency guard
- Verify duplicate exploration STOP conditions
- Verify audit immutability (hash chain)
- Verify throttle enforcement (per-host rate limiting)
- Verify disk retention and pruning
- Verify headless override guardrail

### Hypothesis Settings:
- `deadline=5000` for standard property tests
- `max_examples=100` for thorough coverage

### Warning Policy:
- All datetime usage must be timezone-aware (`datetime.now(timezone.utc)`)
- No `datetime.utcnow()` - it is deprecated

## Risk Mitigations (MANDATORY)

### 1. Per-Host Throttling (REQUIRED)

**Configuration**: `ExecutionThrottleConfig`
- `min_delay_per_action_seconds`: Minimum delay between actions (default: 2.0s)
- `max_actions_per_host_per_minute`: Maximum actions per host per minute (default: 10)
- `burst_allowance`: Allow burst of actions before throttling (default: 3)

**Enforcement**:
- HARD FAIL if config is missing or invalid
- HARD FAIL if rate limit exceeded (`ThrottleLimitExceededError`)
- All throttle decisions logged in audit trail

### 2. Disk Retention & Safety (REQUIRED)

**Configuration**: `EvidenceRetentionPolicy`
- `max_total_disk_mb`: Maximum total disk usage (default: 5000MB = 5GB)
- `max_artifacts_per_execution`: Maximum artifacts per execution (default: 100)
- `ttl_days`: Time-to-live for artifacts (default: 30 days)
- `warning_threshold_percent`: Warn at this usage % (default: 80%)
- `critical_threshold_percent`: HARD FAIL at this usage % (default: 95%)

**Enforcement**:
- Auto-prune expired artifacts before each execution
- HARD FAIL if disk exceeds critical threshold (`DiskRetentionError`)
- All pruning operations logged in audit trail

### 3. Headless Override Guardrail (REQUIRED)

**Default**: `headless=True` (MANDATORY)

**Override Requirements**:
- Setting `headless=False` requires `headless_override_approved=True`
- HARD FAIL without explicit approval (`HeadlessOverrideError`)
- HIGH-RISK warning emitted in audit log when override is used

**Rationale**:
- Non-headless mode exposes browser UI
- Increases detection risk
- Should only be used for debugging with explicit acknowledgment

## FORBIDDEN (NO EXCEPTIONS)

- NO stealth plugins
- NO CAPTCHA bypass
- NO fingerprint spoofing
- NO authentication automation
- NO evasion of detection

## Operational Risk Status

**Status**: Operational risks reduced to LOW

**Mitigations Implemented**:
1. ✅ Per-host throttling with configurable limits
2. ✅ Disk retention with auto-pruning
3. ✅ Headless override guardrail
4. ✅ All mitigations logged to audit trail
5. ✅ HARD FAIL on configuration errors
6. ✅ No mocks in production paths

## Governance: Code-Enforced vs Operator Responsibility

### Code-Enforced Controls (HARD STOP)

The following controls are enforced in code and cause HARD STOP on violation:

| Control | Module | Error | Enforcement |
|---------|--------|-------|-------------|
| Per-host throttling | `throttle.py` | `ThrottleLimitExceededError` | HARD FAIL if rate limit exceeded |
| Throttle config validation | `throttle.py` | `ThrottleConfigError` | HARD FAIL if config missing/invalid |
| Disk retention limits | `retention.py` | `DiskRetentionError` | HARD FAIL at critical threshold (95%) |
| Artifact count limits | `retention.py` | `DiskRetentionError` | HARD FAIL if max_artifacts_per_execution exceeded |
| Headless override | `browser.py` | `HeadlessOverrideError` | HARD FAIL without explicit approval |
| Per-action delay | `browser.py` | N/A | Enforced via `asyncio.sleep()` before each action |

**These controls cannot be bypassed without modifying frozen code.**

### Operator Responsibility (Residual Risk)

The following aspects remain operator responsibility:

1. **Pacing Strategy Selection**: Operators choose throttle config values within code-enforced bounds
   - `min_delay_per_action_seconds`: 0.5s - 60.0s (code-enforced range)
   - `max_actions_per_host_per_minute`: 1 - 60 (code-enforced range)
   - Operators should select conservative values appropriate for target

2. **Long-Term Artifact Monitoring**: Operators should monitor disk usage trends
   - Auto-pruning handles TTL expiration and threshold-based cleanup
   - Operators should review prune logs periodically
   - Operators may call `prune_keep_last_n()` for manual cleanup

3. **Headless Override Decisions**: Operators decide when non-headless mode is appropriate
   - Code requires explicit `headless_override_approved=True`
   - Operators bear responsibility for detection risk when overriding

### Residual Risk Acceptance Statement

**Date**: December 30, 2025

The following residual risks are ACCEPTED under Phase-4 freeze:

1. Operators may select aggressive (but valid) throttle configurations
2. Operators may delay manual artifact cleanup beyond auto-prune
3. Operators may approve headless override for debugging

**Mitigation**: All operator decisions are logged to audit trail. Code-enforced bounds prevent unsafe configurations.

**Risk Level**: LOW (code-enforced controls prevent critical violations)

## Phase-4 Hardening v1 Status

**Status**: FINAL

**Freeze Date**: December 30, 2025

**Test Coverage**: 233 tests

**HARD_STOP_ERRORS**: 12 error types enforced

**Statement**: Phase-4 Hardening v1 is FINAL. No code modifications permitted. Documentation updates for governance clarification do not impact v1 status.
