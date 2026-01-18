import React from 'react';

interface Props {
    title: string;
    message: string;
    onConfirm: () => void;
    onCancel: () => void;
    isOpen: boolean;
}

export const ConfirmationModal: React.FC<Props> = ({ title, message, onConfirm, onCancel, isOpen }) => {
    if (!isOpen) return null;

    return (
        <div style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 50,
            backdropFilter: 'blur(2px)' // PREMIUM: Subtle blur
        }}>
            <div style={{
                backgroundColor: 'var(--bg-panel)',
                border: '1px solid var(--status-error)',
                width: '400px',
                padding: 'var(--space-lg)',
                boxShadow: '0 20px 50px rgba(0,0,0,0.5)',
                borderRadius: 'var(--radius-md)'
            }}>
                <h3 className="text-error font-bold mb-sm" style={{ fontSize: '18px' }}>{title}</h3>
                <p className="text-secondary mb-lg" style={{ fontSize: '14px', lineHeight: 1.5 }}>{message}</p>

                <div className="flex gap-md justify-end">
                    <button
                        onClick={onCancel}
                        style={{
                            padding: '8px 16px',
                            border: '1px solid var(--border-strong)',
                            color: 'var(--text-secondary)',
                            backgroundColor: 'transparent',
                            borderRadius: '4px',
                            cursor: 'pointer'
                        }}
                    >
                        CANCEL
                    </button>
                    <button
                        onClick={onConfirm}
                        style={{
                            padding: '8px 16px',
                            backgroundColor: 'rgba(239, 68, 68, 0.1)',
                            border: '1px solid var(--status-error)',
                            color: 'var(--status-error)',
                            fontWeight: 'bold',
                            borderRadius: '4px',
                            cursor: 'pointer'
                        }}
                    >
                        CONFIRM
                    </button>
                </div>
            </div>
        </div>
    );
};
