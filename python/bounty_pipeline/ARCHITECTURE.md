# Bounty Pipeline Architecture Guard

## CRITICAL: This System Assists Humans. It Does Not Replace Them.

**Phase-1 (MCP - Truth Engine)**: FROZEN - DO NOT MODIFY
- Location: `kali-mcp-toolkit/python/kali_mcp/`
- Location: `kali-mcp-toolkit/src/` (Rust core)
- Status: COMPLETE and LOCKED

**Phase-2 (Cyfer Brain - Exploration Engine)**: FROZEN - DO NOT MODIFY
- Location: `kali-mcp-toolkit/python/cyfer_brain/`
- Status: COMPLETE and LOCKED

**Phase-3 (Bounty Pipeline - Submission Engine)**: This module
- Location: `kali-mcp-toolkit/python/bounty_pipeline/`
- Status: IN DEVELOPMENT

## Architectural Boundaries

### Bounty Pipeline MUST NOT:
1. Classify findings (MCP's responsibility)
2. Generate proofs (MCP's responsibility)
3. Compute confidence scores (MCP's responsibility)
4. Submit reports without human approval
5. Bypass human review
6. Auto-earn or predict bounties
7. Modify any file in `kali_mcp/` or `cyfer_brain/` or `src/`

### Bounty Pipeline CAN:
1. Validate findings have MCP proof
2. Validate legal scope
3. Check for duplicates (advisory only)
4. Generate platform-specific reports
5. Request human review
6. Submit AFTER human approval
7. Track submission status
8. Maintain audit trail

## Human Approval Requirements

### MANDATORY Human Approval Points:
1. Before ANY submission to ANY platform
2. For ambiguous scope decisions
3. For potential duplicate decisions
4. For unredacted sensitive data

### Approval Token Rules:
- Tokens are ONE-TIME USE only
- Tokens EXPIRE after 30 minutes (configurable)
- Tokens are TIED to specific draft content
- Modified drafts require NEW approval

## Audit Trail Requirements

### Every Action MUST Be Recorded:
- Timestamp
- Action type
- Actor (system or human ID)
- Outcome
- Links to MCP proof
- Links to Cyfer Brain observation

### Audit Trail Properties:
- APPEND-ONLY (no deletions)
- HASH-CHAINED (tamper-evident)
- IMMUTABLE (no modifications)

## Error Handling

### HARD STOP Errors (Refuse to Proceed):
- `FindingValidationError` - No MCP proof
- `ScopeViolationError` - Outside legal scope
- `AuthorizationExpiredError` - Authorization expired
- `ArchitecturalViolationError` - Boundary violation
- `AuditIntegrityError` - Audit tampering detected

### Blocking Errors (Wait for Human):
- `HumanApprovalRequired` - Awaiting approval

### Recoverable Errors (Retry/Queue):
- `SubmissionFailedError` - Platform API failure
- `PlatformError` - Platform unavailable
- `RecoveryError` - State recovery issue

## Modification Rules

Before modifying any file:
1. Check if it's in `kali_mcp/` or `cyfer_brain/` or `src/` → DO NOT MODIFY
2. Check if change adds classification logic → REJECT
3. Check if change adds confidence computation → REJECT
4. Check if change bypasses human review → REJECT
5. Check if change enables auto-submission → REJECT
6. Check if change enables auto-earning → REJECT

## Test Policy

### Hypothesis Settings
- `deadline=5000` for standard property tests
- `max_examples=100` for thorough coverage

### Warning Policy
- All datetime usage must be timezone-aware (`datetime.now(timezone.utc)`)
- No `datetime.utcnow()` - it is deprecated

### Required Test Coverage
- HARD FAIL submission without MCP proof
- HARD FAIL submission without human approval
- HARD FAIL legal scope violations
- HARD FAIL any attempt to bypass review
- Verify audit immutability (hash chain)
- Verify credentials are encrypted and never logged

## Phase-3 Status: IN DEVELOPMENT

Core components implemented:
- FindingValidator ✓
- LegalScopeValidator ✓
- HumanReviewGate ✓
- ReportGenerator ✓
- AuditTrail ✓
- DuplicateDetector ✓
- BountyPipeline orchestrator ✓
- Platform Adapters (HackerOne, Bugcrowd, Generic) ✓
- SubmissionManager ✓
- StatusTracker ✓
- RecoveryManager ✓
- ProgramManager ✓

Remaining:
- Integration tests
- End-to-end property tests
