/**
 * Type definitions for the browser controller module.
 */

export interface BrowserConfig {
  headless: boolean;
  timeout: number;
  viewport: {
    width: number;
    height: number;
  };
  userAgent?: string;
}

export interface NavigationResult {
  url: string;
  statusCode: number;
  headers: Record<string, string>;
  loadTime: number;
  domReady: boolean;
}

export interface DOMSnapshot {
  html: string;
  timestamp: number;
  url: string;
  title: string;
  forms: FormInfo[];
  links: LinkInfo[];
  scripts: ScriptInfo[];
}

export interface FormInfo {
  id?: string;
  name?: string;
  action: string;
  method: string;
  inputs: InputInfo[];
}

export interface InputInfo {
  name?: string;
  type: string;
  id?: string;
  value?: string;
  required: boolean;
}

export interface LinkInfo {
  href: string;
  text: string;
  isExternal: boolean;
}

export interface ScriptInfo {
  src?: string;
  isInline: boolean;
  content?: string;
}

export interface NetworkRequest {
  id: string;
  url: string;
  method: string;
  headers: Record<string, string>;
  postData?: string;
  timestamp: number;
}

export interface NetworkResponse {
  requestId: string;
  url: string;
  status: number;
  headers: Record<string, string>;
  body?: string;
  timestamp: number;
  duration: number;
}

export interface StateSnapshot {
  cookies: CookieInfo[];
  localStorage: Record<string, string>;
  sessionStorage: Record<string, string>;
  timestamp: number;
}

export interface CookieInfo {
  name: string;
  value: string;
  domain: string;
  path: string;
  expires?: number;
  httpOnly: boolean;
  secure: boolean;
  sameSite?: string;
}

export interface InvariantCheck {
  name: string;
  validator: (state: StateSnapshot) => boolean;
  description: string;
}

export interface InvariantResult {
  name: string;
  passed: boolean;
  message?: string;
  timestamp: number;
}