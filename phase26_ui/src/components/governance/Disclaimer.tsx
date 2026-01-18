import React from 'react';

interface Props {
    type: 'UNVERIFIED_EVIDENCE' | 'REFERENCE_ONLY';
}

export const Disclaimer: React.FC<Props> = ({ type }) => {
    const text = type === 'UNVERIFIED_EVIDENCE'
        ? "NOT VERIFIED - RAW EVIDENCE"
        : "REFERENCE ONLY - NO APPLICABILITY CLAIM";

    // Styles based on type
    const isWarning = type === 'UNVERIFIED_EVIDENCE';

    // Using inline styles for specific component logic to avoid too many utility classes
    const style: React.CSSProperties = {
        border: `1px solid ${isWarning ? 'var(--status-warning)' : 'var(--accent-blue)'}`,
        color: isWarning ? 'var(--status-warning)' : 'var(--accent-blue)',
        backgroundColor: isWarning ? 'rgba(245, 158, 11, 0.1)' : 'rgba(59, 130, 246, 0.1)',
        padding: '4px',
        fontSize: '10px',
        fontWeight: 700,
        textAlign: 'center',
        textTransform: 'uppercase',
        letterSpacing: '0.1em',
        marginBottom: 'var(--space-sm)',
        userSelect: 'none'
    };

    return (
        <div style={style}>
            {text}
        </div>
    );
};
