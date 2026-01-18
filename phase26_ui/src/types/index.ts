/**
 * Phase-26 UI Types
 * 
 * GOVERNANCE:
 * - Types must reflect Read-Only nature of references
 * - Actions must include HumanInitiation
 */

export interface HumanInitiation {
    human_initiated: true; // Literally must be true
    timestamp: number;
    element_id: string; // The ID of the button clicked
}

export interface Finding {
    id: string;
    title: string;
    description: string;
    severity: string;
    classification: string;
}

export interface CVE {
    id: string;
    description: string;
    references: string[];
    // GOVERNANCE: No "applicable" field allowed
}

export interface LogEntry {
    timestamp: string;
    action: string;
    attribution: "HUMAN" | "SYSTEM";
    details: string;
}

export interface SubmissionRequest {
    finding_id: string;
    reflection: string; // Human intent
    human_confirmation: boolean; // Must be checked
}
