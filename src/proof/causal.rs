//! Causal Engine - Establishes cause-effect relationships

use crate::state::{Action, ApplicationState, StateTransition};
use crate::types::*;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// A link in the causal chain
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CausalLink {
    pub action: Action,
    pub state_changes: Vec<StateChange>,
    pub confidence: f64,
    pub timestamp: DateTime<Utc>,
}

/// Description of a state change
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StateChange {
    pub change_type: StateChangeType,
    pub field: String,
    pub old_value: Option<serde_json::Value>,
    pub new_value: Option<serde_json::Value>,
}

/// Types of state changes
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum StateChangeType {
    OwnershipChange,
    BalanceChange,
    RoleChange,
    WorkflowAdvance,
    DataModification,
    SessionChange,
    Custom(String),
}

/// Complete causal chain from action to effect
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CausalChain {
    pub links: Vec<CausalLink>,
    pub root_action: Option<Action>,
    pub final_effect: Option<StateChange>,
    pub is_complete: bool,
    pub confidence: f64,
}

impl CausalChain {
    pub fn new() -> Self {
        Self {
            links: Vec::new(),
            root_action: None,
            final_effect: None,
            is_complete: false,
            confidence: 0.0,
        }
    }

    /// Check if chain is complete (has root action and final effect)
    pub fn is_complete(&self) -> bool {
        self.is_complete && self.root_action.is_some() && self.final_effect.is_some()
    }

    /// Add a link to the chain
    pub fn add_link(&mut self, link: CausalLink) {
        if self.links.is_empty() {
            self.root_action = Some(link.action.clone());
        }
        
        if let Some(last_change) = link.state_changes.last() {
            self.final_effect = Some(last_change.clone());
        }
        
        self.links.push(link);
        self.update_confidence();
    }

    /// Update overall chain confidence
    fn update_confidence(&mut self) {
        if self.links.is_empty() {
            self.confidence = 0.0;
            return;
        }
        
        // Chain confidence is product of individual link confidences
        self.confidence = self.links.iter()
            .map(|l| l.confidence)
            .product();
    }

    /// Mark chain as complete
    pub fn complete(&mut self) {
        self.is_complete = !self.links.is_empty() && 
                          self.root_action.is_some() && 
                          self.final_effect.is_some();
    }

    /// Get chain length
    pub fn len(&self) -> usize {
        self.links.len()
    }

    /// Check if chain is empty
    pub fn is_empty(&self) -> bool {
        self.links.is_empty()
    }
}

impl Default for CausalChain {
    fn default() -> Self {
        Self::new()
    }
}

/// Engine for establishing causal relationships
pub struct CausalEngine {
    attribution_rules: Vec<AttributionRule>,
}

/// Rule for attributing state changes to actions
pub struct AttributionRule {
    pub name: String,
    pub matcher: Box<dyn Fn(&Action, &StateChange) -> bool + Send + Sync>,
    pub confidence: f64,
}

impl CausalEngine {
    pub fn new() -> Self {
        let mut engine = Self {
            attribution_rules: Vec::new(),
        };
        engine.register_default_rules();
        engine
    }

    /// Register default attribution rules
    fn register_default_rules(&mut self) {
        // HTTP request -> state change attribution
        self.attribution_rules.push(AttributionRule {
            name: "http_request_attribution".to_string(),
            matcher: Box::new(|action, change| {
                // HTTP requests can cause any state change
                action.request.is_some()
            }),
            confidence: 0.9,
        });

        // Authentication action -> session change
        self.attribution_rules.push(AttributionRule {
            name: "auth_session_attribution".to_string(),
            matcher: Box::new(|action, change| {
                matches!(action.action_type, crate::state::ActionType::Authentication) &&
                matches!(change.change_type, StateChangeType::SessionChange)
            }),
            confidence: 0.95,
        });

        // Payment action -> balance change
        self.attribution_rules.push(AttributionRule {
            name: "payment_balance_attribution".to_string(),
            matcher: Box::new(|action, change| {
                matches!(action.action_type, crate::state::ActionType::Payment) &&
                matches!(change.change_type, StateChangeType::BalanceChange)
            }),
            confidence: 0.98,
        });
    }

    /// Build causal chain from state transition
    pub fn build_chain(&self, transition: &StateTransition) -> CausalChain {
        let mut chain = CausalChain::new();
        
        let state_changes = self.detect_state_changes(&transition.from_state, &transition.to_state);
        
        if state_changes.is_empty() {
            return chain;
        }

        // Find best matching rule for each change
        let mut attributed_changes = Vec::new();
        for change in state_changes {
            let best_rule = self.attribution_rules.iter()
                .filter(|rule| (rule.matcher)(&transition.triggering_action, &change))
                .max_by(|a, b| a.confidence.partial_cmp(&b.confidence).unwrap());
            
            if let Some(rule) = best_rule {
                attributed_changes.push((change, rule.confidence));
            }
        }

        if !attributed_changes.is_empty() {
            let avg_confidence = attributed_changes.iter()
                .map(|(_, c)| c)
                .sum::<f64>() / attributed_changes.len() as f64;
            
            chain.add_link(CausalLink {
                action: transition.triggering_action.clone(),
                state_changes: attributed_changes.into_iter().map(|(c, _)| c).collect(),
                confidence: avg_confidence,
                timestamp: transition.timestamp,
            });
            
            chain.complete();
        }

        chain
    }

    /// Detect state changes between two states
    fn detect_state_changes(&self, before: &ApplicationState, after: &ApplicationState) -> Vec<StateChange> {
        let mut changes = Vec::new();

        // Check ownership changes
        for (obj_id, new_owner) in &after.ownership {
            let old_owner = before.ownership.get(obj_id);
            if old_owner != Some(new_owner) {
                changes.push(StateChange {
                    change_type: StateChangeType::OwnershipChange,
                    field: format!("ownership.{}", obj_id.0),
                    old_value: old_owner.map(|o| serde_json::json!(o.0)),
                    new_value: Some(serde_json::json!(new_owner.0)),
                });
            }
        }

        // Check balance changes
        for (acc_id, new_balance) in &after.balances {
            let old_balance = before.balances.get(acc_id);
            if old_balance.map(|b| b.amount) != Some(new_balance.amount) {
                changes.push(StateChange {
                    change_type: StateChangeType::BalanceChange,
                    field: format!("balances.{}", acc_id.0),
                    old_value: old_balance.map(|b| serde_json::json!(b.amount)),
                    new_value: Some(serde_json::json!(new_balance.amount)),
                });
            }
        }

        // Check session changes
        match (&before.current_session, &after.current_session) {
            (None, Some(session)) => {
                changes.push(StateChange {
                    change_type: StateChangeType::SessionChange,
                    field: "current_session".to_string(),
                    old_value: None,
                    new_value: Some(serde_json::json!(session.session_id.0)),
                });
            }
            (Some(old), Some(new)) if old.session_id != new.session_id => {
                changes.push(StateChange {
                    change_type: StateChangeType::SessionChange,
                    field: "current_session".to_string(),
                    old_value: Some(serde_json::json!(old.session_id.0)),
                    new_value: Some(serde_json::json!(new.session_id.0)),
                });
            }
            _ => {}
        }

        // Check workflow changes
        for (session_id, new_step) in &after.workflow_positions {
            let old_step = before.workflow_positions.get(session_id);
            if old_step.map(|s| s.step_index) != Some(new_step.step_index) {
                changes.push(StateChange {
                    change_type: StateChangeType::WorkflowAdvance,
                    field: format!("workflow.{}", session_id.0),
                    old_value: old_step.map(|s| serde_json::json!(s.step_index)),
                    new_value: Some(serde_json::json!(new_step.step_index)),
                });
            }
        }

        changes
    }

    /// Validate that an action caused a specific effect
    pub fn validate_causality(&self, action: &Action, effect: &StateChange) -> bool {
        self.attribution_rules.iter()
            .any(|rule| (rule.matcher)(action, effect))
    }

    /// Get confidence that action caused effect
    pub fn get_causality_confidence(&self, action: &Action, effect: &StateChange) -> f64 {
        self.attribution_rules.iter()
            .filter(|rule| (rule.matcher)(action, effect))
            .map(|rule| rule.confidence)
            .max_by(|a, b| a.partial_cmp(b).unwrap())
            .unwrap_or(0.0)
    }
}

impl Default for CausalEngine {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_causal_chain_creation() {
        let chain = CausalChain::new();
        assert!(chain.is_empty());
        assert!(!chain.is_complete());
    }

    #[test]
    fn test_causal_engine_creation() {
        let engine = CausalEngine::new();
        assert!(!engine.attribution_rules.is_empty());
    }

    #[test]
    fn test_state_change_detection() {
        let engine = CausalEngine::new();
        
        let mut before = ApplicationState::default();
        let mut after = ApplicationState::default();
        
        // Add a balance change
        after.balances.insert(
            AccountId("acc1".to_string()),
            Balance::new(1000, Currency::USD),
        );
        
        let changes = engine.detect_state_changes(&before, &after);
        assert!(!changes.is_empty());
        assert!(changes.iter().any(|c| matches!(c.change_type, StateChangeType::BalanceChange)));
    }
}