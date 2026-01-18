//! Core type definitions for the Kali MCP Toolkit

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use uuid::Uuid;

/// Unique identifier for findings
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct FindingId(pub Uuid);

impl FindingId {
    pub fn new() -> Self {
        Self(Uuid::new_v4())
    }
}

impl Default for FindingId {
    fn default() -> Self {
        Self::new()
    }
}

/// Unique identifier for objects in the target system
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct ObjectId(pub String);

/// Unique identifier for users
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct UserId(pub String);

/// Unique identifier for accounts (financial)
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct AccountId(pub String);

/// Unique identifier for sessions
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct SessionId(pub String);

/// User role in the target system
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct Role(pub String);

/// Financial balance representation
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub struct Balance {
    pub amount: i64,
    pub currency: Currency,
}

impl Balance {
    pub fn new(amount: i64, currency: Currency) -> Self {
        Self { amount, currency }
    }
    
    pub fn zero(currency: Currency) -> Self {
        Self { amount: 0, currency }
    }
}

/// Supported currencies
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Currency {
    USD,
    EUR,
    GBP,
    BTC,
    ETH,
    Points,
    Credits,
    Custom(u32),
}

/// Workflow step identifier
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct WorkflowStep {
    pub workflow_id: String,
    pub step_index: u32,
    pub step_name: String,
}

/// Severity levels for findings
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum Severity {
    Info,
    Low,
    Medium,
    High,
    Critical,
}

impl Severity {
    pub fn cvss_range(&self) -> (f32, f32) {
        match self {
            Severity::Info => (0.0, 0.0),
            Severity::Low => (0.1, 3.9),
            Severity::Medium => (4.0, 6.9),
            Severity::High => (7.0, 8.9),
            Severity::Critical => (9.0, 10.0),
        }
    }
}

/// Classification of findings
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum FindingClassification {
    Bug,
    Signal,
    NoIssue,
    CoverageGap,
}

/// HTTP request representation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HttpRequest {
    pub method: HttpMethod,
    pub url: String,
    pub headers: HashMap<String, String>,
    pub body: Option<Vec<u8>>,
    pub timestamp: DateTime<Utc>,
}

/// HTTP methods
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum HttpMethod {
    GET,
    POST,
    PUT,
    DELETE,
    PATCH,
    HEAD,
    OPTIONS,
    TRACE,
    CONNECT,
}

/// HTTP response representation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HttpResponse {
    pub status_code: u16,
    pub headers: HashMap<String, String>,
    pub body: Vec<u8>,
    pub timestamp: DateTime<Utc>,
    pub duration_ms: u64,
}

/// Action timing information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ActionTiming {
    pub start_time: DateTime<Utc>,
    pub end_time: DateTime<Utc>,
    pub duration_ms: u64,
}

/// Authentication token
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuthToken {
    pub token_type: TokenType,
    pub value: String,
    pub user_id: Option<UserId>,
    pub roles: HashSet<Role>,
    pub expires_at: Option<DateTime<Utc>>,
}

/// Token types
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum TokenType {
    Bearer,
    Basic,
    Cookie,
    ApiKey,
    JWT,
    OAuth2,
    Custom,
}

/// Target domain representation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Target {
    pub domain: String,
    pub subdomains: Vec<String>,
    pub services: Vec<Service>,
    pub technology_stack: TechnologyProfile,
    pub authentication: Option<AuthenticationProfile>,
}

/// Service running on a target
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Service {
    pub host: String,
    pub port: u16,
    pub protocol: Protocol,
    pub service_type: ServiceType,
    pub version: Option<String>,
    pub banner: Option<String>,
}

/// Network protocols
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Protocol {
    HTTP,
    HTTPS,
    TCP,
    UDP,
    SSH,
    FTP,
    SMTP,
    DNS,
    WebSocket,
    Custom,
}

/// Service types
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ServiceType {
    WebServer(String),
    Database(String),
    Cache(String),
    MessageQueue(String),
    API,
    SSH,
    FTP,
    Mail,
    DNS,
    Custom(String),
}

/// Technology stack profile
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct TechnologyProfile {
    pub web_server: Option<String>,
    pub application_framework: Option<String>,
    pub programming_language: Option<String>,
    pub database: Option<String>,
    pub cache: Option<String>,
    pub cdn: Option<String>,
    pub waf: Option<String>,
    pub cms: Option<String>,
    pub javascript_frameworks: Vec<String>,
    pub css_frameworks: Vec<String>,
    pub additional_technologies: HashMap<String, String>,
}

/// Authentication profile for a target
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuthenticationProfile {
    pub auth_type: AuthenticationType,
    pub login_url: Option<String>,
    pub logout_url: Option<String>,
    pub session_cookie_name: Option<String>,
    pub csrf_token_name: Option<String>,
    pub roles_discovered: Vec<Role>,
}

/// Authentication types
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum AuthenticationType {
    FormBased,
    BasicAuth,
    OAuth2,
    JWT,
    SAML,
    APIKey,
    Certificate,
    None,
    Custom,
}