/**
 * Network Interceptor - Captures and analyzes network traffic.
 */

import { Page, HTTPRequest, HTTPResponse } from 'puppeteer';
import { NetworkRequest, NetworkResponse } from '../types';

export interface InterceptionRule {
  urlPattern: RegExp;
  action: 'block' | 'modify' | 'log';
  modifier?: (request: HTTPRequest) => Record<string, string>;
}

export class NetworkInterceptor {
  private page: Page;
  private requests: Map<string, NetworkRequest> = new Map();
  private responses: Map<string, NetworkResponse> = new Map();
  private rules: InterceptionRule[] = [];
  private isIntercepting = false;

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * Start intercepting network requests.
   */
  async startInterception(): Promise<void> {
    if (this.isIntercepting) {
      return;
    }

    await this.page.setRequestInterception(true);

    this.page.on('request', this.handleRequest.bind(this));
    this.page.on('response', this.handleResponse.bind(this));

    this.isIntercepting = true;
  }

  /**
   * Handle intercepted request.
   */
  private async handleRequest(request: HTTPRequest): Promise<void> {
    const id = this.generateRequestId();
    const url = request.url();

    // Store request info
    const networkRequest: NetworkRequest = {
      id,
      url,
      method: request.method(),
      headers: request.headers(),
      postData: request.postData(),
      timestamp: Date.now(),
    };
    this.requests.set(id, networkRequest);

    // Check rules
    for (const rule of this.rules) {
      if (rule.urlPattern.test(url)) {
        if (rule.action === 'block') {
          await request.abort();
          return;
        } else if (rule.action === 'modify' && rule.modifier) {
          const modifiedHeaders = rule.modifier(request);
          await request.continue({ headers: { ...request.headers(), ...modifiedHeaders } });
          return;
        }
      }
    }

    await request.continue();
  }

  /**
   * Handle response.
   */
  private async handleResponse(response: HTTPResponse): Promise<void> {
    const request = response.request();
    const url = request.url();

    // Find matching request
    let requestId: string | undefined;
    for (const [id, req] of this.requests) {
      if (req.url === url && !this.responses.has(id)) {
        requestId = id;
        break;
      }
    }

    if (!requestId) {
      requestId = this.generateRequestId();
    }

    const requestTimestamp = this.requests.get(requestId)?.timestamp || Date.now();

    const networkResponse: NetworkResponse = {
      requestId,
      url,
      status: response.status(),
      headers: response.headers(),
      timestamp: Date.now(),
      duration: Date.now() - requestTimestamp,
    };

    // Try to get response body for text responses
    try {
      const contentType = response.headers()['content-type'] || '';
      if (contentType.includes('text') || contentType.includes('json') || contentType.includes('xml')) {
        networkResponse.body = await response.text();
      }
    } catch {
      // Body not available
    }

    this.responses.set(requestId, networkResponse);
  }

  /**
   * Add an interception rule.
   */
  addRule(rule: InterceptionRule): void {
    this.rules.push(rule);
  }

  /**
   * Remove all rules.
   */
  clearRules(): void {
    this.rules = [];
  }

  /**
   * Get all captured requests.
   */
  getRequests(): NetworkRequest[] {
    return Array.from(this.requests.values());
  }

  /**
   * Get all captured responses.
   */
  getResponses(): NetworkResponse[] {
    return Array.from(this.responses.values());
  }

  /**
   * Get request-response pairs.
   */
  getPairs(): Array<{ request: NetworkRequest; response?: NetworkResponse }> {
    const pairs: Array<{ request: NetworkRequest; response?: NetworkResponse }> = [];
    
    for (const [id, request] of this.requests) {
      pairs.push({
        request,
        response: this.responses.get(id),
      });
    }
    
    return pairs;
  }

  /**
   * Filter requests by URL pattern.
   */
  filterByUrl(pattern: RegExp): NetworkRequest[] {
    return this.getRequests().filter(r => pattern.test(r.url));
  }

  /**
   * Filter requests by method.
   */
  filterByMethod(method: string): NetworkRequest[] {
    return this.getRequests().filter(r => r.method === method.toUpperCase());
  }

  /**
   * Get requests with specific status codes.
   */
  filterByStatus(statusCodes: number[]): NetworkResponse[] {
    return this.getResponses().filter(r => statusCodes.includes(r.status));
  }

  /**
   * Find potential security issues in captured traffic.
   */
  analyzeSecurityIssues(): SecurityIssue[] {
    const issues: SecurityIssue[] = [];

    for (const response of this.getResponses()) {
      // Check for missing security headers
      const headers = response.headers;
      
      if (!headers['x-frame-options'] && !headers['content-security-policy']) {
        issues.push({
          type: 'missing_clickjacking_protection',
          url: response.url,
          description: 'Missing X-Frame-Options or CSP frame-ancestors',
          severity: 'medium',
        });
      }

      if (!headers['x-content-type-options']) {
        issues.push({
          type: 'missing_content_type_options',
          url: response.url,
          description: 'Missing X-Content-Type-Options header',
          severity: 'low',
        });
      }

      if (!headers['strict-transport-security'] && response.url.startsWith('https')) {
        issues.push({
          type: 'missing_hsts',
          url: response.url,
          description: 'Missing Strict-Transport-Security header',
          severity: 'medium',
        });
      }

      // Check for sensitive data in responses
      if (response.body) {
        if (/password|secret|api[_-]?key|token/i.test(response.body)) {
          issues.push({
            type: 'potential_sensitive_data',
            url: response.url,
            description: 'Response may contain sensitive data',
            severity: 'high',
          });
        }
      }
    }

    // Check for mixed content
    const httpsRequests = this.getRequests().filter(r => r.url.startsWith('https'));
    const httpRequests = this.getRequests().filter(r => r.url.startsWith('http://'));
    
    if (httpsRequests.length > 0 && httpRequests.length > 0) {
      issues.push({
        type: 'mixed_content',
        url: httpRequests[0].url,
        description: 'Mixed HTTP/HTTPS content detected',
        severity: 'medium',
      });
    }

    return issues;
  }

  /**
   * Clear captured traffic.
   */
  clear(): void {
    this.requests.clear();
    this.responses.clear();
  }

  /**
   * Stop interception.
   */
  async stopInterception(): Promise<void> {
    if (!this.isIntercepting) {
      return;
    }

    await this.page.setRequestInterception(false);
    this.isIntercepting = false;
  }

  /**
   * Generate unique request ID.
   */
  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

export interface SecurityIssue {
  type: string;
  url: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}