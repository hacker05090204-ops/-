/**
 * Phase-29 Browser API Client
 * 
 * GOVERNANCE:
 * - All methods require human_initiated=true
 * - NO automation, NO background polling
 * - All responses include "NOT VERIFIED" disclaimer
 * - This is CONNECTIVITY ONLY
 */

import { HumanInitiation } from '../types';

// =============================================================================
// TYPES
// =============================================================================

export interface BrowserSessionConfig {
    enable_video?: boolean;
    viewport_width?: number;
    viewport_height?: number;
}

export interface BrowserAction {
    action_type: 'navigate' | 'click' | 'scroll' | 'input_text' | 'screenshot' | 'wait' | 'hover';
    target: string;
    parameters?: Record<string, unknown>;
}

export interface BrowserStartResponse {
    success: boolean;
    session_id: string;
    execution_id: string;
    started_at: string;
    human_initiated: boolean;
    disclaimer: string;
}

export interface BrowserActionResponse {
    success: boolean;
    action_id: string;
    action_type: string;
    executed_at: string;
    result: Record<string, unknown>;
    human_initiated: boolean;
    disclaimer: string;
    error?: string;
}

export interface EvidenceItem {
    path: string;
    captured_at: string;
    label: string;
}

export interface Evidence {
    screenshots: EvidenceItem[];
    har_path: string | null;
    video_path: string | null;
    console_logs: Array<{
        timestamp: string;
        type: string;
        text: string;
    }>;
}

export interface BrowserEvidenceResponse {
    success: boolean;
    session_id: string;
    evidence: Evidence;
    human_initiated: boolean;
    disclaimer: string;
}

export interface BrowserStopResponse {
    success: boolean;
    session_id: string;
    stopped_at: string;
    evidence_summary: {
        screenshot_count: number;
        har_captured: boolean;
        video_captured: boolean;
        console_log_count: number;
    };
    human_initiated: boolean;
    disclaimer: string;
}

export interface BrowserStatusResponse {
    success: boolean;
    session_id: string;
    status: 'active' | 'stopped' | 'error';
    started_at: string | null;
    action_count: number;
    human_initiated: boolean;
    disclaimer: string;
}

// =============================================================================
// API CLIENT
// =============================================================================

/**
 * Phase-29 Browser API Client
 * 
 * GOVERNANCE: All methods require HumanInitiation with human_initiated=true
 */
export const browserApi = {
    /**
     * Start a new browser session
     * 
     * GOVERNANCE: Requires human_initiated=true
     */
    start: async (
        initiation: HumanInitiation,
        config?: BrowserSessionConfig
    ): Promise<BrowserStartResponse> => {
        // GOVERNANCE: Enforce human_initiated
        if (!initiation.human_initiated) {
            throw new Error('GOVERNANCE VIOLATION: human_initiated=true required');
        }

        const response = await fetch('/api/browser/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                human_initiated: true,
                session_config: config || {},
                initiation_metadata: {
                    timestamp: new Date().toISOString(),
                    element_id: initiation.element_id,
                    user_action: 'click',
                },
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to start browser session');
        }

        return response.json();
    },

    /**
     * Execute a browser action
     * 
     * GOVERNANCE: Requires human_initiated=true
     */
    executeAction: async (
        sessionId: string,
        action: BrowserAction,
        initiation: HumanInitiation
    ): Promise<BrowserActionResponse> => {
        // GOVERNANCE: Enforce human_initiated
        if (!initiation.human_initiated) {
            throw new Error('GOVERNANCE VIOLATION: human_initiated=true required');
        }

        const response = await fetch('/api/browser/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                human_initiated: true,
                session_id: sessionId,
                action,
                initiation_metadata: {
                    timestamp: new Date().toISOString(),
                    element_id: initiation.element_id,
                    user_action: 'click',
                },
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to execute action');
        }

        return response.json();
    },

    /**
     * Get evidence for a session
     * 
     * GOVERNANCE: Requires human_initiated=true, read-only
     */
    getEvidence: async (
        sessionId: string,
        initiation: HumanInitiation
    ): Promise<BrowserEvidenceResponse> => {
        // GOVERNANCE: Enforce human_initiated
        if (!initiation.human_initiated) {
            throw new Error('GOVERNANCE VIOLATION: human_initiated=true required');
        }

        const response = await fetch(
            `/api/browser/evidence?session_id=${encodeURIComponent(sessionId)}&human_initiated=true`
        );

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to get evidence');
        }

        return response.json();
    },

    /**
     * Stop a browser session
     * 
     * GOVERNANCE: Requires human_initiated=true
     */
    stop: async (
        sessionId: string,
        initiation: HumanInitiation
    ): Promise<BrowserStopResponse> => {
        // GOVERNANCE: Enforce human_initiated
        if (!initiation.human_initiated) {
            throw new Error('GOVERNANCE VIOLATION: human_initiated=true required');
        }

        const response = await fetch('/api/browser/stop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                human_initiated: true,
                session_id: sessionId,
                initiation_metadata: {
                    timestamp: new Date().toISOString(),
                    element_id: initiation.element_id,
                    user_action: 'click',
                },
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to stop session');
        }

        return response.json();
    },

    /**
     * Get session status
     * 
     * GOVERNANCE: Requires human_initiated=true, read-only
     */
    getStatus: async (
        sessionId: string,
        initiation: HumanInitiation
    ): Promise<BrowserStatusResponse> => {
        // GOVERNANCE: Enforce human_initiated
        if (!initiation.human_initiated) {
            throw new Error('GOVERNANCE VIOLATION: human_initiated=true required');
        }

        const response = await fetch(
            `/api/browser/status?session_id=${encodeURIComponent(sessionId)}&human_initiated=true`
        );

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to get status');
        }

        return response.json();
    },
};
