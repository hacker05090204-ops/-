import React, { useEffect, useState } from 'react';
import { api } from '../../api';
import { CVE } from '../../types';
import { Disclaimer } from '../governance/Disclaimer';

export const CVEPanel: React.FC = () => {
    const [cves, setCves] = useState<CVE[]>([]);

    useEffect(() => {
        api.fetchCVEs().then((_data: any) => {
            setCves([
                { id: "CVE-2024-0001", description: "Buffer overflow in legacy module", references: ["NVD Database", "Vendor Advisory"] },
                { id: "CVE-2024-0002", description: "Privilege escalation via API", references: ["Internal Audit"] },
                { id: "CVE-2024-0003", description: "Unvalidated input in search", references: ["Bugcrowd"] }
            ]);
        });
    }, []);

    return (
        <div className="flex flex-col h-full">
            <div className="mb-md">
                <Disclaimer type="REFERENCE_ONLY" />
            </div>

            <div className="flex flex-col gap-sm scroll-y flex-1 pr-sm">
                {cves.map(cve => (
                    <div key={cve.id} className="card flex flex-col gap-xs hover:bg-card-hover" style={{ transition: 'background-color 0.2s' }}>
                        <div className="flex justify-between items-start">
                            <span className="text-mono text-bold text-primary">{cve.id}</span>
                            <span className="text-label text-error">CRITICAL</span>
                        </div>
                        <p className="text-body text-secondary" style={{ fontSize: '13px' }}>{cve.description}</p>
                        <div className="flex gap-sm mt-sm">
                            {cve.references.map((ref, i) => (
                                <span key={i} className="text-label text-tertiary" style={{ border: '1px solid var(--border-subtle)', padding: '2px 4px', borderRadius: '3px' }}>
                                    {ref}
                                </span>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};
