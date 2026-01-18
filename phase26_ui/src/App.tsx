import React, { useState } from 'react';
import ReactDOM from 'react-dom/client';
import { StatusBanner } from './components/governance/StatusBanner';
import { CVEPanel } from './components/panels/CVEPanel';
import { SubmissionPanel } from './components/panels/SubmissionPanel';
import { TargetPanel } from './components/panels/TargetPanel';
import './index.css';

const App = () => {
    const [activeTab, setActiveTab] = useState<'submit' | 'report'>('submit');

    return (
        <div className="app-container">
            {/* Sidebar - Fixed Heavy Column */}
            {/* Sidebar - Fixed Heavy Column */}
            <aside className="panel" style={{ width: '64px', borderRadius: 0, borderTop: 0, borderBottom: 0, borderLeft: 0, zIndex: 50 }}>
                <div className="flex flex-col items-center gap-md py-md">
                    <div
                        className={`card text-center text-label flex items-center justify-center cursor-pointer hover-scale ${activeTab === 'submit' ? 'bg-card-hover border-strong text-primary' : 'text-tertiary'}`}
                        style={{ width: '40px', height: '40px', cursor: 'pointer', transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)' }}
                        onClick={() => setActiveTab('submit')}
                        title="Submission Interface"
                    >
                        DB
                    </div>
                    {/* Log Icon - Removed Opacity, used CheckBox style */}
                    <div className="card text-center text-label flex items-center justify-center cursor-not-allowed" style={{ width: '40px', height: '40px', color: 'var(--text-tertiary)', borderColor: 'transparent' }}>LG</div>

                    {/* New Report/Session Icon */}
                    <div
                        className={`card text-center text-label flex items-center justify-center cursor-pointer hover-scale ${activeTab === 'report' ? 'bg-card-hover border-strong text-primary' : 'text-tertiary'}`}
                        style={{ width: '40px', height: '40px', cursor: 'pointer', transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)' }}
                        onClick={() => setActiveTab('report')}
                        title="Target Session"
                    >
                        RP
                    </div>

                    <div className="mt-auto"></div>
                    <div className="card text-center text-label text-error flex items-center justify-center" style={{ width: '40px', height: '40px', borderColor: 'var(--status-error)' }}>⚠</div>
                </div>
            </aside>

            {/* Main Content Area */}
            <main className="main-layout flex-col">
                <StatusBanner />

                <div className="flex gap-md flex-1 overflow-hidden relative">
                    {/* Primary Task Area */}
                    <div className="panel flex-1 p-md gap-md animate-fade-in">
                        {activeTab === 'submit' ? <SubmissionPanel /> : <TargetPanel />}
                    </div>

                    {/* Secondary Info Column */}
                    <div className="flex flex-col gap-md" style={{ width: '380px' }}>
                        <div className="panel flex-1 p-md overflow-hidden">
                            <h3 className="text-h3 mb-md">Vulnerability Reference</h3>
                            <CVEPanel />
                        </div>
                        <div className="panel p-md" style={{ height: '30%' }}>
                            <h3 className="text-h3 mb-sm">System Logs</h3>
                            <div className="text-mono text-xs" style={{ color: 'var(--status-success)', opacity: 0.8 }}>
                                [SYSTEM] Phase-26 Governance Active<br />
                                [AUDIT]  64/64 Integrity Checks Passed<br />
                                [USER]   Session Authenticated<br />
                                [NET]    Proxy: Active (8029)
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);
