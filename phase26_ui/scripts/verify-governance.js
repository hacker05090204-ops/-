
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function scanDirectory(dir, fileList = []) {
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

console.log("Starting Governance & Anti-Pattern Scan...");

const srcDir = path.resolve(__dirname, '../src');
if (!fs.existsSync(srcDir)) {
    console.error(`Source directory not found: ${srcDir}`);
    process.exit(1);
}

const files = scanDirectory(srcDir);
let errors = [];

files.forEach((file) => {
    const content = fs.readFileSync(file, 'utf-8');
    const contentLower = content.toLowerCase();

    // EXISTING CHECKS
    if (content.includes('auto_submit')) errors.push(`Violation: "auto_submit" in ${file}`);
    if (content.includes('auto_navigate')) errors.push(`Violation: "auto_navigate" in ${file}`);
    if (content.includes('headless: true')) errors.push(`Violation: "headless: true" in ${file}`);
    if (/function\s+verify/i.test(content) || /const\s+verify\s+=/i.test(content)) {
        errors.push(`Violation: "verify" function in ${file}`);
    }

    // NEW HARDENING CHECKS (Anti-Patterns)
    const forbiddenWords = ['recommended', 'suggested', 'best option', 'preferred'];
    forbiddenWords.forEach(word => {
        if (contentLower.includes(word)) {
            errors.push(`Anti-Pattern: Forbidden nudge word "${word}" in ${file}`);
        }
    });

    if (/checked=\{true\}/.test(content) || /defaultChecked=\{true\}/.test(content)) {
        errors.push(`Anti-Pattern: Pre-selected input in ${file}`);
    }
});

if (errors.length > 0) {
    console.error("GOVERNANCE / HARDENING CHECKS FAILED:");
    errors.forEach(e => console.error(` - ${e}`));
    process.exit(1);
} else {
    console.log("✅ GOVERNANCE & HARDENING CHECKS PASSED.");
    process.exit(0);
}
