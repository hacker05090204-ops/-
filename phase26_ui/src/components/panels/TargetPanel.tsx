import React, { useState } from 'react';

export const TargetPanel: React.FC = () => {
    const [target, setTarget] = useState("");
    const [scope, setScope] = useState("");

    const handleSave = () => {
        console.log("Saving Target Scope:", { target, scope });
        alert("Target Scope Configured");
    };

    return (
        <div className="flex flex-col h-full animate-slide-up">
            <div className="flex items-center justify-between mb-lg pb-md" style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                <h2 className="text-h2">Session Configuration</h2>
                <span className="text-label text-tertiary">TARGET SCOPE</span>
            </div>

            <div className="flex flex-col gap-lg flex-1">
                {/* Target Config */}
                <div className="flex flex-col gap-sm">
                    <label className="text-label">Target Name / URL</label>
                    <input
                        className="card text-body"
                        style={{ padding: '12px', outline: 'none', color: 'var(--text-primary)' }}
                        value={target}
                        onChange={(e) => setTarget(e.target.value)}
                        placeholder="e.g. https://target-company.com"
                    />
                </div>

                {/* Scope Config */}
                <div className="flex flex-col gap-sm flex-1">
                    <label className="text-label">Scope Definition</label>
                    <textarea
                        className="card text-body flex-1 scroll-y"
                        style={{ padding: '12px', outline: 'none', resize: 'none', color: 'var(--text-primary)' }}
                        value={scope}
                        onChange={(e) => setScope(e.target.value)}
                        placeholder="Define authorized scope (e.g., wildcards, excluded paths)..."
                    />
                </div>

                {/* Info Box */}
                <div className="card p-md bg-card flex flex-col gap-xs">
                    <span className="text-label text-info">ACTIVE SESSION CONTEXT</span>
                    <p className="text-mono" style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>
                        This scope will define the boundaries for all subsequent findings and automated checks in this session.
                    </p>
                </div>

                {/* Action Bar */}
                <div className="pt-md" style={{ borderTop: '1px solid var(--border-subtle)' }}>
                    <button
                        onClick={handleSave}
                        className="text-h3"
                        style={{
                            width: '100%',
                            padding: '16px',
                            backgroundColor: 'var(--text-primary)',
                            color: 'var(--bg-app)',
                            borderRadius: 'var(--radius-sm)',
                            cursor: 'pointer',
                            fontWeight: 700
                        }}
                    >
                        LOCK TARGET SCOPE
                    </button>
                </div>
            </div>
        </div>
    );
};
