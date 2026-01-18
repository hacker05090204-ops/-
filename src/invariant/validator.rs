//! Invariant Validator - Evaluates findings against security invariants

use super::catalog::{InvariantCatalog, InvariantCategory, SecurityInvariant};
use crate::state::ApplicationState;
use crate::types::*;
use serde::{Deserialize, Serialize};
use std::sync::Arc;

/// Result of invariant validation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationResult {
    pub is_valid: bool,
    pub violations: Vec<ViolationDetails>,
    pub checked_invariants: Vec<String>,
    pub classification: FindingClassification,
}

impl ValidationResult {
    pub fn valid(checked_invariants: Vec<String>) -> Self {
        Self {
            is_valid: true,
            violations: Vec::new(),
            checked_invariants,
            classification: FindingClassification::NoIssue,
        }
    }

    pub fn violation(violations: Vec<ViolationDetails>, checked_invariants: Vec<String>) -> Self {
        Self {
            is_valid: false,
            violations,
            checked_invariants,
            classification: FindingClassification::Bug,
        }
    }

    pub fn signal(checked_invariants: Vec<String>) -> Self {
        Self {
            is_valid: true,
            violations: Vec::new(),
            checked_invariants,
            classification: FindingClassification::Signal,
        }
    }
}

/// Details of an invariant violation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ViolationDetails {
    pub invariant_id: String,
    pub invariant_name: String,
    pub category: InvariantCategory,
    pub message: String,
    pub severity: Severity,
    pub confidence: f64,
}

/// Invariant validator that evaluates state transitions
pub struct InvariantValidator {
    catalog: Arc<InvariantCatalog>,
}

impl InvariantValidator {
    pub fn new(catalog: Arc<InvariantCatalog>) -> Self {
        Self { catalog }
    }

    /// Validate a state transition against all invariants
    pub fn validate_transition(
        &self,
        before: &ApplicationState,
        after: &ApplicationState,
    ) -> ValidationResult {
        let mut violations = Vec::new();
        let mut checked = Vec::new();

        for invariant in self.catalog.all() {
            checked.push(invariant.id.clone());
            
            if !invariant.validate(before, after) {
                violations.push(ViolationDetails {
                    invariant_id: invariant.id.clone(),
                    invariant_name: invariant.name.clone(),
                    category: invariant.category,
                    message: invariant.violation_message.clone(),
                    severity: self.determine_severity(&invariant.category),
                    confidence: 1.0, // Invariant violations have high confidence
                });
            }
        }

        if violations.is_empty() {
            ValidationResult::valid(checked)
        } else {
            ValidationResult::violation(violations, checked)
        }
    }

    /// Validate against specific invariant categories
    pub fn validate_categories(
        &self,
        before: &ApplicationState,
        after: &ApplicationState,
        categories: &[InvariantCategory],
    ) -> ValidationResult {
        let mut violations = Vec::new();
        let mut checked = Vec::new();

        for category in categories {
            for invariant in self.catalog.get_by_category(*category) {
                checked.push(invariant.id.clone());
                
                if !invariant.validate(before, after) {
                    violations.push(ViolationDetails {
                        invariant_id: invariant.id.clone(),
                        invariant_name: invariant.name.clone(),
                        category: invariant.category,
                        message: invariant.violation_message.clone(),
                        severity: self.determine_severity(&invariant.category),
                        confidence: 1.0,
                    });
                }
            }
        }

        if violations.is_empty() {
            ValidationResult::valid(checked)
        } else {
            ValidationResult::violation(violations, checked)
        }
    }

    /// Validate against a specific invariant by ID
    pub fn validate_invariant(
        &self,
        invariant_id: &str,
        before: &ApplicationState,
        after: &ApplicationState,
    ) -> Option<ValidationResult> {
        let invariant = self.catalog.get(invariant_id)?;
        
        if invariant.validate(before, after) {
            Some(ValidationResult::valid(vec![invariant_id.to_string()]))
        } else {
            Some(ValidationResult::violation(
                vec![ViolationDetails {
                    invariant_id: invariant.id.clone(),
                    invariant_name: invariant.name.clone(),
                    category: invariant.category,
                    message: invariant.violation_message.clone(),
                    severity: self.determine_severity(&invariant.category),
                    confidence: 1.0,
                }],
                vec![invariant_id.to_string()],
            ))
        }
    }

    /// Determine severity based on invariant category
    fn determine_severity(&self, category: &InvariantCategory) -> Severity {
        match category {
            InvariantCategory::Authorization => Severity::High,
            InvariantCategory::Monetary => Severity::Critical,
            InvariantCategory::Workflow => Severity::Medium,
            InvariantCategory::Trust => Severity::High,
            InvariantCategory::DataIntegrity => Severity::High,
            InvariantCategory::SessionManagement => Severity::High,
            InvariantCategory::InputValidation => Severity::Medium,
            InvariantCategory::RateLimiting => Severity::Low,
            InvariantCategory::Custom => Severity::Medium,
        }
    }

    /// Check if a finding should be classified as a bug
    pub fn is_bug(&self, result: &ValidationResult) -> bool {
        !result.violations.is_empty()
    }

    /// Check if a finding should be classified as a signal (not a bug)
    pub fn is_signal(&self, result: &ValidationResult) -> bool {
        result.violations.is_empty() && result.classification == FindingClassification::Signal
    }

    /// Get the catalog reference
    pub fn catalog(&self) -> &InvariantCatalog {
        &self.catalog
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::state::ApplicationState;

    #[test]
    fn test_validator_creation() {
        let catalog = Arc::new(InvariantCatalog::new());
        let validator = InvariantValidator::new(catalog);
        assert!(validator.catalog().count() > 0);
    }

    #[test]
    fn test_valid_transition() {
        let catalog = Arc::new(InvariantCatalog::new());
        let validator = InvariantValidator::new(catalog);
        
        let before = ApplicationState::default();
        let after = ApplicationState::default();
        
        let result = validator.validate_transition(&before, &after);
        assert!(result.is_valid);
        assert!(result.violations.is_empty());
    }

    #[test]
    fn test_severity_determination() {
        let catalog = Arc::new(InvariantCatalog::new());
        let validator = InvariantValidator::new(catalog);
        
        assert_eq!(
            validator.determine_severity(&InvariantCategory::Monetary),
            Severity::Critical
        );
        assert_eq!(
            validator.determine_severity(&InvariantCategory::Authorization),
            Severity::High
        );
    }
}