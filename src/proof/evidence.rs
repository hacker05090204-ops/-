//! Evidence Collector - Captures immutable proof artifacts

use crate::types::*;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sha2::{Sha256, Digest};
use std::collections::HashMap;

/// Types of evidence
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum EvidenceType {
    HttpRequest,
    HttpResponse,
    Screenshot,
    DomSnapshot,
    NetworkCapture,
    StateSnapshot,
    LogEntry,
    ExploitOutput,
    Custom(String),
}

/// Single evidence artifact
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvidenceArtifact {
    pub id: String,
    pub evidence_type: EvidenceType,
    pub content: Vec<u8>,
    pub content_hash: String,
    pub metadata: HashMap<String, String>,
    pub captured_at: DateTime<Utc>,
}

impl EvidenceArtifact {
    pub fn new(evidence_type: EvidenceType, content: Vec<u8>) -> Self {
        let content_hash = Self::compute_hash(&content);
        Self {
            id: uuid::Uuid::new_v4().to_string(),
            evidence_type,
            content,
            content_hash,
            metadata: HashMap::new(),
            captured_at: Utc::now(),
        }
    }

    pub fn with_metadata(mut self, key: impl Into<String>, value: impl Into<String>) -> Self {
        self.metadata.insert(key.into(), value.into());
        self
    }

    fn compute_hash(content: &[u8]) -> String {
        let mut hasher = Sha256::new();
        hasher.update(content);
        hex::encode(hasher.finalize())
    }

    /// Verify content integrity
    pub fn verify_integrity(&self) -> bool {
        Self::compute_hash(&self.content) == self.content_hash
    }

    /// Get content as string (if valid UTF-8)
    pub fn content_as_string(&self) -> Option<String> {
        String::from_utf8(self.content.clone()).ok()
    }
}

/// Complete evidence collection for a finding
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Evidence {
    pub artifacts: Vec<EvidenceArtifact>,
    pub collection_id: String,
    pub collected_at: DateTime<Utc>,
    pub is_complete: bool,
}

impl Evidence {
    pub fn new() -> Self {
        Self {
            artifacts: Vec::new(),
            collection_id: uuid::Uuid::new_v4().to_string(),
            collected_at: Utc::now(),
            is_complete: false,
        }
    }

    /// Add an artifact to the collection
    pub fn add_artifact(&mut self, artifact: EvidenceArtifact) {
        self.artifacts.push(artifact);
    }

    /// Get artifacts by type
    pub fn get_by_type(&self, evidence_type: EvidenceType) -> Vec<&EvidenceArtifact> {
        self.artifacts.iter()
            .filter(|a| a.evidence_type == evidence_type)
            .collect()
    }

    /// Check if evidence has required types
    pub fn has_required_types(&self, required: &[EvidenceType]) -> bool {
        required.iter().all(|t| {
            self.artifacts.iter().any(|a| &a.evidence_type == t)
        })
    }

    /// Verify all artifacts integrity
    pub fn verify_all_integrity(&self) -> bool {
        self.artifacts.iter().all(|a| a.verify_integrity())
    }

    /// Mark collection as complete
    pub fn complete(&mut self) {
        self.is_complete = true;
    }

    /// Get total size of all artifacts
    pub fn total_size(&self) -> usize {
        self.artifacts.iter().map(|a| a.content.len()).sum()
    }
}

impl Default for Evidence {
    fn default() -> Self {
        Self::new()
    }
}

/// Collector for gathering evidence
pub struct EvidenceCollector {
    current_collection: Evidence,
    required_types: Vec<EvidenceType>,
}

impl EvidenceCollector {
    pub fn new() -> Self {
        Self {
            current_collection: Evidence::new(),
            required_types: vec![
                EvidenceType::HttpRequest,
                EvidenceType::HttpResponse,
            ],
        }
    }

    pub fn with_required_types(required: Vec<EvidenceType>) -> Self {
        Self {
            current_collection: Evidence::new(),
            required_types: required,
        }
    }

    /// Start a new collection
    pub fn start_collection(&mut self) {
        self.current_collection = Evidence::new();
    }

    /// Add HTTP request evidence
    pub fn add_http_request(&mut self, request: &HttpRequest) {
        let content = serde_json::to_vec(request).unwrap_or_default();
        let mut artifact = EvidenceArtifact::new(EvidenceType::HttpRequest, content);
        artifact.metadata.insert("method".to_string(), format!("{:?}", request.method));
        artifact.metadata.insert("url".to_string(), request.url.clone());
        self.current_collection.add_artifact(artifact);
    }

    /// Add HTTP response evidence
    pub fn add_http_response(&mut self, response: &HttpResponse) {
        let content = serde_json::to_vec(response).unwrap_or_default();
        let mut artifact = EvidenceArtifact::new(EvidenceType::HttpResponse, content);
        artifact.metadata.insert("status_code".to_string(), response.status_code.to_string());
        artifact.metadata.insert("duration_ms".to_string(), response.duration_ms.to_string());
        self.current_collection.add_artifact(artifact);
    }

    /// Add screenshot evidence
    pub fn add_screenshot(&mut self, image_data: Vec<u8>, description: &str) {
        let artifact = EvidenceArtifact::new(EvidenceType::Screenshot, image_data)
            .with_metadata("description", description);
        self.current_collection.add_artifact(artifact);
    }

    /// Add DOM snapshot evidence
    pub fn add_dom_snapshot(&mut self, html: &str) {
        let artifact = EvidenceArtifact::new(
            EvidenceType::DomSnapshot, 
            html.as_bytes().to_vec()
        );
        self.current_collection.add_artifact(artifact);
    }

    /// Add state snapshot evidence
    pub fn add_state_snapshot(&mut self, state: &crate::state::ApplicationState) {
        let content = serde_json::to_vec(state).unwrap_or_default();
        self.current_collection.add_artifact(
            EvidenceArtifact::new(EvidenceType::StateSnapshot, content)
        );
    }

    /// Add exploit output evidence
    pub fn add_exploit_output(&mut self, output: &str, exploit_name: &str) {
        let artifact = EvidenceArtifact::new(
            EvidenceType::ExploitOutput,
            output.as_bytes().to_vec()
        ).with_metadata("exploit_name", exploit_name);
        self.current_collection.add_artifact(artifact);
    }

    /// Add custom evidence
    pub fn add_custom(&mut self, name: &str, content: Vec<u8>) {
        let artifact = EvidenceArtifact::new(
            EvidenceType::Custom(name.to_string()),
            content
        );
        self.current_collection.add_artifact(artifact);
    }

    /// Finalize and return the collection
    pub fn finalize(&mut self) -> Evidence {
        let mut collection = std::mem::replace(&mut self.current_collection, Evidence::new());
        
        if collection.has_required_types(&self.required_types) {
            collection.complete();
        }
        
        collection
    }

    /// Check if current collection is complete
    pub fn is_complete(&self) -> bool {
        self.current_collection.has_required_types(&self.required_types)
    }

    /// Get current collection reference
    pub fn current(&self) -> &Evidence {
        &self.current_collection
    }
}

impl Default for EvidenceCollector {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_evidence_artifact_creation() {
        let content = b"test content".to_vec();
        let artifact = EvidenceArtifact::new(EvidenceType::HttpRequest, content.clone());
        
        assert!(!artifact.id.is_empty());
        assert_eq!(artifact.content, content);
        assert!(artifact.verify_integrity());
    }

    #[test]
    fn test_evidence_collection() {
        let mut evidence = Evidence::new();
        
        evidence.add_artifact(EvidenceArtifact::new(
            EvidenceType::HttpRequest,
            b"request".to_vec()
        ));
        evidence.add_artifact(EvidenceArtifact::new(
            EvidenceType::HttpResponse,
            b"response".to_vec()
        ));
        
        assert_eq!(evidence.artifacts.len(), 2);
        assert!(evidence.has_required_types(&[EvidenceType::HttpRequest]));
    }

    #[test]
    fn test_evidence_collector() {
        let mut collector = EvidenceCollector::new();
        
        let request = HttpRequest {
            method: HttpMethod::GET,
            url: "https://example.com".to_string(),
            headers: HashMap::new(),
            body: None,
            timestamp: Utc::now(),
        };
        
        let response = HttpResponse {
            status_code: 200,
            headers: HashMap::new(),
            body: b"OK".to_vec(),
            timestamp: Utc::now(),
            duration_ms: 100,
        };
        
        collector.add_http_request(&request);
        collector.add_http_response(&response);
        
        assert!(collector.is_complete());
        
        let evidence = collector.finalize();
        assert!(evidence.is_complete);
        assert_eq!(evidence.artifacts.len(), 2);
    }

    #[test]
    fn test_integrity_verification() {
        let artifact = EvidenceArtifact::new(
            EvidenceType::HttpRequest,
            b"test".to_vec()
        );
        
        assert!(artifact.verify_integrity());
    }
}