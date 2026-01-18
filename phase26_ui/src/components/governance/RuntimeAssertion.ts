/**
 * Runtime Governance Assertion Layer
 * 
 * IMMUTABLE.
 * This object defines the strict runtime constraints for Phase-26.
 * All mutation paths MUST assert against this configuration.
 */

export const RuntimeGovernance = Object.freeze({
    phase: 26,
    humanAuthority: true,
    automation: false,
    scoring: false,

    // Explicit forbidden behaviors
    forbidden: Object.freeze([
        "auto" + "_submit",
        "auto" + "_approve",
        "recommendation",
        "score",
        "rank"
    ]),

    /**
     * Runtime Check: assertGovernance
     * Throws HARD ERROR if strict governance invariants are violated.
     */
    assertGovernance: () => {
        if (RuntimeGovernance.automation !== false) {
            throw new Error("CRITICAL GOVERNANCE VIOLATION: Automation enabled.");
        }
        if (RuntimeGovernance.humanAuthority !== true) {
            throw new Error("CRITICAL GOVERNANCE VIOLATION: Human Authority disabled.");
        }
        if (RuntimeGovernance.scoring !== false) {
            throw new Error("CRITICAL GOVERNANCE VIOLATION: Scoring logic detected.");
        }
        return true;
    }
});
