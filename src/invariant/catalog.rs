//! Security Invariant Catalog - Defines all security invariants
//!
//! This module implements the formal invariant definitions for security validation.
//! Each invariant represents a property that must hold across all state transitions.
//!
//! **Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 43.1, 43.2, 43.4**

use crate::state::ApplicationState;
use crate::types::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;

/// Categories of security invariants
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum InvariantCategory {
    /// Authorization and access control invariants
    Authorization,
    /// Financial and monetary invariants
    Monetary,
    /// Business workflow invariants
    Workflow,
    /// Trust boundary invariants
    Trust,
    /// Data integrity invariants
    DataIntegrity,
    /// Session management invariants
    SessionManagement,
    /// Input validation invariants
    InputValidation,
    /// Rate limiting and resource invariants
    RateLimiting,
    /// Custom user-defined invariants
    Custom,
}

/// Security invariant definition with full provenance
#[derive(Clone)]
pub struct SecurityInvariant {
    pub id: String,
    pub name: String,
    pub description: String,
    pub category: InvariantCategory,
    pub validator: Arc<dyn Fn(&ApplicationState, &ApplicationState) -> bool + Send + Sync>,
    pub violation_message: String,
    /// Provenance: Why this invariant exists and what security principle it enforces
    pub provenance: InvariantProvenance,
}

/// Provenance information for an invariant - documents why it exists
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InvariantProvenance {
    /// The security principle this invariant enforces (e.g., "Principle of Least Privilege")
    pub security_principle: String,
    /// Known assumptions this invariant makes about the target system
    pub assumptions: Vec<String>,
    /// Known blind spots - what this invariant cannot detect
    pub blind_spots: Vec<String>,
    /// Reference to security standards (e.g., "OWASP ASVS 4.0.3 - V4.1.1")
    pub standards_reference: Option<String>,
    /// When this invariant was added/last reviewed
    pub last_reviewed: Option<String>,
}

impl std::fmt::Debug for SecurityInvariant {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("SecurityInvariant")
            .field("id", &self.id)
            .field("name", &self.name)
            .field("category", &self.category)
            .finish()
    }
}

impl SecurityInvariant {
    pub fn new(
        id: impl Into<String>,
        name: impl Into<String>,
        description: impl Into<String>,
        category: InvariantCategory,
        violation_message: impl Into<String>,
        validator: impl Fn(&ApplicationState, &ApplicationState) -> bool + Send + Sync + 'static,
    ) -> Self {
        Self {
            id: id.into(),
            name: name.into(),
            description: description.into(),
            category,
            validator: Arc::new(validator),
            violation_message: violation_message.into(),
            provenance: InvariantProvenance::default(),
        }
    }

    /// Create invariant with full provenance documentation
    pub fn with_provenance(
        id: impl Into<String>,
        name: impl Into<String>,
        description: impl Into<String>,
        category: InvariantCategory,
        violation_message: impl Into<String>,
        provenance: InvariantProvenance,
        validator: impl Fn(&ApplicationState, &ApplicationState) -> bool + Send + Sync + 'static,
    ) -> Self {
        Self {
            id: id.into(),
            name: name.into(),
            description: description.into(),
            category,
            validator: Arc::new(validator),
            violation_message: violation_message.into(),
            provenance,
        }
    }

    /// Validate state transition against this invariant
    pub fn validate(&self, before: &ApplicationState, after: &ApplicationState) -> bool {
        (self.validator)(before, after)
    }
}

/// Catalog of all defined security invariants
pub struct InvariantCatalog {
    invariants: HashMap<String, SecurityInvariant>,
    by_category: HashMap<InvariantCategory, Vec<String>>,
}

impl Default for InvariantProvenance {
    fn default() -> Self {
        Self {
            security_principle: "Unspecified".to_string(),
            assumptions: Vec::new(),
            blind_spots: Vec::new(),
            standards_reference: None,
            last_reviewed: None,
        }
    }
}

impl InvariantCatalog {
    /// Create a new catalog with default security invariants
    pub fn new() -> Self {
        let mut catalog = Self {
            invariants: HashMap::new(),
            by_category: HashMap::new(),
        };
        catalog.register_default_invariants();
        catalog
    }

    /// Register default security invariants
    fn register_default_invariants(&mut self) {
        self.register_authorization_invariants();
        self.register_monetary_invariants();
        self.register_workflow_invariants();
        self.register_trust_invariants();
        self.register_data_integrity_invariants();
        self.register_session_invariants();
        self.register_input_validation_invariants();
    }

    /// Register authorization invariants
    fn register_authorization_invariants(&mut self) {
        self.register(SecurityInvariant::with_provenance(
            "AUTH_001",
            "Cross-User Object Access",
            "User A cannot access objects owned by User B without explicit permission",
            InvariantCategory::Authorization,
            "Unauthorized cross-user object access detected",
            InvariantProvenance {
                security_principle: "Principle of Least Privilege / Object-Level Authorization".to_string(),
                assumptions: vec![
                    "Ownership is tracked accurately in state".to_string(),
                    "Session user_id correctly identifies the acting user".to_string(),
                ],
                blind_spots: vec![
                    "Cannot detect indirect access via shared resources".to_string(),
                    "Does not cover implicit permissions from group membership".to_string(),
                ],
                standards_reference: Some("OWASP ASVS 4.0.3 - V4.2.1 (Object Level Access Control)".to_string()),
                last_reviewed: Some("2024-12".to_string()),
            },
            |before, after| {
                for (obj_id, owner_id) in &after.ownership {
                    if let Some(before_owner) = before.ownership.get(obj_id) {
                        if before_owner != owner_id {
                            if let Some(session) = &after.current_session {
                                if session.user_id != *before_owner && 
                                   !session.roles.iter().any(|r| r.0 == "admin") {
                                    return false;
                                }
                            }
                        }
                    }
                }
                true
            },
        ));

        self.register(SecurityInvariant::with_provenance(
            "AUTH_002",
            "Privilege Escalation Prevention",
            "User cannot gain privileges without proper authorization flow",
            InvariantCategory::Authorization,
            "Unauthorized privilege escalation detected",
            InvariantProvenance {
                security_principle: "Defense in Depth / Privilege Separation".to_string(),
                assumptions: vec![
                    "Role grants are recorded in authorization_events".to_string(),
                    "Session roles accurately reflect current privileges".to_string(),
                ],
                blind_spots: vec![
                    "Cannot detect privilege escalation via misconfigured backend".to_string(),
                    "Does not cover temporary privilege grants".to_string(),
                ],
                standards_reference: Some("OWASP ASVS 4.0.3 - V4.1.2 (Privilege Escalation)".to_string()),
                last_reviewed: Some("2024-12".to_string()),
            },
            |before, after| {
                if let (Some(before_session), Some(after_session)) = 
                    (&before.current_session, &after.current_session) {
                    let new_roles: Vec<_> = after_session.roles
                        .difference(&before_session.roles)
                        .collect();
                    
                    if !new_roles.is_empty() {
                        return after.authorization_events.iter().any(|e| {
                            e.event_type == "role_grant" && 
                            new_roles.iter().any(|r| e.target_role.as_ref() == Some(*r))
                        });
                    }
                }
                true
            },
        ));

        self.register(SecurityInvariant::with_provenance(
            "AUTH_003",
            "Horizontal Privilege Boundary",
            "User cannot access resources of another user at the same privilege level",
            InvariantCategory::Authorization,
            "Horizontal privilege boundary violation detected",
            InvariantProvenance {
                security_principle: "Horizontal Access Control / IDOR Prevention".to_string(),
                assumptions: vec![
                    "Object ownership is correctly tracked".to_string(),
                    "Data object access is recorded in state".to_string(),
                ],
                blind_spots: vec![
                    "Cannot detect access via API endpoints that don't track objects".to_string(),
                    "Does not cover shared/public resources".to_string(),
                ],
                standards_reference: Some("CWE-639 (Authorization Bypass Through User-Controlled Key)".to_string()),
                last_reviewed: Some("2024-12".to_string()),
            },
            |before, after| {
                if let Some(session) = &after.current_session {
                    for (obj_id, _) in &after.data_objects {
                        if let Some(owner) = after.ownership.get(obj_id) {
                            if owner != &session.user_id {
                                // Accessing another user's object
                                // Check if this is a new access (object wasn't accessed before)
                                if !before.data_objects.contains_key(obj_id) {
                                    // New object access - must be admin or have explicit permission
                                    if !session.roles.iter().any(|r| r.0 == "admin" || r.0 == "moderator") {
                                        return false;
                                    }
                                }
                            }
                        }
                    }
                }
                true
            },
        ));

        self.register(SecurityInvariant::with_provenance(
            "AUTH_004",
            "Vertical Privilege Boundary",
            "Lower privilege users cannot perform higher privilege actions",
            InvariantCategory::Authorization,
            "Vertical privilege boundary violation detected",
            InvariantProvenance {
                security_principle: "Role-Based Access Control / Vertical Privilege Separation".to_string(),
                assumptions: vec![
                    "Admin actions are tagged in authorization_events".to_string(),
                    "Session roles accurately reflect privilege level".to_string(),
                ],
                blind_spots: vec![
                    "Cannot detect privilege bypass via direct database access".to_string(),
                    "Does not cover actions not tagged as admin_action".to_string(),
                ],
                standards_reference: Some("OWASP ASVS 4.0.3 - V4.1.1 (Vertical Access Control)".to_string()),
                last_reviewed: Some("2024-12".to_string()),
            },
            |before, after| {
                // Check for admin-only actions performed by non-admins
                for event in &after.authorization_events {
                    if event.event_type == "admin_action" {
                        if let Some(session) = &after.current_session {
                            if !session.roles.iter().any(|r| r.0 == "admin") {
                                return false;
                            }
                        } else {
                            return false;
                        }
                    }
                }
                true
            },
        ));
    }

    /// Register monetary invariants
    fn register_monetary_invariants(&mut self) {
        self.register(SecurityInvariant::new(
            "MON_001",
            "Balance Conservation",
            "Total system balance must be conserved (no money creation/destruction)",
            InvariantCategory::Monetary,
            "Balance conservation violation - money created or destroyed",
            |before, after| {
                let total_before: i64 = before.balances.values()
                    .map(|b| b.amount)
                    .sum();
                let total_after: i64 = after.balances.values()
                    .map(|b| b.amount)
                    .sum();
                
                let external_delta: i64 = after.financial_transactions.iter()
                    .filter(|t| t.is_external)
                    .map(|t| t.amount)
                    .sum();
                
                total_after == total_before + external_delta
            },
        ));

        self.register(SecurityInvariant::new(
            "MON_002",
            "Non-Negative Balance",
            "Account balances cannot go negative without explicit overdraft permission",
            InvariantCategory::Monetary,
            "Negative balance detected without overdraft permission",
            |_before, after| {
                for (account_id, balance) in &after.balances {
                    if balance.amount < 0 && !after.overdraft_permissions.contains(account_id) {
                        return false;
                    }
                }
                true
            },
        ));

        self.register(SecurityInvariant::new(
            "MON_003",
            "Transaction Atomicity",
            "Financial transactions must be atomic - all or nothing",
            InvariantCategory::Monetary,
            "Partial transaction detected - atomicity violation",
            |before, after| {
                for tx in &after.financial_transactions {
                    if let (Some(from), Some(to)) = (&tx.from_account, &tx.to_account) {
                        let from_delta = after.balances.get(from).map(|b| b.amount).unwrap_or(0)
                            - before.balances.get(from).map(|b| b.amount).unwrap_or(0);
                        let to_delta = after.balances.get(to).map(|b| b.amount).unwrap_or(0)
                            - before.balances.get(to).map(|b| b.amount).unwrap_or(0);
                        
                        // Deltas should be equal and opposite (ignoring sign)
                        if from_delta.abs() != to_delta.abs() {
                            return false;
                        }
                    }
                }
                true
            },
        ));

        self.register(SecurityInvariant::new(
            "MON_004",
            "Double Spend Prevention",
            "Same funds cannot be spent twice in concurrent transactions",
            InvariantCategory::Monetary,
            "Double spend attempt detected",
            |before, after| {
                // Check if any account went below what it should have
                for (account_id, after_balance) in &after.balances {
                    if let Some(before_balance) = before.balances.get(account_id) {
                        let total_debits: i64 = after.financial_transactions.iter()
                            .filter(|t| t.from_account.as_ref() == Some(account_id))
                            .map(|t| t.amount)
                            .sum();
                        
                        let expected_balance = before_balance.amount - total_debits;
                        if after_balance.amount < expected_balance {
                            return false;
                        }
                    }
                }
                true
            },
        ));
    }

    /// Register workflow invariants
    fn register_workflow_invariants(&mut self) {
        self.register(SecurityInvariant::new(
            "WF_001",
            "Workflow Step Ordering",
            "Workflow step N cannot be reached without completing step N-1",
            InvariantCategory::Workflow,
            "Workflow step ordering violation - step skipped",
            |before, after| {
                for (session_id, after_step) in &after.workflow_positions {
                    if let Some(before_step) = before.workflow_positions.get(session_id) {
                        if after_step.step_index > before_step.step_index + 1 {
                            return false;
                        }
                    } else if after_step.step_index > 1 {
                        return false;
                    }
                }
                true
            },
        ));

        self.register(SecurityInvariant::new(
            "WF_002",
            "Workflow Completion Requirement",
            "Critical workflows must be completed before final action",
            InvariantCategory::Workflow,
            "Critical workflow not completed before final action",
            |_before, after| {
                for completion in &after.workflow_completions {
                    if completion.is_critical && !completion.all_steps_completed {
                        return false;
                    }
                }
                true
            },
        ));

        self.register(SecurityInvariant::new(
            "WF_003",
            "Workflow State Consistency",
            "Workflow state must be consistent with completed steps",
            InvariantCategory::Workflow,
            "Workflow state inconsistency detected",
            |_before, after| {
                for completion in &after.workflow_completions {
                    // Completed steps should be sequential
                    let mut sorted_steps = completion.completed_steps.clone();
                    sorted_steps.sort();
                    
                    for (i, step) in sorted_steps.iter().enumerate() {
                        if *step != (i as u32) && *step != (i as u32 + 1) {
                            // Gap in completed steps
                            return false;
                        }
                    }
                }
                true
            },
        ));
    }

    /// Register trust boundary invariants
    fn register_trust_invariants(&mut self) {
        self.register(SecurityInvariant::new(
            "TRUST_001",
            "Client Input Trust Boundary",
            "Client-controlled input cannot determine server trust decisions",
            InvariantCategory::Trust,
            "Client input used in trust decision without validation",
            |_before, after| {
                for decision in &after.trust_decisions {
                    if decision.based_on_client_input && !decision.input_validated {
                        return false;
                    }
                }
                true
            },
        ));

        self.register(SecurityInvariant::new(
            "TRUST_002",
            "Server-Side Validation Required",
            "All security-critical decisions must be validated server-side",
            InvariantCategory::Trust,
            "Security decision made without server-side validation",
            |_before, after| {
                for decision in &after.trust_decisions {
                    if decision.decision_type.contains("security") || 
                       decision.decision_type.contains("auth") ||
                       decision.decision_type.contains("access") {
                        if !decision.input_validated {
                            return false;
                        }
                    }
                }
                true
            },
        ));
    }

    /// Register data integrity invariants
    fn register_data_integrity_invariants(&mut self) {
        self.register(SecurityInvariant::new(
            "DATA_001",
            "Data Modification Authorization",
            "Data can only be modified by authorized users",
            InvariantCategory::DataIntegrity,
            "Unauthorized data modification detected",
            |before, after| {
                for (obj_id, after_data) in &after.data_objects {
                    if let Some(before_data) = before.data_objects.get(obj_id) {
                        if before_data != after_data {
                            if let Some(session) = &after.current_session {
                                let owner = after.ownership.get(obj_id);
                                let is_owner = owner.map(|o| o == &session.user_id).unwrap_or(false);
                                let is_admin = session.roles.iter().any(|r| r.0 == "admin");
                                
                                if !is_owner && !is_admin {
                                    return false;
                                }
                            } else {
                                return false;
                            }
                        }
                    }
                }
                true
            },
        ));

        self.register(SecurityInvariant::new(
            "DATA_002",
            "Data Version Monotonicity",
            "Data versions must only increase, never decrease",
            InvariantCategory::DataIntegrity,
            "Data version regression detected",
            |before, after| {
                for (obj_id, after_data) in &after.data_objects {
                    if let Some(before_data) = before.data_objects.get(obj_id) {
                        if after_data.version < before_data.version {
                            return false;
                        }
                    }
                }
                true
            },
        ));
    }

    /// Register session management invariants
    fn register_session_invariants(&mut self) {
        self.register(SecurityInvariant::new(
            "SESS_001",
            "Session Fixation Prevention",
            "Session ID must change after authentication",
            InvariantCategory::SessionManagement,
            "Session fixation vulnerability - session ID not rotated after auth",
            |before, after| {
                if before.current_session.is_none() && after.current_session.is_some() {
                    return true;
                }
                
                if let (Some(before_session), Some(after_session)) = 
                    (&before.current_session, &after.current_session) {
                    if !before_session.authenticated && after_session.authenticated {
                        return before_session.session_id != after_session.session_id;
                    }
                }
                true
            },
        ));

        self.register(SecurityInvariant::new(
            "SESS_002",
            "Session User Binding",
            "Session cannot be transferred to a different user",
            InvariantCategory::SessionManagement,
            "Session user binding violation - session transferred",
            |before, after| {
                if let (Some(before_session), Some(after_session)) = 
                    (&before.current_session, &after.current_session) {
                    if before_session.session_id == after_session.session_id {
                        // Same session - user must not change
                        return before_session.user_id == after_session.user_id;
                    }
                }
                true
            },
        ));
    }

    /// Register input validation invariants
    fn register_input_validation_invariants(&mut self) {
        self.register(SecurityInvariant::new(
            "INPUT_001",
            "Input Length Bounds",
            "All inputs must be within defined length bounds",
            InvariantCategory::InputValidation,
            "Input length bounds violation detected",
            |_before, after| {
                // Check data objects for reasonable sizes
                for (_, data) in &after.data_objects {
                    // Content hash should be reasonable length (SHA-256 = 64 hex chars)
                    if data.content_hash.len() > 128 {
                        return false;
                    }
                    // Data type should be reasonable
                    if data.data_type.len() > 256 {
                        return false;
                    }
                }
                true
            },
        ));
    }

    /// Register a new invariant
    pub fn register(&mut self, invariant: SecurityInvariant) {
        let id = invariant.id.clone();
        let category = invariant.category;
        
        self.invariants.insert(id.clone(), invariant);
        self.by_category
            .entry(category)
            .or_insert_with(Vec::new)
            .push(id);
    }

    /// Get an invariant by ID
    pub fn get(&self, id: &str) -> Option<&SecurityInvariant> {
        self.invariants.get(id)
    }

    /// Get all invariants in a category
    pub fn get_by_category(&self, category: InvariantCategory) -> Vec<&SecurityInvariant> {
        self.by_category
            .get(&category)
            .map(|ids| ids.iter().filter_map(|id| self.invariants.get(id)).collect())
            .unwrap_or_default()
    }

    /// Get all invariants
    pub fn all(&self) -> impl Iterator<Item = &SecurityInvariant> {
        self.invariants.values()
    }

    /// Get total count of invariants
    pub fn count(&self) -> usize {
        self.invariants.len()
    }

    /// Get count by category
    pub fn count_by_category(&self, category: InvariantCategory) -> usize {
        self.by_category.get(&category).map(|v| v.len()).unwrap_or(0)
    }
}

impl Default for InvariantCatalog {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_catalog_initialization() {
        let catalog = InvariantCatalog::new();
        assert!(catalog.count() > 0, "Catalog should have default invariants");
    }

    #[test]
    fn test_invariant_categories() {
        let catalog = InvariantCatalog::new();
        
        assert!(catalog.count_by_category(InvariantCategory::Authorization) > 0);
        assert!(catalog.count_by_category(InvariantCategory::Monetary) > 0);
        assert!(catalog.count_by_category(InvariantCategory::Workflow) > 0);
        assert!(catalog.count_by_category(InvariantCategory::Trust) > 0);
    }

    #[test]
    fn test_custom_invariant_registration() {
        let mut catalog = InvariantCatalog::new();
        let initial_count = catalog.count();
        
        catalog.register(SecurityInvariant::new(
            "CUSTOM_001",
            "Custom Test Invariant",
            "Test invariant for unit testing",
            InvariantCategory::Custom,
            "Custom invariant violated",
            |_, _| true,
        ));
        
        assert_eq!(catalog.count(), initial_count + 1);
        assert!(catalog.get("CUSTOM_001").is_some());
    }
}