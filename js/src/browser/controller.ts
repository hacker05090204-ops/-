/**
 * Browser Controller - Manages headless browser instances for security testing.
 */

import puppeteer, { Browser, Page, HTTPRequest, HTTPResponse } from 'puppeteer';
import {
  BrowserConfig,
  NavigationResult,
  DOMSnapshot,
  StateSnapshot,
  CookieInfo,
} from '../types';

const DEFAULT_CONFIG: BrowserConfig = {
  headless: true,
  timeout: 30000,
  viewport: {
    width: 1920,
    height: 1080,
  },
};

export class BrowserController {
  private browser: Browser | null = null;
  private config: BrowserConfig;
  private pages: Map<string, Page> = new Map();

  constructor(config: Partial<BrowserConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Initialize the browser instance.
   */
  async initialize(): Promise<void> {
    if (this.browser) {
      return;
    }

    this.browser = await puppeteer.launch({
      headless: this.config.headless ? 'new' : false,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--disable-gpu',
      ],
    });
  }

  /**
   * Create a new page with configured settings.
   */
  async createPage(pageId: string): Promise<Page> {
    if (!this.browser) {
      await this.initialize();
    }

    const page = await this.browser!.newPage();
    
    await page.setViewport(this.config.viewport);
    
    if (this.config.userAgent) {
      await page.setUserAgent(this.config.userAgent);
    }

    page.setDefaultTimeout(this.config.timeout);
    
    this.pages.set(pageId, page);
    return page;
  }

  /**
   * Navigate to a URL and analyze the result.
   */
  async navigateAndAnalyze(
    pageId: string,
    url: string
  ): Promise<NavigationResult> {
    const page = this.pages.get(pageId);
    if (!page) {
      throw new Error(`Page not found: ${pageId}`);
    }

    const startTime = Date.now();
    
    const response = await page.goto(url, {
      waitUntil: 'networkidle2',
      timeout: this.config.timeout,
    });

    const loadTime = Date.now() - startTime;

    return {
      url: page.url(),
      statusCode: response?.status() ?? 0,
      headers: response?.headers() ?? {},
      loadTime,
      domReady: true,
    };
  }

  /**
   * Capture DOM snapshot.
   */
  async captureDOMSnapshot(pageId: string): Promise<DOMSnapshot> {
    const page = this.pages.get(pageId);
    if (!page) {
      throw new Error(`Page not found: ${pageId}`);
    }

    const html = await page.content();
    const title = await page.title();
    const url = page.url();

    // Extract forms
    const forms = await page.evaluate(() => {
      const formElements = document.querySelectorAll('form');
      return Array.from(formElements).map(form => ({
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

    // Extract links
    const links = await page.evaluate(() => {
      const linkElements = document.querySelectorAll('a[href]');
      const currentHost = window.location.host;
      return Array.from(linkElements).map(link => {
        const href = (link as HTMLAnchorElement).href;
        let isExternal = false;
        try {
          const linkUrl = new URL(href);
          isExternal = linkUrl.host !== currentHost;
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

    // Extract scripts
    const scripts = await page.evaluate(() => {
      const scriptElements = document.querySelectorAll('script');
      return Array.from(scriptElements).map(script => ({
        src: script.src || undefined,
        isInline: !script.src,
        content: !script.src ? script.textContent?.substring(0, 1000) : undefined,
      }));
    });

    return {
      html,
      timestamp: Date.now(),
      url,
      title,
      forms,
      links,
      scripts,
    };
  }

  /**
   * Capture state snapshot (cookies, storage).
   */
  async captureStateSnapshot(pageId: string): Promise<StateSnapshot> {
    const page = this.pages.get(pageId);
    if (!page) {
      throw new Error(`Page not found: ${pageId}`);
    }

    // Get cookies
    const cookies = await page.cookies();
    const cookieInfo: CookieInfo[] = cookies.map(c => ({
      name: c.name,
      value: c.value,
      domain: c.domain,
      path: c.path,
      expires: c.expires,
      httpOnly: c.httpOnly,
      secure: c.secure,
      sameSite: c.sameSite,
    }));

    // Get localStorage and sessionStorage
    const storage = await page.evaluate(() => {
      const local: Record<string, string> = {};
      const session: Record<string, string> = {};
      
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key) {
          local[key] = localStorage.getItem(key) || '';
        }
      }
      
      for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        if (key) {
          session[key] = sessionStorage.getItem(key) || '';
        }
      }
      
      return { local, session };
    });

    return {
      cookies: cookieInfo,
      localStorage: storage.local,
      sessionStorage: storage.session,
      timestamp: Date.now(),
    };
  }

  /**
   * Execute JavaScript in page context.
   */
  async executeScript<T>(pageId: string, script: string): Promise<T> {
    const page = this.pages.get(pageId);
    if (!page) {
      throw new Error(`Page not found: ${pageId}`);
    }

    return await page.evaluate(script) as T;
  }

  /**
   * Fill and submit a form.
   */
  async fillForm(
    pageId: string,
    formSelector: string,
    data: Record<string, string>
  ): Promise<void> {
    const page = this.pages.get(pageId);
    if (!page) {
      throw new Error(`Page not found: ${pageId}`);
    }

    for (const [name, value] of Object.entries(data)) {
      const selector = `${formSelector} [name="${name}"]`;
      await page.type(selector, value);
    }
  }

  /**
   * Click an element.
   */
  async click(pageId: string, selector: string): Promise<void> {
    const page = this.pages.get(pageId);
    if (!page) {
      throw new Error(`Page not found: ${pageId}`);
    }

    await page.click(selector);
  }

  /**
   * Wait for navigation after an action.
   */
  async waitForNavigation(pageId: string): Promise<void> {
    const page = this.pages.get(pageId);
    if (!page) {
      throw new Error(`Page not found: ${pageId}`);
    }

    await page.waitForNavigation({ waitUntil: 'networkidle2' });
  }

  /**
   * Take a screenshot.
   */
  async screenshot(pageId: string): Promise<Buffer> {
    const page = this.pages.get(pageId);
    if (!page) {
      throw new Error(`Page not found: ${pageId}`);
    }

    return await page.screenshot({ fullPage: true }) as Buffer;
  }

  /**
   * Close a specific page.
   */
  async closePage(pageId: string): Promise<void> {
    const page = this.pages.get(pageId);
    if (page) {
      await page.close();
      this.pages.delete(pageId);
    }
  }

  /**
   * Close the browser and all pages.
   */
  async close(): Promise<void> {
    for (const [pageId] of this.pages) {
      await this.closePage(pageId);
    }
    
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
    }
  }

  /**
   * Get page by ID.
   */
  getPage(pageId: string): Page | undefined {
    return this.pages.get(pageId);
  }

  /**
   * Check if browser is initialized.
   */
  isInitialized(): boolean {
    return this.browser !== null;
  }
}