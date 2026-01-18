# Cyfer Brain Architecture Guard

## CRITICAL: Phase Separation

**Phase-1 (MCP - Truth Engine)**: FROZEN - DO NOT MODIFY
- Location: `kali-mcp-toolkit/python/kali_mcp/`
- Location: `kali-mcp-toolkit/src/` (Rust core)
- Status: COMPLETE and LOCKED

**Phase-2 (Cyfer Brain - Exploration Engine)**: This module
- Location: `kali-mcp-toolkit/python/cyfer_brain/`
- Status: COMPLETE

## Architectural Boundaries

### Cyfer Brain MUST NOT:
1. Classify findings (MCP's responsibility)
2. Generate proofs (MCP's responsibility)
3. Compute confidence (MCP's responsibility)
4. Override MCP classifications
5. Auto-submit reports
6. Modify any file in `kali_mcp/` or `src/`

### Cyfer Brain CAN:
1. Generate hypotheses
2. Explore state space
3. Execute tools (outputs are UNTRUSTED)
4. Submit observations to MCP
5. React to MCP classifications
6. Manage exploration boundaries

## Test Policy

### Hypothesis Settings
- `deadline=None` for tests involving sleep/backoff
- `deadline=5000` for standard property tests
- `max_examples=100` for thorough coverage

### Warning Policy
- All datetime usage must be timezone-aware (`datetime.now(timezone.utc)`)
- No `datetime.utcnow()` - it is deprecated

## Modification Rules

Before modifying any file:
1. Check if it's in `kali_mcp/` or `src/` → DO NOT MODIFY
2. Check if change adds classification logic → REJECT
3. Check if change adds confidence computation → REJECT
4. Check if change bypasses MCP → REJECT

## Phase-2 Status: CLOSED

All tasks complete. 155 tests passing. No architectural violations.
