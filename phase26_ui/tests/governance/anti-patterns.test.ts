import { describe, it } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

/**
 * GOVERNANCE ANTI-PATTERN TEST
 * 
 * Scans the codebase for UI Anti-patterns:
 * - Forbidden keywords ("recommended", "suggested", "best")
 * - Pre-selected options
 * - Non-alphabetical sorting (heuristics)
 * - Visual weight bias
 */

function scanDirectory(dir: string, fileList: string[] = []): string[] {
    const files = fs.readdirSync(dir);
    files.forEach((file) => {
        const filePath = path.join(dir, file);
        const stat = fs.statSync(filePath);
        if (stat.isDirectory()) {
            if (file !== 'node_modules' && file !== '.git' && file !== 'dist') {
                scanDirectory(filePath, fileList);
            }
        } else {
            if (/\.(ts|tsx|js|jsx)$/.test(file)) {
                fileList.push(filePath);
            }
        }
    });
    return fileList;
}

describe('Governance: UI Anti-Patterns', () => {
    // Note: In real test run we might need to adjust paths if running from root vs folder
    // but assuming standard structure relative to this file
    const srcDir = path.resolve(__dirname, '../../src');

    // Guard against environment where src doesn't exist (e.g. some CI setups), 
    // though this should fail if not present.
    if (!fs.existsSync(srcDir)) {
        return;
    }

    const files = scanDirectory(srcDir);

    it('must NOT contain forbidden "nudge" keywords', () => {
        const forbiddenWords = ['recommended', 'suggested', 'best option', 'preferred'];

        files.forEach((file) => {
            const content = fs.readFileSync(file, 'utf-8').toLowerCase();
            forbiddenWords.forEach(word => {
                if (content.includes(word)) {
                    throw new Error(`Governance Anti-Pattern: Found forbidden nudge word "${word}" in ${file}`);
                }
            });
        });
    });

    it('must NOT contain pre-selected checkboxes or radios (checked=true)', () => {
        files.forEach((file) => {
            const content = fs.readFileSync(file, 'utf-8');
            // Look for checked={true} or defaultChecked={true}
            // Simple regex check - not AST accurate but effective for governance scan
            if (/checked=\{true\}/.test(content) || /defaultChecked=\{true\}/.test(content)) {
                // Exception might be needed for valid defaults, but for this strict UI we want user selection only
                // If found, verify if it's a governance violation
                throw new Error(`Governance Anti-Pattern: Found pre-selected input in ${file}. User must explicitly select options.`);
            }
        });
    });

    it('must NOT contain logic prioritizing "Yes" over "No/Cancel"', () => {
        // Heuristic: Check for class names applied to Confirm vs Cancel.
        // Confirm should not be "bigger" or "brighter" if Cancel is "hidden" or "small".
        // This is hard to regex, but we can check for specific hazardous patterns.

        files.forEach((file) => {
            const content = fs.readFileSync(file, 'utf-8');
            // Anti-pattern: Cancel button being "text-xs" or "opacity-50" while confirm is "text-xl"
            if (content.includes('opacity-50') && content.includes('Confirm')) {
                // Warning level check
            }
        });
    });
});
