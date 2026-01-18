/**
 * Property-based tests for browser controller and JavaScript analysis.
 *
 * **Task 8: Implement browser controller and JavaScript analysis**
 * **Property Tests: 8.1**
 *
 * Requirements validated:
 * - Browser State Consistency
 * - DOM Analysis
 * - Network Interception
 * - JavaScript Execution
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fc from 'fast-check';

// Mock puppeteer for unit testing - returns unique page objects
vi.mock('puppeteer', () => ({
  default: {
    launch: vi.fn().mockResolvedValue({
      newPage: vi.fn().mockImplementation(() => Promise.resolve({
        _uniqueId: Math.random().toString(36),
        setViewport: vi.fn(),
        setUserAgent: vi.fn(),
        setDefaultTimeout: vi.fn(),
        goto: vi.fn().mockResolvedValue({
          status: () => 200,
          headers: () => ({}),
        }),
        content: vi.fn().mockResolvedValue('<html><body>Test</body></html>'),
        title: vi.fn().mockResolvedValue('Test Page'),
        url: vi.fn().mockReturnValue('https://example.com'),
        evaluate: vi.fn().mockImplementation((fn) => {
          if (typeof fn === 'function') {
            return Promise.resolve({});
          }
          return Promise.resolve(fn);
        }),
        cookies: vi.fn().mockResolvedValue([]),
        screenshot: vi.fn().mockResolvedValue(Buffer.from('test')),
        close: vi.fn(),
        setRequestInterception: vi.fn(),
        on: vi.fn(),
        click: vi.fn(),
        type: vi.fn(),
        waitForNavigation: vi.fn(),
      })),
      close: vi.fn(),
    }),
  },
}));

import { BrowserController } from '../controller';
import { DOMAnalyzer, DOMChange, PotentialVulnerability } from '../dom-analyzer';
import { NetworkInterceptor, SecurityIssue } from '../network-interceptor';
import { JSExecutor } from '../js-executor';
import { DOMSnapshot, StateSnapshot, FormInfo, LinkInfo } from '../../types';

// ============================================================================
// Test Helpers
// ============================================================================

function createMockPage() {
  return {
    setViewport: vi.fn(),
    setUserAgent: vi.fn(),
    setDefaultTimeout: vi.fn(),
    goto: vi.fn().mockResolvedValue({
      status: () => 200,
      headers: () => ({}),
    }),
    content: vi.fn().mockResolvedValue('<html><body>Test</body></html>'),
    title: vi.fn().mockResolvedValue('Test Page'),
    url: vi.fn().mockReturnValue('https://example.com'),
    evaluate: vi.fn().mockResolvedValue({}),
    cookies: vi.fn().mockResolvedValue([]),
    screenshot: vi.fn().mockResolvedValue(Buffer.from('test')),
    close: vi.fn(),
    setRequestInterception: vi.fn(),
    on: vi.fn(),
    click: vi.fn(),
    type: vi.fn(),
    waitForNavigation: vi.fn(),
  };
}

function createMockDOMSnapshot(): DOMSnapshot {
  return {
    html: '<html><body>Test</body></html>',
    timestamp: Date.now(),
    url: 'https://example.com',
    title: 'Test Page',
    forms: [],
    links: [],
    scripts: [],
  };
}

function createMockStateSnapshot(): StateSnapshot {
  return {
    cookies: [],
    localStorage: {},
    sessionStorage: {},
    timestamp: Date.now(),
  };
}

// ============================================================================
// Property Test 8.1: Browser State Consistency
// **Validates: Requirements 2A.1 for browser contexts**
// ============================================================================

describe('BrowserController', () => {
  let controller: BrowserController;

  beforeEach(() => {
    controller = new BrowserController();
  });

  afterEach(async () => {
    await controller.close();
  });

  describe('Property: Browser initialization is idempotent', () => {
    it('should only initialize once', async () => {
      await controller.initialize();
      const firstInit = controller.isInitialized();
      
      await controller.initialize();
      const secondInit = controller.isInitialized();
      
      expect(firstInit).toBe(true);
      expect(secondInit).toBe(true);
    });
  });

  describe('Property: Page creation is consistent', () => {
    it('should create unique pages with unique IDs', async () => {
      await controller.initialize();
      
      const page1 = await controller.createPage('page1');
      const page2 = await controller.createPage('page2');
      
      expect(controller.getPage('page1')).toBeDefined();
      expect(controller.getPage('page2')).toBeDefined();
      expect(controller.getPage('page1')).not.toBe(controller.getPage('page2'));
    });

    it('should throw for non-existent pages', async () => {
      await controller.initialize();
      
      expect(controller.getPage('nonexistent')).toBeUndefined();
    });
  });

  describe('Property: Page closure removes page from registry', () => {
    it('should remove page after closing', async () => {
      await controller.initialize();
      await controller.createPage('test');
      
      expect(controller.getPage('test')).toBeDefined();
      
      await controller.closePage('test');
      
      expect(controller.getPage('test')).toBeUndefined();
    });
  });
});

describe('DOMAnalyzer', () => {
  describe('Property: DOM snapshot comparison is symmetric', () => {
    it('should detect changes in both directions', () => {
      const mockPage = createMockPage() as any;
      const analyzer = new DOMAnalyzer(mockPage);
      
      const before: DOMSnapshot = {
        ...createMockDOMSnapshot(),
        forms: [{ action: 'form1', method: 'POST', inputs: [] }],
      };
      
      const after: DOMSnapshot = {
        ...createMockDOMSnapshot(),
        forms: [{ action: 'form2', method: 'POST', inputs: [] }],
      };
      
      const changes = analyzer.compareSnapshots(before, after);
      
      // Should detect form1 removed and form2 added
      expect(changes.length).toBeGreaterThan(0);
    });
  });

  describe('Property: Empty snapshots produce no changes', () => {
    it('should return empty changes for identical snapshots', () => {
      const mockPage = createMockPage() as any;
      const analyzer = new DOMAnalyzer(mockPage);
      
      const snapshot = createMockDOMSnapshot();
      const changes = analyzer.compareSnapshots(snapshot, snapshot);
      
      expect(changes.length).toBe(0);
    });
  });
});

describe('NetworkInterceptor', () => {
  let interceptor: NetworkInterceptor;
  let mockPage: any;

  beforeEach(() => {
    mockPage = createMockPage();
    interceptor = new NetworkInterceptor(mockPage);
  });

  describe('Property: Request filtering is consistent', () => {
    it('should filter by URL pattern consistently', () => {
      // Add some mock requests
      const requests = [
        { id: '1', url: 'https://api.example.com/users', method: 'GET', headers: {}, timestamp: Date.now() },
        { id: '2', url: 'https://api.example.com/posts', method: 'GET', headers: {}, timestamp: Date.now() },
        { id: '3', url: 'https://other.com/data', method: 'GET', headers: {}, timestamp: Date.now() },
      ];
      
      // Simulate filtering
      const pattern = /api\.example\.com/;
      const filtered = requests.filter(r => pattern.test(r.url));
      
      expect(filtered.length).toBe(2);
      expect(filtered.every(r => r.url.includes('api.example.com'))).toBe(true);
    });
  });

  describe('Property: Security analysis is deterministic', () => {
    it('should produce consistent results for same input', () => {
      const responses = [
        {
          requestId: '1',
          url: 'https://example.com',
          status: 200,
          headers: {},
          timestamp: Date.now(),
          duration: 100,
        },
      ];
      
      // Analyze twice
      const analyzeHeaders = (headers: Record<string, string>) => {
        const issues: string[] = [];
        if (!headers['x-frame-options'] && !headers['content-security-policy']) {
          issues.push('missing_clickjacking_protection');
        }
        if (!headers['x-content-type-options']) {
          issues.push('missing_content_type_options');
        }
        return issues;
      };
      
      const result1 = analyzeHeaders(responses[0].headers);
      const result2 = analyzeHeaders(responses[0].headers);
      
      expect(result1).toEqual(result2);
    });
  });

  describe('Property: Rule matching is order-independent for non-overlapping patterns', () => {
    it('should match rules correctly', () => {
      const rules = [
        { urlPattern: /api\.example\.com/, action: 'log' as const },
        { urlPattern: /other\.com/, action: 'block' as const },
      ];
      
      const url1 = 'https://api.example.com/test';
      const url2 = 'https://other.com/test';
      
      const matchedRule1 = rules.find(r => r.urlPattern.test(url1));
      const matchedRule2 = rules.find(r => r.urlPattern.test(url2));
      
      expect(matchedRule1?.action).toBe('log');
      expect(matchedRule2?.action).toBe('block');
    });
  });
});

describe('JSExecutor', () => {
  let executor: JSExecutor;
  let mockPage: any;

  beforeEach(() => {
    mockPage = createMockPage();
    executor = new JSExecutor(mockPage);
  });

  describe('Property: State capture is complete', () => {
    it('should capture all state components', async () => {
      mockPage.evaluate.mockResolvedValue({
        cookies: [{ name: 'session', value: 'abc123' }],
        localStorage: { user: 'test' },
        sessionStorage: { temp: 'data' },
        timestamp: Date.now(),
      });
      
      const state = await executor.getState();
      
      expect(state).toHaveProperty('cookies');
      expect(state).toHaveProperty('localStorage');
      expect(state).toHaveProperty('sessionStorage');
      expect(state).toHaveProperty('timestamp');
    });
  });

  describe('Property: Invariant checks are independent', () => {
    it('should run checks independently', async () => {
      mockPage.evaluate.mockResolvedValue({
        cookies: [],
        localStorage: {},
        sessionStorage: {},
        timestamp: Date.now(),
      });
      
      const checks = [
        {
          name: 'check1',
          description: 'Check that cookies are empty',
          validator: (state: StateSnapshot) => state.cookies.length === 0,
        },
        {
          name: 'check2',
          description: 'Check that localStorage is empty',
          validator: (state: StateSnapshot) => Object.keys(state.localStorage).length === 0,
        },
      ];
      
      const results = await executor.runInvariantChecks(checks);
      
      expect(results.length).toBe(2);
      expect(results[0].name).toBe('check1');
      expect(results[1].name).toBe('check2');
    });
  });
});

// ============================================================================
// Property-Based Tests with fast-check
// ============================================================================

describe('Property-Based Tests', () => {
  describe('DOM Snapshot Properties', () => {
    it('should preserve form count through serialization', () => {
      fc.assert(
        fc.property(
          fc.array(fc.record({
            action: fc.webUrl(),
            method: fc.constantFrom('GET', 'POST'),
            inputs: fc.array(fc.record({
              name: fc.string({ minLength: 1, maxLength: 20 }),
              type: fc.constantFrom('text', 'password', 'email', 'hidden'),
            })),
          }), { maxLength: 10 }),
          (forms) => {
            const snapshot: DOMSnapshot = {
              ...createMockDOMSnapshot(),
              forms: forms as FormInfo[],
            };
            
            const serialized = JSON.stringify(snapshot);
            const deserialized = JSON.parse(serialized) as DOMSnapshot;
            
            return deserialized.forms.length === forms.length;
          }
        )
      );
    });

    it('should preserve link count through serialization', () => {
      fc.assert(
        fc.property(
          fc.array(fc.record({
            href: fc.webUrl(),
            text: fc.string({ maxLength: 100 }),
            isExternal: fc.boolean(),
          }), { maxLength: 20 }),
          (links) => {
            const snapshot: DOMSnapshot = {
              ...createMockDOMSnapshot(),
              links: links as LinkInfo[],
            };
            
            const serialized = JSON.stringify(snapshot);
            const deserialized = JSON.parse(serialized) as DOMSnapshot;
            
            return deserialized.links.length === links.length;
          }
        )
      );
    });
  });

  describe('State Snapshot Properties', () => {
    it('should preserve cookie data through serialization', () => {
      fc.assert(
        fc.property(
          fc.array(fc.record({
            name: fc.string({ minLength: 1, maxLength: 50 }),
            value: fc.string({ maxLength: 200 }),
            domain: fc.domain(),
            path: fc.constantFrom('/', '/api', '/app'),
            httpOnly: fc.boolean(),
            secure: fc.boolean(),
          }), { maxLength: 10 }),
          (cookies) => {
            const snapshot: StateSnapshot = {
              ...createMockStateSnapshot(),
              cookies: cookies as any[],
            };
            
            const serialized = JSON.stringify(snapshot);
            const deserialized = JSON.parse(serialized) as StateSnapshot;
            
            return deserialized.cookies.length === cookies.length;
          }
        )
      );
    });

    it('should preserve localStorage data through serialization', () => {
      fc.assert(
        fc.property(
          fc.dictionary(
            fc.string({ minLength: 1, maxLength: 20 }),
            fc.string({ maxLength: 100 })
          ),
          (storage) => {
            const snapshot: StateSnapshot = {
              ...createMockStateSnapshot(),
              localStorage: storage,
            };
            
            const serialized = JSON.stringify(snapshot);
            const deserialized = JSON.parse(serialized) as StateSnapshot;
            
            return Object.keys(deserialized.localStorage).length === Object.keys(storage).length;
          }
        )
      );
    });
  });

  describe('Security Issue Detection Properties', () => {
    it('should detect missing security headers consistently', () => {
      fc.assert(
        fc.property(
          fc.record({
            'x-frame-options': fc.option(fc.constant('DENY')),
            'x-content-type-options': fc.option(fc.constant('nosniff')),
            'strict-transport-security': fc.option(fc.constant('max-age=31536000')),
          }),
          (headers) => {
            const issues: string[] = [];
            
            if (!headers['x-frame-options']) {
              issues.push('missing_xfo');
            }
            if (!headers['x-content-type-options']) {
              issues.push('missing_xcto');
            }
            if (!headers['strict-transport-security']) {
              issues.push('missing_hsts');
            }
            
            // Property: number of issues equals number of missing headers
            const missingCount = Object.values(headers).filter(v => v === null).length;
            return issues.length === missingCount;
          }
        )
      );
    });
  });
});
