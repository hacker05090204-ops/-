//! Property-based tests for invariant engine
//!
//! **Task 2: Implement core invariant engine and catalog**
//! **Property Tests: 2.1, 2.2, 2.3**
//!
//! Requirements validated:
//! - 15.1: Universal Invariant Definition
//! - 15.2: Invariant Evaluation Completeness
//! - 15.3: False Positive Rejection

use kali_mcp_core::invariant::{
    InvariantCatalog, InvariantCategory, InvariantValidator, SecurityInvariant,
    CoverageTracker, CoverageGap,
};
use kali_mcp_core::state::{
    ApplicationState, SessionState, DataObject,
    TrustDecision, WorkflowCompletion, FinancialTransaction,
};
use kali_mcp_core::types::*;
use chrono::Utc;
use std::collections::{HashMap, HashSet};
use std::sync::Arc;

// ============================================================================
// Test Helpers - Generate valid test data
// ============================================================================

fn create_user_id(id: u32) -> UserId {
    UserId(format!("user_{}", id))
}

fn create_object_id(id: u32) -> ObjectId {
    ObjectId(format!("object_{}", id))
}

fn create_account_id(id: u32) -> AccountId {
    AccountId(format!("account_{}", id))
}

fn create_session_id(id: u32) -> SessionId {
    SessionId(format!("session_{}", id))
}

fn create_session_state(user_id: u32, roles: Vec<&str>, authenticated: bool) -> SessionState {
    SessionState {
        session_id: create_session_id(user_id),
        user_id: create_user_id(user_id),
        roles: roles.into_iter().map(|r| Role(r.to_string())).collect(),
        authenticated,
        created_at: Utc::now(),
        last_activity: Utc::now(),
    }
}

fn create_base_state() -> ApplicationState {
    ApplicationState {
        timestamp: Some(Utc::now()),
        ownership: HashMap::new(),
        balances: HashMap::new(),
        workflow_positions: HashMap::new(),
        current_session: None,
        data_objects: HashMap::new(),
        authorization_events: Vec::new(),
        financial_transactions: Vec::new(),
        overdraft_permissions: HashSet::new(),
        trust_decisions: Vec::new(),
        workflow_completions: Vec::new(),
    }
}

// ============================================================================
// Property Test 2.1: Universal Invariant Definition
// **Validates: Requirements 15.1**
// ============================================================================

#[cfg(test)]
mod property_test_2_1 {
    use super::*;
    use quickcheck::TestResult;
    use quickcheck_macros::quickcheck;

    /// Property: Every invariant must have a unique ID
    #[test]
    fn prop_invariant_ids_are_unique() {
        let catalog = InvariantCatalog::new();
        let mut seen_ids = HashSet::new();
        
        for invariant in catalog.all() {
            assert!(
                seen_ids.insert(invariant.id.clone()),
                "Duplicate invariant ID found: {}",
                invariant.id
            );
        }
    }

    /// Property: Every invariant must belong to exactly one category
    #[test]
    fn prop_invariant_has_single_category() {
        let catalog = InvariantCatalog::new();
        
        for invariant in catalog.all() {
            // Category is a single enum value, so this is guaranteed by type system
            // But we verify the category is valid
            let category = invariant.category;
            let invariants_in_category = catalog.get_by_category(category);
            
            assert!(
                invariants_in_category.iter().any(|i| i.id == invariant.id),
                "Invariant {} not found in its declared category {:?}",
                invariant.id,
                category
            );
        }
    }

    /// Property: Invariant validation is deterministic
    #[quickcheck]
    fn prop_validation_is_deterministic(seed: u32) -> bool {
        let catalog = Arc::new(InvariantCatalog::new());
        let validator = InvariantValidator::new(Arc::clone(&catalog));
        
        let before = create_base_state();
        let after = create_base_state();
        
        // Run validation multiple times
        let result1 = validator.validate_transition(&before, &after);
        let result2 = validator.validate_transition(&before, &after);
        let result3 = validator.validate_transition(&before, &after);
        
        // Results must be identical
        result1.is_valid == result2.is_valid 
            && result2.is_valid == result3.is_valid
            && result1.violations.len() == result2.violations.len()
            && result2.violations.len() == result3.violations.len()
    }

    /// Property: Empty state transitions are always valid
    #[test]
    fn prop_empty_transitions_valid() {
        let catalog = Arc::new(InvariantCatalog::new());
        let validator = InvariantValidator::new(catalog);
        
        let state = create_base_state();
        let result = validator.validate_transition(&state, &state);
        
        assert!(result.is_valid, "Empty transition should be valid");
        assert!(result.violations.is_empty(), "No violations for empty transition");
    }

    /// Property: All categories have at least one invariant
    #[test]
    fn prop_all_categories_have_invariants() {
        let catalog = InvariantCatalog::new();
        
        let required_categories = [
            InvariantCategory::Authorization,
            InvariantCategory::Monetary,
            InvariantCategory::Workflow,
            InvariantCategory::Trust,
            InvariantCategory::DataIntegrity,
            InvariantCategory::SessionManagement,
        ];
        
        for category in required_categories {
            assert!(
                catalog.count_by_category(category) > 0,
                "Category {:?} has no invariants",
                category
            );
        }
    }

    /// Property: Invariant descriptions are non-empty
    #[test]
    fn prop_invariant_descriptions_non_empty() {
        let catalog = InvariantCatalog::new();
        
        for invariant in catalog.all() {
            assert!(!invariant.name.is_empty(), "Invariant {} has empty name", invariant.id);
            assert!(!invariant.description.is_empty(), "Invariant {} has empty description", invariant.id);
            assert!(!invariant.violation_message.is_empty(), "Invariant {} has empty violation message", invariant.id);
        }
    }
}

// ============================================================================
// Property Test 2.2: Invariant Evaluation Completeness
// **Validates: Requirements 15.2**
// ============================================================================

#[cfg(test)]
mod property_test_2_2 {
    use super::*;
    use quickcheck_macros::quickcheck;

    /// Property: All registered invariants are checked during validation
    #[test]
    fn prop_all_invariants_checked() {
        let catalog = Arc::new(InvariantCatalog::new());
        let validator = InvariantValidator::new(Arc::clone(&catalog));
        
        let before = create_base_state();
        let after = create_base_state();
        
        let result = validator.validate_transition(&before, &after);
        
        // All invariants should be in checked list
        assert_eq!(
            result.checked_invariants.len(),
            catalog.count(),
            "Not all invariants were checked"
        );
    }

    /// Property: Category-specific validation only checks relevant invariants
    #[test]
    fn prop_category_validation_is_scoped() {
        let catalog = Arc::new(InvariantCatalog::new());
        let validator = InvariantValidator::new(Arc::clone(&catalog));
        
        let before = create_base_state();
        let after = create_base_state();
        
        let categories = [InvariantCategory::Authorization];
        let result = validator.validate_categories(&before, &after, &categories);
        
        // Only authorization invariants should be checked
        let auth_count = catalog.count_by_category(InvariantCategory::Authorization);
        assert_eq!(
            result.checked_invariants.len(),
            auth_count,
            "Category validation checked wrong number of invariants"
        );
    }

    /// Property: Specific invariant validation returns result for that invariant
    #[test]
    fn prop_specific_invariant_validation() {
        let catalog = Arc::new(InvariantCatalog::new());
        let validator = InvariantValidator::new(Arc::clone(&catalog));
        
        let before = create_base_state();
        let after = create_base_state();
        
        // Validate specific invariant
        let result = validator.validate_invariant("AUTH_001", &before, &after);
        
        assert!(result.is_some(), "Should return result for existing invariant");
        let result = result.unwrap();
        assert_eq!(result.checked_invariants.len(), 1);
        assert_eq!(result.checked_invariants[0], "AUTH_001");
    }

    /// Property: Non-existent invariant returns None
    #[test]
    fn prop_nonexistent_invariant_returns_none() {
        let catalog = Arc::new(InvariantCatalog::new());
        let validator = InvariantValidator::new(catalog);
        
        let before = create_base_state();
        let after = create_base_state();
        
        let result = validator.validate_invariant("NONEXISTENT_999", &before, &after);
        assert!(result.is_none(), "Should return None for non-existent invariant");
    }

    /// Property: Coverage tracker records all checks
    #[test]
    fn prop_coverage_tracker_records_checks() {
        let catalog = Arc::new(InvariantCatalog::new());
        let tracker = CoverageTracker::new(Arc::clone(&catalog));
        
        // Record some checks
        tracker.record_check("AUTH_001");
        tracker.record_check("MON_001");
        tracker.record_check("WF_001");
        
        assert!(tracker.is_covered("AUTH_001"));
        assert!(tracker.is_covered("MON_001"));
        assert!(tracker.is_covered("WF_001"));
        assert!(!tracker.is_covered("AUTH_002"));
    }

    /// Property: Coverage report accurately reflects checked invariants
    #[test]
    fn prop_coverage_report_accuracy() {
        let catalog = Arc::new(InvariantCatalog::new());
        let tracker = CoverageTracker::new(Arc::clone(&catalog));
        
        let total = catalog.count();
        
        // Check half the invariants
        for (i, inv) in catalog.all().enumerate() {
            if i % 2 == 0 {
                tracker.record_check(&inv.id);
            }
        }
        
        let report = tracker.generate_report();
        
        assert_eq!(report.total_invariants, total);
        assert!(report.coverage_percentage > 0.0);
        assert!(report.coverage_percentage < 100.0);
        assert!(!report.is_complete); // Never claim completeness
    }
}

// ============================================================================
// Property Test 2.3: False Positive Rejection
// **Validates: Requirements 15.3**
// ============================================================================

#[cfg(test)]
mod property_test_2_3 {
    use super::*;

    /// Property: Authorized ownership changes don't trigger violations
    #[test]
    fn prop_authorized_ownership_change_valid() {
        let catalog = Arc::new(InvariantCatalog::new());
        let validator = InvariantValidator::new(catalog);
        
        let obj_id = create_object_id(1);
        let user1 = create_user_id(1);
        let user2 = create_user_id(2);
        
        let mut before = create_base_state();
        before.ownership.insert(obj_id.clone(), user1.clone());
        before.current_session = Some(create_session_state(1, vec!["admin"], true));
        
        let mut after = before.clone();
        after.ownership.insert(obj_id, user2);
        
        let result = validator.validate_transition(&before, &after);
        
        // Admin can transfer ownership - should be valid
        assert!(result.is_valid, "Admin ownership transfer should be valid");
    }

    /// Property: Unauthorized ownership changes trigger violations
    #[test]
    fn prop_unauthorized_ownership_change_invalid() {
        let catalog = Arc::new(InvariantCatalog::new());
        let validator = InvariantValidator::new(catalog);
        
        let obj_id = create_object_id(1);
        let user1 = create_user_id(1);
        let user2 = create_user_id(2);
        let user3 = create_user_id(3);
        
        let mut before = create_base_state();
        before.ownership.insert(obj_id.clone(), user1.clone());
        // User 3 is not owner and not admin
        before.current_session = Some(create_session_state(3, vec!["user"], true));
        
        let mut after = before.clone();
        after.ownership.insert(obj_id, user2);
        
        let result = validator.validate_transition(&before, &after);
        
        // Non-owner, non-admin cannot transfer - should be invalid
        assert!(!result.is_valid, "Unauthorized ownership transfer should be invalid");
        assert!(
            result.violations.iter().any(|v| v.invariant_id == "AUTH_001"),
            "Should trigger AUTH_001 violation"
        );
    }

    /// Property: Balance conservation is enforced
    #[test]
    fn prop_balance_conservation_enforced() {
        let catalog = Arc::new(InvariantCatalog::new());
        let validator = InvariantValidator::new(catalog);
        
        let acc1 = create_account_id(1);
        let acc2 = create_account_id(2);
        
        let mut before = create_base_state();
        before.balances.insert(acc1.clone(), Balance::new(1000, Currency::USD));
        before.balances.insert(acc2.clone(), Balance::new(500, Currency::USD));
        
        // Valid transfer - total conserved with proper transaction record
        let mut after_valid = before.clone();
        after_valid.balances.insert(acc1.clone(), Balance::new(800, Currency::USD));
        after_valid.balances.insert(acc2.clone(), Balance::new(700, Currency::USD));
        // Add the financial transaction record
        after_valid.financial_transactions.push(FinancialTransaction {
            id: "tx_001".to_string(),
            from_account: Some(acc1.clone()),
            to_account: Some(acc2.clone()),
            amount: 200,
            currency: Currency::USD,
            is_external: false,
            timestamp: chrono::Utc::now(),
        });
        
        let result = validator.validate_transition(&before, &after_valid);
        if !result.is_valid {
            for v in &result.violations {
                eprintln!("Violation: {} - {} - {}", v.invariant_id, v.invariant_name, v.message);
            }
        }
        assert!(result.is_valid, "Conserved balance transfer with transaction record should be valid");
        
        // Invalid - money created (external deposit without is_external flag)
        let mut after_invalid = before.clone();
        after_invalid.balances.insert(acc1.clone(), Balance::new(1000, Currency::USD));
        after_invalid.balances.insert(acc2.clone(), Balance::new(700, Currency::USD)); // +200 from nowhere
        
        let result = validator.validate_transition(&before, &after_invalid);
        assert!(!result.is_valid, "Money creation without external transaction should be invalid");
    }

    /// Property: Workflow step skipping is detected
    #[test]
    fn prop_workflow_step_skipping_detected() {
        let catalog = Arc::new(InvariantCatalog::new());
        let validator = InvariantValidator::new(catalog);
        
        let session_id = create_session_id(1);
        
        let mut before = create_base_state();
        before.workflow_positions.insert(
            session_id.clone(),
            WorkflowStep {
                workflow_id: "checkout".to_string(),
                step_index: 1,
                step_name: "cart".to_string(),
            },
        );
        
        // Valid - go to step 2
        let mut after_valid = before.clone();
        after_valid.workflow_positions.insert(
            session_id.clone(),
            WorkflowStep {
                workflow_id: "checkout".to_string(),
                step_index: 2,
                step_name: "shipping".to_string(),
            },
        );
        
        let result = validator.validate_transition(&before, &after_valid);
        assert!(result.is_valid, "Sequential workflow step should be valid");
        
        // Invalid - skip to step 5
        let mut after_invalid = before.clone();
        after_invalid.workflow_positions.insert(
            session_id.clone(),
            WorkflowStep {
                workflow_id: "checkout".to_string(),
                step_index: 5,
                step_name: "complete".to_string(),
            },
        );
        
        let result = validator.validate_transition(&before, &after_invalid);
        assert!(!result.is_valid, "Workflow step skipping should be invalid");
    }

    /// Property: Session fixation is detected
    #[test]
    fn prop_session_fixation_detected() {
        let catalog = Arc::new(InvariantCatalog::new());
        let validator = InvariantValidator::new(catalog);
        
        let session_id = create_session_id(1);
        
        let mut before = create_base_state();
        before.current_session = Some(SessionState {
            session_id: session_id.clone(),
            user_id: create_user_id(1),
            roles: HashSet::new(),
            authenticated: false,
            created_at: Utc::now(),
            last_activity: Utc::now(),
        });
        
        // Invalid - same session ID after authentication
        let mut after_invalid = before.clone();
        after_invalid.current_session = Some(SessionState {
            session_id: session_id.clone(), // Same ID!
            user_id: create_user_id(1),
            roles: HashSet::new(),
            authenticated: true, // Now authenticated
            created_at: Utc::now(),
            last_activity: Utc::now(),
        });
        
        let result = validator.validate_transition(&before, &after_invalid);
        assert!(!result.is_valid, "Session fixation should be detected");
        
        // Valid - new session ID after authentication
        let mut after_valid = before.clone();
        after_valid.current_session = Some(SessionState {
            session_id: create_session_id(2), // New ID
            user_id: create_user_id(1),
            roles: HashSet::new(),
            authenticated: true,
            created_at: Utc::now(),
            last_activity: Utc::now(),
        });
        
        let result = validator.validate_transition(&before, &after_valid);
        assert!(result.is_valid, "Session rotation should be valid");
    }

    /// Property: Trust boundary violations are detected
    #[test]
    fn prop_trust_boundary_violation_detected() {
        let catalog = Arc::new(InvariantCatalog::new());
        let validator = InvariantValidator::new(catalog);
        
        let mut before = create_base_state();
        
        // Invalid - trust decision based on unvalidated client input
        let mut after_invalid = before.clone();
        after_invalid.trust_decisions.push(TrustDecision {
            decision_type: "access_grant".to_string(),
            based_on_client_input: true,
            input_validated: false, // Not validated!
            timestamp: Utc::now(),
        });
        
        let result = validator.validate_transition(&before, &after_invalid);
        assert!(!result.is_valid, "Unvalidated trust decision should be invalid");
        
        // Valid - trust decision with validated input
        let mut after_valid = before.clone();
        after_valid.trust_decisions.push(TrustDecision {
            decision_type: "access_grant".to_string(),
            based_on_client_input: true,
            input_validated: true, // Validated
            timestamp: Utc::now(),
        });
        
        let result = validator.validate_transition(&before, &after_valid);
        assert!(result.is_valid, "Validated trust decision should be valid");
    }

    /// Property: Severity is correctly assigned based on category
    #[test]
    fn prop_severity_assignment_correct() {
        let catalog = Arc::new(InvariantCatalog::new());
        let validator = InvariantValidator::new(catalog);
        
        // Create a monetary violation
        let acc1 = create_account_id(1);
        
        let mut before = create_base_state();
        before.balances.insert(acc1.clone(), Balance::new(1000, Currency::USD));
        
        let mut after = before.clone();
        after.balances.insert(acc1, Balance::new(2000, Currency::USD)); // Money created
        
        let result = validator.validate_transition(&before, &after);
        
        // Monetary violations should be Critical
        for violation in &result.violations {
            if violation.category == InvariantCategory::Monetary {
                assert_eq!(
                    violation.severity,
                    Severity::Critical,
                    "Monetary violations should be Critical severity"
                );
            }
        }
    }

    /// Property: Violations have high confidence (1.0) for invariant breaks
    #[test]
    fn prop_violation_confidence_is_high() {
        let catalog = Arc::new(InvariantCatalog::new());
        let validator = InvariantValidator::new(catalog);
        
        // Create any violation
        let acc1 = create_account_id(1);
        
        let mut before = create_base_state();
        before.balances.insert(acc1.clone(), Balance::new(1000, Currency::USD));
        
        let mut after = before.clone();
        after.balances.insert(acc1, Balance::new(2000, Currency::USD));
        
        let result = validator.validate_transition(&before, &after);
        
        for violation in &result.violations {
            assert_eq!(
                violation.confidence, 1.0,
                "Invariant violations should have confidence 1.0"
            );
        }
    }
}

// ============================================================================
// Integration Tests
// ============================================================================

#[cfg(test)]
mod integration_tests {
    use super::*;

    /// Test complete validation workflow
    #[test]
    fn test_complete_validation_workflow() {
        let catalog = Arc::new(InvariantCatalog::new());
        let validator = InvariantValidator::new(Arc::clone(&catalog));
        let tracker = CoverageTracker::new(Arc::clone(&catalog));
        
        // Create a complex state transition
        let mut before = create_base_state();
        before.current_session = Some(create_session_state(1, vec!["user"], true));
        before.ownership.insert(create_object_id(1), create_user_id(1));
        before.balances.insert(create_account_id(1), Balance::new(1000, Currency::USD));
        before.balances.insert(create_account_id(2), Balance::new(0, Currency::USD));
        
        let mut after = before.clone();
        // Valid changes by owner - internal transfer with transaction record
        after.balances.insert(create_account_id(1), Balance::new(800, Currency::USD));
        after.balances.insert(create_account_id(2), Balance::new(200, Currency::USD));
        // Add the financial transaction record
        after.financial_transactions.push(FinancialTransaction {
            id: "tx_001".to_string(),
            from_account: Some(create_account_id(1)),
            to_account: Some(create_account_id(2)),
            amount: 200,
            currency: Currency::USD,
            is_external: false,
            timestamp: chrono::Utc::now(),
        });
        
        // Validate
        let result = validator.validate_transition(&before, &after);
        
        // Record coverage
        tracker.record_checks(&result.checked_invariants);
        
        // Generate report
        let report = tracker.generate_report();
        
        if !result.is_valid {
            for v in &result.violations {
                eprintln!("Violation: {} - {} - {}", v.invariant_id, v.invariant_name, v.message);
            }
        }
        assert!(result.is_valid, "Internal transfer with transaction record should be valid");
        assert!(report.covered_invariants > 0);
        assert!(!report.is_complete); // Never claim completeness
    }

    /// Test that custom invariants can be added
    #[test]
    fn test_custom_invariant_registration() {
        let mut catalog = InvariantCatalog::new();
        let initial_count = catalog.count();
        
        // Add custom invariant
        catalog.register(SecurityInvariant::new(
            "CUSTOM_TEST_001",
            "Test Custom Invariant",
            "A custom invariant for testing",
            InvariantCategory::Custom,
            "Custom test invariant violated",
            |_before, _after| true,
        ));
        
        assert_eq!(catalog.count(), initial_count + 1);
        assert!(catalog.get("CUSTOM_TEST_001").is_some());
        assert_eq!(catalog.count_by_category(InvariantCategory::Custom), 1);
    }

    /// Test coverage gap identification
    #[test]
    fn test_coverage_gap_identification() {
        let catalog = Arc::new(InvariantCatalog::new());
        let tracker = CoverageTracker::new(Arc::clone(&catalog));
        
        // Only check authorization invariants
        for inv in catalog.get_by_category(InvariantCategory::Authorization) {
            tracker.record_check(&inv.id);
        }
        
        let report = tracker.generate_report();
        
        // Should have gaps in other categories
        assert!(!report.gaps.is_empty(), "Should identify coverage gaps");
        
        // Monetary gaps should be Critical severity
        for gap in &report.gaps {
            if gap.category == InvariantCategory::Monetary {
                assert_eq!(
                    gap.severity,
                    kali_mcp_core::invariant::GapSeverity::Critical
                );
            }
        }
    }
}
