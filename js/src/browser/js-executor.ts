/**
 * JS Executor - Executes custom JavaScript for state inspection.
 */

import { Page } from 'puppeteer';
import { StateSnapshot, InvariantCheck, InvariantResult } from '../types';

export class JSExecutor {
  private page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * Execute arbitrary JavaScript in page context.
   */
  async execute<T>(script: string): Promise<T> {
    return await this.page.evaluate(script) as T;
  }

  /**
   * Execute a function in page context.
   */
  async executeFunction<T, A extends any[]>(
    fn: (...args: A) => T,
    ...args: A
  ): Promise<T> {
    return await this.page.evaluate(fn, ...args);
  }

  /**
   * Get current page state.
   */
  async getState(): Promise<StateSnapshot> {
    return await this.page.evaluate(() => {
      // Get cookies
      const cookies = document.cookie.split(';').map(c => {
        const [name, value] = c.trim().split('=');
        return {
          name,
          value: value || '',
          domain: window.location.hostname,
          path: '/',
          httpOnly: false,
          secure: window.location.protocol === 'https:',
        };
      }).filter(c => c.name);

      // Get localStorage
      const local: Record<string, string> = {};
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key) {
          local[key] = localStorage.getItem(key) || '';
        }
      }

      // Get sessionStorage
      const session: Record<string, string> = {};
      for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        if (key) {
          session[key] = sessionStorage.getItem(key) || '';
        }
      }

      return {
        cookies,
        localStorage: local,
        sessionStorage: session,
        timestamp: Date.now(),
      };
    });
  }

  /**
   * Check if user is authenticated based on common patterns.
   */
  async isAuthenticated(): Promise<boolean> {
    return await this.page.evaluate(() => {
      // Check for common authentication indicators
      const authIndicators = [
        // Check cookies
        document.cookie.includes('session'),
        document.cookie.includes('auth'),
        document.cookie.includes('token'),
        document.cookie.includes('logged'),
        
        // Check localStorage
        localStorage.getItem('token') !== null,
        localStorage.getItem('auth') !== null,
        localStorage.getItem('user') !== null,
        
        // Check for logout button/link
        document.querySelector('[href*="logout"]') !== null,
        document.querySelector('[href*="signout"]') !== null,
        document.querySelector('button[class*="logout"]') !== null,
        
        // Check for user profile elements
        document.querySelector('[class*="user-profile"]') !== null,
        document.querySelector('[class*="avatar"]') !== null,
      ];

      return authIndicators.some(indicator => indicator);
    });
  }

  /**
   * Get current user information if available.
   */
  async getCurrentUser(): Promise<Record<string, any> | null> {
    return await this.page.evaluate(() => {
      // Try common patterns for user data
      const userDataSources = [
        () => {
          const userData = localStorage.getItem('user');
          return userData ? JSON.parse(userData) : null;
        },
        () => {
          const userData = sessionStorage.getItem('user');
          return userData ? JSON.parse(userData) : null;
        },
        () => {
          // Check for user data in window object
          const win = window as any;
          return win.__USER__ || win.user || win.currentUser || null;
        },
      ];

      for (const source of userDataSources) {
        try {
          const data = source();
          if (data) return data;
        } catch {
          continue;
        }
      }

      return null;
    });
  }

  /**
   * Run invariant checks against current state.
   */
  async runInvariantChecks(checks: InvariantCheck[]): Promise<InvariantResult[]> {
    const state = await this.getState();
    const results: InvariantResult[] = [];

    for (const check of checks) {
      try {
        const passed = check.validator(state);
        results.push({
          name: check.name,
          passed,
          message: passed ? undefined : `Invariant "${check.name}" failed`,
          timestamp: Date.now(),
        });
      } catch (error) {
        results.push({
          name: check.name,
          passed: false,
          message: `Error checking invariant: ${error}`,
          timestamp: Date.now(),
        });
      }
    }

    return results;
  }

  /**
   * Inject and execute a payload for XSS testing.
   */
  async testXSSPayload(payload: string, targetSelector: string): Promise<boolean> {
    return await this.page.evaluate((payload, selector) => {
      const target = document.querySelector(selector);
      if (!target) return false;

      // Create a marker to detect execution
      (window as any).__xssExecuted = false;
      
      // Modify payload to set marker
      const markerPayload = payload.replace(
        /alert\([^)]*\)/g,
        '(window.__xssExecuted = true)'
      );

      // Try to inject
      if (target instanceof HTMLInputElement) {
        target.value = markerPayload;
        target.dispatchEvent(new Event('input', { bubbles: true }));
      } else {
        target.innerHTML = markerPayload;
      }

      // Check if executed
      const executed = (window as any).__xssExecuted;
      delete (window as any).__xssExecuted;
      
      return executed;
    }, payload, targetSelector);
  }

  /**
   * Extract all JavaScript variables from window object.
   */
  async extractGlobalVariables(): Promise<Record<string, string>> {
    return await this.page.evaluate(() => {
      const globals: Record<string, string> = {};
      const defaultProps = new Set(Object.getOwnPropertyNames(window));
      
      // Get custom properties added to window
      for (const key of Object.keys(window)) {
        if (!defaultProps.has(key)) {
          try {
            const value = (window as any)[key];
            globals[key] = typeof value === 'object' 
              ? JSON.stringify(value).substring(0, 500)
              : String(value).substring(0, 500);
          } catch {
            globals[key] = '[Unable to serialize]';
          }
        }
      }

      return globals;
    });
  }

  /**
   * Monitor for specific events.
   */
  async setupEventMonitor(eventTypes: string[]): Promise<void> {
    await this.page.evaluate((types) => {
      (window as any).__capturedEvents = [];
      
      types.forEach(type => {
        document.addEventListener(type, (event) => {
          (window as any).__capturedEvents.push({
            type: event.type,
            target: (event.target as Element)?.tagName || 'unknown',
            timestamp: Date.now(),
          });
        }, true);
      });
    }, eventTypes);
  }

  /**
   * Get captured events.
   */
  async getCapturedEvents(): Promise<Array<{ type: string; target: string; timestamp: number }>> {
    return await this.page.evaluate(() => {
      const events = (window as any).__capturedEvents || [];
      (window as any).__capturedEvents = [];
      return events;
    });
  }

  /**
   * Trigger a form submission and capture the result.
   */
  async submitFormAndCapture(formSelector: string): Promise<{
    submitted: boolean;
    redirected: boolean;
    newUrl?: string;
  }> {
    const originalUrl = this.page.url();
    
    const submitted = await this.page.evaluate((selector) => {
      const form = document.querySelector(selector) as HTMLFormElement;
      if (!form) return false;
      form.submit();
      return true;
    }, formSelector);

    if (!submitted) {
      return { submitted: false, redirected: false };
    }

    // Wait for potential navigation
    try {
      await this.page.waitForNavigation({ timeout: 5000 });
      const newUrl = this.page.url();
      return {
        submitted: true,
        redirected: newUrl !== originalUrl,
        newUrl: newUrl !== originalUrl ? newUrl : undefined,
      };
    } catch {
      return { submitted: true, redirected: false };
    }
  }
}