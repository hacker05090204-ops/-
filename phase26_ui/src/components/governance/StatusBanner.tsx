import React from 'react';

export const StatusBanner: React.FC = () => {
    return (
        <header className="panel flex-row items-center justify-between px-md" style={{ height: '60px', borderRadius: 'var(--radius-md) var(--radius-md) 0 0', borderBottom: 0 }}>
            {/* Left: Branding */}
            <div className="flex items-center gap-md">
                <div className="flex items-center justify-center bg-card" style={{ width: '32px', height: '32px', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
                    <span className="text-h3 text-primary">K</span>
                </div>
                <div className="flex flex-col">
                    <span className="text-h3 text-primary">Kali Governance</span>
                    <span className="text-label text-tertiary">Phase-26 Control Plane</span>
                </div>
            </div>

            {/* Right: Status Indicators */}
            <div className="flex gap-lg">
                <div className="flex flex-col items-end">
                    <span className="text-label text-tertiary">Authority</span>
                    <span className="text-mono text-success">HUMAN_ACTIVE</span>
                </div>
                <div className="flex flex-col items-end">
                    <span className="text-label text-tertiary">Enforcement</span>
                    <span className="text-mono text-warning">STRICT_BLOCK</span>
                </div>
                <div className="flex flex-col items-end">
                    <span className="text-label text-tertiary">Network</span>
                    <span className="text-mono text-info">PROXY_8029</span>
                </div>
            </div>
        </header>
    );
};
