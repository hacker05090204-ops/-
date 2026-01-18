import { HumanInitiation, SubmissionRequest } from '../types';
import { RuntimeGovernance } from '../components/governance/RuntimeAssertion';

/**
 * Phase-26 API Layer
 * 
 * GOVERNANCE:
 * All state-changing methods REQUIRE `HumanInitiation` object.
 * All mutations MUST pass RuntimeGovernance.assertGovernance().
 */

// Simulated backend call (Phase-15/19 shim)
async function transport(endpoint: string, method: string, body: any) {
    console.log(`[Phase26] ${method} ${endpoint}`, body);
    return { success: true };
}

export const api = {
    // READ-ONLY: No human initiation strictly required for reading, 
    // but useful to track who is looking.
    fetchCVEs: async () => {
        return transport('/api/cve', 'GET', {});
    },

    fetchEvidence: async () => {
        return transport('/api/evidence', 'GET', {});
    },

    // ACTION: Human Initiation REQUIRED
    submitFinding: async (
        request: SubmissionRequest,
        initiation: HumanInitiation
    ) => {
        // HARD RUNTIME ASSERTION
        RuntimeGovernance.assertGovernance();

        if (!initiation.human_initiated) {
            throw new Error("GOVERNANCE VIOLATION: Automation detected. Submission blocked.");
        }

        return transport('/api/submission', 'POST', {
            ...request,
            metadata: { initiation }
        });
    },

    // ACTION: Check Enforcer (Phase-15)
    validateInput: async (
        data: any,
        initiation: HumanInitiation
    ) => {
        // HARD RUNTIME ASSERTION
        RuntimeGovernance.assertGovernance();

        if (!initiation.human_initiated) {
            throw new Error("GOVERNANCE VIOLATION: Auto-validation blocked.");
        }
        return transport('/api/validate', 'POST', { data, metadata: { initiation } });
    }
};
