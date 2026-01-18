/**
 * Phase-29 Evidence Viewer Component
 * 
 * GOVERNANCE:
 * - READ-ONLY display of evidence
 * - "NOT VERIFIED" banner on all evidence
 * - NO interpretation, scoring, or recommendations
 * - Requires human_initiated for all actions
 */

import React, { useState } from 'react';
import { HumanInitiation } from '../../types';
import { browserApi, Evidence, EvidenceItem } from '../../api/browser';

interface EvidenceViewerProps {
    sessionId: string | null;
}

/**
 * Evidence Viewer Panel
 * 
 * GOVERNANCE: Displays evidence READ-ONLY with NOT VERIFIED banner
 */
export const EvidenceViewer: React.FC<EvidenceViewerProps> = ({ sessionId }) => {
    const [evidence, setEvidence] = useState<Evidence | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    /**
     * Fetch evidence - HUMAN INITIATED ONLY
     */
    const handleFetchEvidence = async (e: React.MouseEvent<HTMLButtonElement>) => {
        if (!sessionId) {
            setError('No active session');
            return;
        }

        // GOVERNANCE: Create human initiation from click event
        const initiation: HumanInitiation = {
            human_initiated: true,
            timestamp: Date.now(),
            element_id: e.currentTarget.id || 'fetch-evidence-btn',
        };

        setLoading(true);
        setError(null);

        try {
            const response = await browserApi.getEvidence(sessionId, initiation);
            setEvidence(response.evidence);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch evidence');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="border border-gray-800 bg-gray-900/50 p-4 h-full flex flex-col">
            {/* NOT VERIFIED BANNER - GOVERNANCE REQUIREMENT */}
            <div className="bg-yellow-900/50 border border-yellow-600 text-yellow-400 px-3 py-2 mb-4 text-xs">
                ⚠️ NOT VERIFIED — Evidence is read-only, no interpretation provided
            </div>

            <div className="flex justify-between items-center mb-4 border-b border-gray-800 pb-2">
                <h2 className="text-gray-400">Evidence Viewer</h2>
                <button
                    id="fetch-evidence-btn"
                    onClick={handleFetchEvidence}
                    disabled={!sessionId || loading}
                    className="px-3 py-1 text-xs bg-gray-800 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed border border-gray-700"
                >
                    {loading ? 'Loading...' : 'Refresh Evidence'}
                </button>
            </div>

            {error && (
                <div className="bg-red-900/50 border border-red-600 text-red-400 px-3 py-2 mb-4 text-xs">
                    {error}
                </div>
            )}

            {!sessionId && (
                <div className="text-gray-500 text-sm">
                    No active session. Start a browser session to view evidence.
                </div>
            )}

            {evidence && (
                <div className="flex-1 overflow-auto space-y-4">
                    {/* Screenshots Section */}
                    <div>
                        <h3 className="text-gray-500 text-xs mb-2">
                            Screenshots ({evidence.screenshots.length})
                        </h3>
                        {evidence.screenshots.length === 0 ? (
                            <div className="text-gray-600 text-xs">No screenshots captured</div>
                        ) : (
                            <div className="space-y-2">
                                {evidence.screenshots.map((item: EvidenceItem, index: number) => (
                                    <div
                                        key={index}
                                        className="bg-gray-800 p-2 text-xs border border-gray-700"
                                    >
                                        <div className="text-gray-400">{item.label}</div>
                                        <div className="text-gray-600">{item.captured_at}</div>
                                        <div className="text-blue-400 truncate">{item.path}</div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* HAR File Section */}
                    <div>
                        <h3 className="text-gray-500 text-xs mb-2">HAR File</h3>
                        {evidence.har_path ? (
                            <div className="bg-gray-800 p-2 text-xs border border-gray-700">
                                <div className="text-blue-400 truncate">{evidence.har_path}</div>
                            </div>
                        ) : (
                            <div className="text-gray-600 text-xs">No HAR file captured</div>
                        )}
                    </div>

                    {/* Video Section */}
                    <div>
                        <h3 className="text-gray-500 text-xs mb-2">Video</h3>
                        {evidence.video_path ? (
                            <div className="bg-gray-800 p-2 text-xs border border-gray-700">
                                <div className="text-blue-400 truncate">{evidence.video_path}</div>
                            </div>
                        ) : (
                            <div className="text-gray-600 text-xs">No video captured</div>
                        )}
                    </div>

                    {/* Console Logs Section */}
                    <div>
                        <h3 className="text-gray-500 text-xs mb-2">
                            Console Logs ({evidence.console_logs.length})
                        </h3>
                        {evidence.console_logs.length === 0 ? (
                            <div className="text-gray-600 text-xs">No console logs captured</div>
                        ) : (
                            <div className="space-y-1 max-h-32 overflow-auto">
                                {evidence.console_logs.map((log, index) => (
                                    <div
                                        key={index}
                                        className="text-xs font-mono bg-gray-800 px-2 py-1 border-l-2 border-gray-600"
                                    >
                                        <span className="text-gray-500">[{log.type}]</span>{' '}
                                        <span className="text-gray-400">{log.text}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Footer Disclaimer */}
            <div className="mt-4 pt-2 border-t border-gray-800 text-gray-600 text-xs">
                Phase-29 | CONNECTIVITY ONLY | Human Authority Required
            </div>
        </div>
    );
};
