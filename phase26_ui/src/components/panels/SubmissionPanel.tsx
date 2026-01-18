import React, { useState } from 'react';
import { api } from '../../api';
import { ConfirmationModal } from '../common/ConfirmationModal';

export const SubmissionPanel: React.FC = () => {
    const [findingId, setFindingId] = useState("");
    const [reflection, setReflection] = useState("");
    const [showModal, setShowModal] = useState(false);

    const handleSubmitClick = () => {
        if (!findingId || !reflection) return;
        setShowModal(true);
    };

    const handleConfirm = async () => {
        try {
            await api.submitFinding(
                { finding_id: findingId, reflection: reflection, human_confirmation: true },
                { human_initiated: true, timestamp: Date.now(), element_id: 'submission-confirm-btn' }
            );
            setShowModal(false);
            setReflection("");
            alert("Submission Sent via Phase-19");
        } catch (e) {
            alert("Submission Failed: " + String(e));
        }
    };

    return (
        <div className="flex flex-col h-full animate-slide-up">
            <div className="flex items-center justify-between mb-lg pb-md" style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                <h2 className="text-h2">Submission Interface</h2>
                <span className="text-label text-tertiary">SECURE CHANNEL</span>
            </div>

            <div className="flex flex-col gap-lg flex-1">
                {/* Finding ID Input */}
                <div className="flex flex-col gap-sm">
                    <label className="text-label">Finding Identifier</label>
                    <input
                        className="card text-body"
                        style={{ padding: '12px', outline: 'none', color: 'var(--text-primary)' }}
                        value={findingId}
                        onChange={(e) => setFindingId(e.target.value)}
                        placeholder="e.g. CVE-2024-XXXX"
                    />
                </div>

                {/* Reflection Textarea */}
                <div className="flex flex-col gap-sm flex-1">
                    <label className="text-label">Reflection & Intent</label>
                    <textarea
                        className="card text-body flex-1 scroll-y"
                        style={{ padding: '12px', outline: 'none', resize: 'none', color: 'var(--text-primary)' }}
                        value={reflection}
                        onChange={(e) => setReflection(e.target.value)}
                        placeholder="Describe the validity of this finding and your verification intent..."
                    />
                </div>

                {/* Action Bar */}
                <div className="pt-md" style={{ borderTop: '1px solid var(--border-subtle)' }}>
                    <button
                        onClick={handleSubmitClick}
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
                        INITIATE SUBMISSION
                    </button>
                </div>
            </div>

            <ConfirmationModal
                isOpen={showModal}
                title="CONFIRM SUBMISSION"
                message="This action requires human authorization. You are submitting this finding to the immutable ledger."
                onConfirm={handleConfirm}
                onCancel={() => setShowModal(false)}
            />
        </div>
    );
};
