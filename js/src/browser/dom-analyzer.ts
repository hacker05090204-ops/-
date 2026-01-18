/**
 * DOM Analyzer - Analyzes dynamic DOM changes and state.
 */

import { Page } from 'puppeteer';
import { DOMSnapshot, FormInfo, LinkInfo } from '../types';

export interface DOMChange {
  type: 'added' | 'removed' | 'modified';
  element: string;
  selector: string;
  timestamp: number;
}

export interface DOMAnalysisResult {
  forms: FormInfo[];
  links: LinkInfo[];
  inputFields: InputFieldAnalysis[];
  potentialVulnerabilities: PotentialVulnerability[];
}

export interface InputFieldAnalysis {
  name: string;
  type: string;
  hasValidation: boolean;
  maxLength?: number;
  pattern?: string;
  isHidden: boolean;
}

export interface PotentialVulnerability {
  type: string;
  element: string;
  description: string;
  confidence: number;
}

export class DOMAnalyzer {
  private page: Page;
  private changes: DOMChange[] = [];
  private observerSetup = false;

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * Set up mutation observer to track DOM changes.
   */
  async setupMutationObserver(): Promise<void> {
    if (this.observerSetup) {
      return;
    }

    await this.page.evaluate(() => {
      (window as any).__domChanges = [];
      
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          const change = {
            type: mutation.type === 'childList' 
              ? (mutation.addedNodes.length > 0 ? 'added' : 'removed')
              : 'modified',
            element: (mutation.target as Element).tagName || 'unknown',
            timestamp: Date.now(),
          };
          (window as any).__domChanges.push(change);
        });
      });

      observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        characterData: true,
      });

      (window as any).__domObserver = observer;
    });

    this.observerSetup = true;
  }

  /**
   * Get recorded DOM changes.
   */
  async getChanges(): Promise<DOMChange[]> {
    const changes = await this.page.evaluate(() => {
      const recorded = (window as any).__domChanges || [];
      (window as any).__domChanges = [];
      return recorded;
    });

    this.changes.push(...changes);
    return changes;
  }

  /**
   * Analyze the current DOM for security-relevant elements.
   */
  async analyze(): Promise<DOMAnalysisResult> {
    const forms = await this.analyzeForms();
    const links = await this.analyzeLinks();
    const inputFields = await this.analyzeInputFields();
    const potentialVulnerabilities = await this.detectPotentialVulnerabilities();

    return {
      forms,
      links,
      inputFields,
      potentialVulnerabilities,
    };
  }

  /**
   * Analyze forms in the DOM.
   */
  private async analyzeForms(): Promise<FormInfo[]> {
    return await this.page.evaluate(() => {
      const forms = document.querySelectorAll('form');
      return Array.from(forms).map(form => ({
        id: form.id || undefined,
        name: form.name || undefined,
        action: form.action,
        method: form.method.toUpperCase(),
        inputs: Array.from(form.querySelectorAll('input, textarea, select')).map(input => ({
          name: (input as HTMLInputElement).name || undefined,
          type: (input as HTMLInputElement).type || 'text',
          id: input.id || undefined,
          value: (input as HTMLInputElement).value || undefined,
          required: (input as HTMLInputElement).required,
        })),
      }));
    });
  }

  /**
   * Analyze links in the DOM.
   */
  private async analyzeLinks(): Promise<LinkInfo[]> {
    return await this.page.evaluate(() => {
      const links = document.querySelectorAll('a[href]');
      const currentHost = window.location.host;
      
      return Array.from(links).map(link => {
        const href = (link as HTMLAnchorElement).href;
        let isExternal = false;
        try {
          const url = new URL(href);
          isExternal = url.host !== currentHost;
        } catch {
          isExternal = false;
        }
        return {
          href,
          text: link.textContent?.trim() || '',
          isExternal,
        };
      });
    });
  }

  /**
   * Analyze input fields for security characteristics.
   */
  private async analyzeInputFields(): Promise<InputFieldAnalysis[]> {
    return await this.page.evaluate(() => {
      const inputs = document.querySelectorAll('input, textarea');
      
      return Array.from(inputs).map(input => {
        const el = input as HTMLInputElement;
        return {
          name: el.name || el.id || 'unnamed',
          type: el.type || 'text',
          hasValidation: el.pattern !== '' || el.required || el.maxLength > 0,
          maxLength: el.maxLength > 0 ? el.maxLength : undefined,
          pattern: el.pattern || undefined,
          isHidden: el.type === 'hidden' || 
                    getComputedStyle(el).display === 'none' ||
                    getComputedStyle(el).visibility === 'hidden',
        };
      });
    });
  }

  /**
   * Detect potential vulnerabilities in the DOM.
   */
  private async detectPotentialVulnerabilities(): Promise<PotentialVulnerability[]> {
    return await this.page.evaluate(() => {
      const vulnerabilities: PotentialVulnerability[] = [];

      // Check for forms without CSRF tokens
      const forms = document.querySelectorAll('form[method="post" i]');
      forms.forEach(form => {
        const hasCSRF = form.querySelector('input[name*="csrf" i], input[name*="token" i]');
        if (!hasCSRF) {
          vulnerabilities.push({
            type: 'missing_csrf',
            element: `form#${form.id || 'unnamed'}`,
            description: 'POST form without apparent CSRF token',
            confidence: 0.7,
          });
        }
      });

      // Check for password fields without autocomplete=off
      const passwordFields = document.querySelectorAll('input[type="password"]');
      passwordFields.forEach(field => {
        if ((field as HTMLInputElement).autocomplete !== 'off') {
          vulnerabilities.push({
            type: 'password_autocomplete',
            element: `input#${field.id || 'unnamed'}`,
            description: 'Password field allows autocomplete',
            confidence: 0.5,
          });
        }
      });

      // Check for inline event handlers (potential XSS vectors)
      const elementsWithHandlers = document.querySelectorAll('[onclick], [onerror], [onload], [onmouseover]');
      elementsWithHandlers.forEach(el => {
        vulnerabilities.push({
          type: 'inline_event_handler',
          element: el.tagName.toLowerCase(),
          description: 'Element with inline event handler',
          confidence: 0.3,
        });
      });

      // Check for forms with action to different domain
      const allForms = document.querySelectorAll('form[action]');
      const currentHost = window.location.host;
      allForms.forEach(form => {
        try {
          const actionUrl = new URL((form as HTMLFormElement).action);
          if (actionUrl.host !== currentHost) {
            vulnerabilities.push({
              type: 'cross_domain_form',
              element: `form#${form.id || 'unnamed'}`,
              description: 'Form submits to different domain',
              confidence: 0.6,
            });
          }
        } catch {
          // Invalid URL, skip
        }
      });

      return vulnerabilities;
    });
  }

  /**
   * Compare two DOM snapshots.
   */
  compareSnapshots(before: DOMSnapshot, after: DOMSnapshot): DOMChange[] {
    const changes: DOMChange[] = [];

    // Compare forms
    const beforeFormIds = new Set(before.forms.map(f => f.id || f.action));
    const afterFormIds = new Set(after.forms.map(f => f.id || f.action));

    for (const id of afterFormIds) {
      if (!beforeFormIds.has(id)) {
        changes.push({
          type: 'added',
          element: 'form',
          selector: `form[action="${id}"]`,
          timestamp: after.timestamp,
        });
      }
    }

    for (const id of beforeFormIds) {
      if (!afterFormIds.has(id)) {
        changes.push({
          type: 'removed',
          element: 'form',
          selector: `form[action="${id}"]`,
          timestamp: after.timestamp,
        });
      }
    }

    return changes;
  }

  /**
   * Stop the mutation observer.
   */
  async stopObserver(): Promise<void> {
    if (!this.observerSetup) {
      return;
    }

    await this.page.evaluate(() => {
      if ((window as any).__domObserver) {
        (window as any).__domObserver.disconnect();
        (window as any).__domObserver = null;
      }
    });

    this.observerSetup = false;
  }
}