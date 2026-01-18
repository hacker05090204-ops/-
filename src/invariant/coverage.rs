//! Coverage Tracker - Maps invariant coverage and identifies gaps

use super::catalog::{InvariantCatalog, InvariantCategory};
use crate::state::StateTransition;
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use std::sync::Arc;
use parking_lot::RwLock;

/// Coverage gap information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CoverageGap {
    pub category: InvariantCategory,
    pub description: String,
    pub uncovered_transitions: Vec<String>,
    pub severity: GapSeverity,
}

/// Severity of coverage gaps
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum GapSeverity {
    Low,
    Medium,
    High,
    Critical,
}

/// Coverage report for invariant validation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CoverageReport {
    pub total_invariants: usize,
    pub covered_invariants: usize,
    pub coverage_percentage: f64,
    pub gaps: Vec<CoverageGap>,
    pub by_category: HashMap<InvariantCategory, CategoryCoverage>,
    pub uncovered_transition_types: Vec<String>,
    pub is_complete: bool,
}

/// Coverage information for a specific category
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CategoryCoverage {
    pub total: usize,
    pub covered: usize,
    pub percentage: f64,
    pub uncovered_ids: Vec<String>,
}

/// Tracks invariant coverage across state transitions
pub struct CoverageTracker {
    catalog: Arc<InvariantCatalog>,
    covered_invariants: RwLock<HashSet<String>>,
    observed_transitions: RwLock<Vec<TransitionType>>,
    unclassified_transitions: RwLock<Vec<String>>,
}

/// Type of state transition observed
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct TransitionType {
    pub category: String,
    pub action: String,
    pub state_changes: Vec<String>,
}

impl CoverageTracker {
    pub fn new(catalog: Arc<InvariantCatalog>) -> Self {
        Self {
            catalog,
            covered_invariants: RwLock::new(HashSet::new()),
            observed_transitions: RwLock::new(Vec::new()),
            unclassified_transitions: RwLock::new(Vec::new()),
        }
    }

    /// Record that an invariant was checked
    pub fn record_check(&self, invariant_id: &str) {
        self.covered_invariants.write().insert(invariant_id.to_string());
    }

    /// Record multiple invariant checks
    pub fn record_checks(&self, invariant_ids: &[String]) {
        let mut covered = self.covered_invariants.write();
        for id in invariant_ids {
            covered.insert(id.clone());
        }
    }

    /// Record an observed state transition
    pub fn record_transition(&self, transition: TransitionType) {
        self.observed_transitions.write().push(transition);
    }

    /// Record a transition that couldn't be classified under any invariant
    pub fn record_unclassified(&self, description: String) {
        self.unclassified_transitions.write().push(description);
    }

    /// Generate a coverage report
    pub fn generate_report(&self) -> CoverageReport {
        let covered = self.covered_invariants.read();
        let total = self.catalog.count();
        let covered_count = covered.len();
        
        let coverage_percentage = if total > 0 {
            (covered_count as f64 / total as f64) * 100.0
        } else {
            0.0
        };

        let mut by_category = HashMap::new();
        let categories = [
            InvariantCategory::Authorization,
            InvariantCategory::Monetary,
            InvariantCategory::Workflow,
            InvariantCategory::Trust,
            InvariantCategory::DataIntegrity,
            InvariantCategory::SessionManagement,
            InvariantCategory::InputValidation,
            InvariantCategory::RateLimiting,
            InvariantCategory::Custom,
        ];

        for category in categories {
            let invariants = self.catalog.get_by_category(category);
            let total_in_cat = invariants.len();
            let covered_in_cat: Vec<_> = invariants
                .iter()
                .filter(|inv| covered.contains(&inv.id))
                .collect();
            
            let uncovered_ids: Vec<_> = invariants
                .iter()
                .filter(|inv| !covered.contains(&inv.id))
                .map(|inv| inv.id.clone())
                .collect();

            let percentage = if total_in_cat > 0 {
                (covered_in_cat.len() as f64 / total_in_cat as f64) * 100.0
            } else {
                100.0
            };

            by_category.insert(category, CategoryCoverage {
                total: total_in_cat,
                covered: covered_in_cat.len(),
                percentage,
                uncovered_ids,
            });
        }

        let gaps = self.identify_gaps(&by_category);
        let unclassified = self.unclassified_transitions.read().clone();

        CoverageReport {
            total_invariants: total,
            covered_invariants: covered_count,
            coverage_percentage,
            gaps,
            by_category,
            uncovered_transition_types: unclassified,
            is_complete: false, // Never claim completeness
        }
    }

    /// Identify coverage gaps
    fn identify_gaps(&self, by_category: &HashMap<InvariantCategory, CategoryCoverage>) -> Vec<CoverageGap> {
        let mut gaps = Vec::new();

        for (category, coverage) in by_category {
            if coverage.percentage < 100.0 {
                let severity = match category {
                    InvariantCategory::Monetary => GapSeverity::Critical,
                    InvariantCategory::Authorization => GapSeverity::High,
                    InvariantCategory::Trust => GapSeverity::High,
                    InvariantCategory::SessionManagement => GapSeverity::High,
                    InvariantCategory::DataIntegrity => GapSeverity::Medium,
                    InvariantCategory::Workflow => GapSeverity::Medium,
                    InvariantCategory::RateLimiting => GapSeverity::Medium,
                    InvariantCategory::InputValidation => GapSeverity::Low,
                    InvariantCategory::Custom => GapSeverity::Low,
                };

                gaps.push(CoverageGap {
                    category: *category,
                    description: format!(
                        "{:?} invariants: {}/{} covered ({:.1}%)",
                        category, coverage.covered, coverage.total, coverage.percentage
                    ),
                    uncovered_transitions: coverage.uncovered_ids.clone(),
                    severity,
                });
            }
        }

        // Add gaps for unclassified transitions
        let unclassified = self.unclassified_transitions.read();
        if !unclassified.is_empty() {
            gaps.push(CoverageGap {
                category: InvariantCategory::Custom,
                description: format!(
                    "{} state transitions could not be classified under any invariant",
                    unclassified.len()
                ),
                uncovered_transitions: unclassified.clone(),
                severity: GapSeverity::Medium,
            });
        }

        gaps
    }

    /// Check if a specific invariant has been covered
    pub fn is_covered(&self, invariant_id: &str) -> bool {
        self.covered_invariants.read().contains(invariant_id)
    }

    /// Get list of uncovered invariants
    pub fn get_uncovered(&self) -> Vec<String> {
        let covered = self.covered_invariants.read();
        self.catalog
            .all()
            .filter(|inv| !covered.contains(&inv.id))
            .map(|inv| inv.id.clone())
            .collect()
    }

    /// Reset coverage tracking
    pub fn reset(&self) {
        self.covered_invariants.write().clear();
        self.observed_transitions.write().clear();
        self.unclassified_transitions.write().clear();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_coverage_tracker_creation() {
        let catalog = Arc::new(InvariantCatalog::new());
        let tracker = CoverageTracker::new(catalog);
        
        let report = tracker.generate_report();
        assert_eq!(report.covered_invariants, 0);
        assert!(!report.is_complete);
    }

    #[test]
    fn test_record_check() {
        let catalog = Arc::new(InvariantCatalog::new());
        let tracker = CoverageTracker::new(catalog);
        
        tracker.record_check("AUTH_001");
        assert!(tracker.is_covered("AUTH_001"));
        assert!(!tracker.is_covered("AUTH_002"));
    }

    #[test]
    fn test_coverage_report() {
        let catalog = Arc::new(InvariantCatalog::new());
        let tracker = CoverageTracker::new(Arc::clone(&catalog));
        
        // Record some checks
        for inv in catalog.all().take(3) {
            tracker.record_check(&inv.id);
        }
        
        let report = tracker.generate_report();
        assert_eq!(report.covered_invariants, 3);
        assert!(report.coverage_percentage > 0.0);
    }

    #[test]
    fn test_unclassified_transitions() {
        let catalog = Arc::new(InvariantCatalog::new());
        let tracker = CoverageTracker::new(catalog);
        
        tracker.record_unclassified("Unknown state change in payment flow".to_string());
        
        let report = tracker.generate_report();
        assert!(!report.uncovered_transition_types.is_empty());
    }
}