# Phase-4 Execution Layer Limitations

## Status: HARDENED

**Date**: December 31, 2025  
**Version**: 1.0.0  
**Authority**: Security Engineering

---

## FORMAL DECLARATION

This document explicitly states all constraints and limitations enforced
by the Phase-4 Execution Layer. These limitations are MANDATORY and
cannot be bypassed.

**This system assists humans. It does not autonomously hunt, judge, or earn.**

---

## FORBIDDEN CAPABILITIES

### ❌ NO Stealth Plugins

The system does NOT use stealth plugins to hide automation.

- No `puppeteer-extra-plugin-stealth`
- No `playwright-stealth`
- No custom stealth scripts
- No WebDriver property masking

**Rationale**: Stealth plugins are deceptive and violate ethical testing principles.

### ❌ NO CAPTCHA Bypass

The system does NOT bypass CAPTCHAs.

- No CAPTCHA solving services
- No machine learning CAPTCHA solvers
- No audio CAPTCHA bypass
- No image recognition bypass

**Rationale**: CAPTCHA bypass violates terms of service and is potentially illegal.

### ❌ NO Fingerprint Spoofing

The system does NOT spoof browser fingerprints.

- No canvas fingerprint manipulation
- No WebGL fingerprint spoofing
- No audio context fingerprint masking
- No font enumeration spoofing
- No navigator property spoofing

**Rationale**: Fingerprint spoofing is deceptive and may violate computer fraud laws.

### ❌ NO Authentication Automation

The system does NOT automate authentication.

- No login automation
- No credential stuffing
- No session hijacking
- No cookie manipulation for auth bypass
- No OAuth flow automation

**Rationale**: Authentication automation without explicit authorization is unauthorized access.

### ❌ NO Evasion of Detection

The system does NOT evade automation detection.

- No bot detection bypass
- No rate limit evasion
- No IP rotation for evasion
- No user-agent rotation for evasion
- No timing randomization for evasion

**Rationale**: Evasion techniques indicate malicious intent.

---

## OBSERVE ONLY CAPABILITIES

### ✅ Automation Detection Awareness

The system OBSERVES automation detection signals but does NOT evade them.

When detection is triggered:
1. Signal is recorded in audit log
2. Execution STOPS immediately
3. Human is alerted
4. NO evasion is attempted

Detected signals include:
- `navigator.webdriver` property
- CAPTCHA presence
- Rate limiting (HTTP 429)
- Bot detection challenges

---

## MANDATORY CONSTRAINTS

### Human Approval Required

Every execution requires explicit human approval via ExecutionToken.

- Tokens are ONE-TIME USE only
- Tokens expire after 15 minutes (configurable)
- Tokens are bound to specific action(s) via hash
- No batch-approve-all capability

### Scope Enforcement

All targets must be within authorized scope.

- Domain must be in authorized list
- Excluded paths are blocked
- Shopify stores require ownership attestation
- No access to admin paths
- No access to checkout paths

### Evidence Integrity

All evidence is cryptographically verified.

- SHA-256 hashes for all artifacts
- Hash-chain linking for tamper evidence
- Manifest verification before MCP submission
- HARD FAIL on hash mismatch

### HTTPS Only

All external communications use HTTPS.

- Non-HTTPS URLs rejected at configuration
- SSL certificates verified by default
- No HTTP fallback

### Response Validation

All API responses are strictly validated.

- Pydantic schema validation
- Missing required fields cause HARD FAIL
- Unexpected fields logged as warnings

### Retry Policy

Network failures are retried with exponential backoff.

- Maximum 3 retries
- Exponential backoff (1s, 2s, 4s)
- No retry on 4xx client errors (except 429)
- HARD FAIL after all retries exhausted

---

## HARD FAIL CONDITIONS

The following conditions cause immediate termination:

1. Scope violation
2. Forbidden action attempted
3. Unsafe action detected
4. Hash chain verification failure
5. Partial evidence capture
6. All retries exhausted
7. Browser crash
8. CSP block
9. Non-HTTPS URL configured
10. Response validation failure

---

## BLOCKING CONDITIONS

The following conditions block until human action:

1. Human approval required
2. Automation detection triggered

---

## AUDIT TRAIL

All actions are recorded in a hash-chained audit log:

- Action type and parameters
- Human approver ID
- Execution outcome
- Evidence bundle ID
- Timestamp
- Previous record hash

---

**END OF LIMITATIONS DOCUMENT**
