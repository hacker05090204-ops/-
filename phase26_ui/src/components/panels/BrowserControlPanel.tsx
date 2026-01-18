/**
 * Phase-29 Browser Control Panel
 * 
 * GOVERNANCE:
 * - All actions require explicit human click
 * - NO automation, NO auto-run, NO background execution
 * - human_initiated=true enforced on all API calls
 */

import React, { useState } from 'react';
import { HumanInitiation } from '../../types';
import { browserApi, BrowserAction } from '../../api/browser';

interface BrowserControlPanelProps {
    onSessionChange: (sessionId: string | null) => void;
}

/**
 * Browser Control Panel
 * 
 * GOVERNANCE: All buttons require explicit human click
 */
export const BrowserControlPanel: React.FC<BrowserControlPanelProps> = ({
    onSessionChange,
}) => {
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [status, setStatus] = useState<'idle' | 'active' | 'stopped'>('idle');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [actionLog, setActionLog] = useState<string[]>([]);

    // Action form state
    const [actionType, setActionType] = useState<BrowserAction['action_type']>('navigate');
    const [target, setTarget] = useState('');

    /**
     * Create human initiation from click event
     * GOVERNANCE: Tracks the human action that triggered the request
     */
    const createInitiation = (e: React.MouseEvent<HTMLButtonElement>): HumanInitiation => ({
        human_initiated: true,
        timestamp: Date.now(),
        element_id: e.currentTarget.id || 'unknown-btn',
    });

    /**
     * Add entry to action log
     */
    const log = (message: string) => {
        setActionLog((prev) => [
            `[${new Date().toLocaleTimeString()}] ${message}`,
            ...prev.slice(0, 19), // Keep last 20 entries
        ]);
    };

    /**
     * Start browser session - HUMAN INITIATED ONLY
     */
    const handleStart = async (e: React.MouseEvent<HTMLButtonElement>) => {
        const initiation = createInitiation(e);
        setLoading(true);
        setError(null);

        try {
            log('Starting browser session...');
            const response = await browserApi.start(initiation, {
                enable_video: false,
            });
            setSessionId(response.session_id);
            setStatus('active');
            onSessionChange(response.session_id);
            log(`Session started: ${response.session_id.slice(0, 8)}...`);
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Failed to start';
            setError(message);
            log(`ERROR: ${message}`);
        } finally {
            setLoading(false);
        }
    };

    /**
     * Execute action - HUMAN INITIATED ONLY
     */
    const handleExecuteAction = async (e: React.MouseEvent<HTMLButtonElement>) => {
        if (!sessionId || !target) {
            setError('Session and target required');
            return;
        }

        const initiation = createInitiation(e);
        setLoading(true);
        setError(null);

        const action: BrowserAction = {
            action_type: actionType,
            target,
            parameters: {},
        };

        try {
            log(`Executing ${actionType} on ${target}...`);
            const response = await browserApi.executeAction(sessionId, action, initiation);
            log(`Action completed: ${response.action_id.slice(0, 8)}...`);
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Action failed';
            setError(message);
            log(`ERROR: ${message}`);
        } finally {
            setLoading(false);
        }
    };

    /**
     * Stop browser session - HUMAN INITIATED ONLY
     */
    const handleStop = async (e: React.MouseEvent<HTMLButtonElement>) => {
        if (!sessionId) return;

        const initiation = createInitiation(e);
        setLoading(true);
        setError(null);

        try {
            log('Stopping browser session...');
            const response = await browserApi.stop(sessionId, initiation);
            setStatus('stopped');
            log(`Session stopped. Screenshots: ${response.evidence_summary.screenshot_count}`);
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Failed to stop';
            setError(message);
            log(`ERROR: ${message}`);
        } finally {
            setLoading(false);
        }
    };

    /**
     * Reset panel state
     */
    const handleReset = () => {
        setSessionId(null);
        setStatus('idle');
        setError(null);
        setTarget('');
        onSessionChange(null);
        log('Panel reset');
    };

    return (
        <div className="border border-gray-800 bg-gray-900/50 p-4 h-full flex flex-col">
            {/* NOT VERIFIED BANNER */}
            <div className="bg-yellow-900/50 border border-yellow-600 text-yellow-400 px-3 py-2 mb-4 text-xs">
                ⚠️ NOT VERIFIED — Browser execution for evidence capture only
            </div>

            <h2 className="text-gray-400 mb-4 border-b border-gray-800 pb-2">
                Browser Control
            </h2>

            {/* Status Display */}
            <div className="mb-4 flex items-center gap-2">
                <span className="text-gray-500 text-xs">Status:</span>
                <span
                    className={`text-xs px-2 py-1 rounded ${
                        status === 'active'
                            ? 'bg-green-900/50 text-green-400'
                            : status === 'stopped'
                            ? 'bg-red-900/50 text-red-400'
                            : 'bg-gray-800 text-gray-400'
                    }`}
                >
                    {status.toUpperCase()}
                </span>
                {sessionId && (
                    <span className="text-gray-600 text-xs">
                        ({sessionId.slice(0, 8)}...)
                    </span>
                )}
            </div>

            {/* Error Display */}
            {error && (
                <div className="bg-red-900/50 border border-red-600 text-red-400 px-3 py-2 mb-4 text-xs">
                    {error}
                </div>
            )}

            {/* Session Controls */}
            <div className="mb-4 flex gap-2">
                <button
                    id="start-browser-btn"
                    onClick={handleStart}
                    disabled={loading || status === 'active'}
                    className="px-4 py-2 text-xs bg-green-900/50 hover:bg-green-800/50 disabled:opacity-50 disabled:cursor-not-allowed border border-green-700"
                >
                    Start Session
                </button>
                <button
                    id="stop-browser-btn"
                    onClick={handleStop}
                    disabled={loading || status !== 'active'}
                    className="px-4 py-2 text-xs bg-red-900/50 hover:bg-red-800/50 disabled:opacity-50 disabled:cursor-not-allowed border border-red-700"
                >
                    Stop Session
                </button>
                <button
                    id="reset-btn"
                    onClick={handleReset}
                    disabled={loading}
                    className="px-4 py-2 text-xs bg-gray-800 hover:bg-gray-700 disabled:opacity-50 border border-gray-700"
                >
                    Reset
                </button>
            </div>

            {/* Action Form */}
            {status === 'active' && (
                <div className="mb-4 p-3 bg-gray-800/50 border border-gray-700">
                    <h3 className="text-gray-500 text-xs mb-2">Execute Action</h3>
                    <div className="space-y-2">
                        <select
                            value={actionType}
                            onChange={(e) =>
                                setActionType(e.target.value as BrowserAction['action_type'])
                            }
                            className="w-full bg-gray-900 border border-gray-700 text-gray-300 text-xs p-2"
                        >
                            <option value="navigate">Navigate</option>
                            <option value="click">Click</option>
                            <option value="scroll">Scroll</option>
                            <option value="screenshot">Screenshot</option>
                            <option value="input_text">Input Text</option>
                        </select>
                        <input
                            type="text"
                            value={target}
                            onChange={(e) => setTarget(e.target.value)}
                            placeholder={
                                actionType === 'navigate'
                                    ? 'https://example.com'
                                    : '#selector or URL'
                            }
                            className="w-full bg-gray-900 border border-gray-700 text-gray-300 text-xs p-2"
                        />
                        <button
                            id="execute-action-btn"
                            onClick={handleExecuteAction}
                            disabled={loading || !target}
                            className="w-full px-4 py-2 text-xs bg-blue-900/50 hover:bg-blue-800/50 disabled:opacity-50 disabled:cursor-not-allowed border border-blue-700"
                        >
                            Execute Action
                        </button>
                    </div>
                </div>
            )}

            {/* Action Log */}
            <div className="flex-1 overflow-auto">
                <h3 className="text-gray-500 text-xs mb-2">Action Log</h3>
                <div className="bg-gray-900 border border-gray-800 p-2 h-32 overflow-auto font-mono text-xs">
                    {actionLog.length === 0 ? (
                        <div className="text-gray-600">No actions yet</div>
                    ) : (
                        actionLog.map((entry, index) => (
                            <div
                                key={index}
                                className={`${
                                    entry.includes('ERROR')
                                        ? 'text-red-400'
                                        : 'text-green-400'
                                }`}
                            >
                                {entry}
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Footer */}
            <div className="mt-4 pt-2 border-t border-gray-800 text-gray-600 text-xs">
                Phase-29 | Human Click Required | NO Automation
            </div>
        </div>
    );
};
