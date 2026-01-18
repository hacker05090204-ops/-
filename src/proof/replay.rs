//! Replay Engine - Deterministically reproduces findings

use crate::state::{Action, ApplicationState, StateTransition};
use crate::types::*;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Instructions for replaying a finding
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReplayInstructions {
    pub steps: Vec<ReplayStep>,
    pub initial_state_requirements: StateRequirements,
    pub expected_outcome: ExpectedOutcome,
    pub timing_constraints: Option<TimingConstraints>,
}

impl ReplayInstructions {
    pub fn new() -> Self {
        Self {
            steps: Vec::new(),
            initial_state_requirements: StateRequirements::default(),
            expected_outcome: ExpectedOutcome::default(),
            timing_constraints: None,
        }
    }

    /// Add a replay step
    pub fn add_step(&mut self, step: ReplayStep) {
        self.steps.push(step);
    }

    /// Check if instructions are complete
    pub fn is_complete(&self) -> bool {
        !self.steps.is_empty() && self.expected_outcome.invariant_violated.is_some()
    }
}

impl Default for ReplayInstructions {
    fn default() -> Self {
        Self::new()
    }
}

/// Single step in replay sequence
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReplayStep {
    pub sequence: u32,
    pub action: Action,
    pub expected_state_after: Option<StateAssertion>,
    pub wait_before_ms: Option<u64>,
    pub retry_on_failure: bool,
    pub max_retries: u32,
}

/// Assertion about expected state
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StateAssertion {
    pub assertions: Vec<Assertion>,
}

/// Individual assertion
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Assertion {
    pub field: String,
    pub operator: AssertionOperator,
    pub expected_value: serde_json::Value,
}

/// Assertion operators
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum AssertionOperator {
    Equals,
    NotEquals,
    GreaterThan,
    LessThan,
    Contains,
    NotContains,
    Exists,
    NotExists,
}

/// Requirements for initial state
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct StateRequirements {
    pub required_session: Option<SessionRequirement>,
    pub required_balances: HashMap<String, i64>,
    pub required_ownership: HashMap<String, String>,
    pub required_workflow_position: Option<u32>,
}

/// Session requirements
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionRequirement {
    pub authenticated: bool,
    pub required_roles: Vec<String>,
}

/// Expected outcome of replay
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct ExpectedOutcome {
    pub invariant_violated: Option<String>,
    pub state_changes: Vec<ExpectedStateChange>,
    pub error_expected: bool,
}

/// Expected state change
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExpectedStateChange {
    pub field: String,
    pub change_type: String,
}

/// Timing constraints for replay
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TimingConstraints {
    pub max_total_duration_ms: u64,
    pub min_step_interval_ms: u64,
    pub max_step_interval_ms: u64,
}

/// Result of replay attempt
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReplayResult {
    pub success: bool,
    pub steps_completed: u32,
    pub total_steps: u32,
    pub final_state: Option<ApplicationState>,
    pub invariant_violated: bool,
    pub error: Option<String>,
    pub duration_ms: u64,
    pub is_deterministic: bool,
}

impl ReplayResult {
    pub fn success(final_state: ApplicationState, steps: u32, duration_ms: u64) -> Self {
        Self {
            success: true,
            steps_completed: steps,
            total_steps: steps,
            final_state: Some(final_state),
            invariant_violated: true,
            error: None,
            duration_ms,
            is_deterministic: true,
        }
    }

    pub fn failure(error: String, steps_completed: u32, total_steps: u32) -> Self {
        Self {
            success: false,
            steps_completed,
            total_steps,
            final_state: None,
            invariant_violated: false,
            error: Some(error),
            duration_ms: 0,
            is_deterministic: false,
        }
    }
}

/// Engine for replaying action sequences
pub struct ReplayEngine {
    max_retries: u32,
    timeout_ms: u64,
}

impl ReplayEngine {
    pub fn new() -> Self {
        Self {
            max_retries: 3,
            timeout_ms: 30000,
        }
    }

    pub fn with_config(max_retries: u32, timeout_ms: u64) -> Self {
        Self {
            max_retries,
            timeout_ms,
        }
    }

    /// Generate replay instructions from a state transition
    pub fn generate_instructions(&self, transition: &StateTransition) -> ReplayInstructions {
        let mut instructions = ReplayInstructions::new();
        
        // Set initial state requirements based on before state
        instructions.initial_state_requirements = self.extract_requirements(&transition.from_state);
        
        // Add the triggering action as a replay step
        instructions.add_step(ReplayStep {
            sequence: 1,
            action: transition.triggering_action.clone(),
            expected_state_after: None,
            wait_before_ms: None,
            retry_on_failure: true,
            max_retries: self.max_retries,
        });
        
        instructions
    }

    /// Generate instructions from multiple transitions
    pub fn generate_from_sequence(&self, transitions: &[StateTransition]) -> ReplayInstructions {
        let mut instructions = ReplayInstructions::new();
        
        if let Some(first) = transitions.first() {
            instructions.initial_state_requirements = self.extract_requirements(&first.from_state);
        }
        
        for (i, transition) in transitions.iter().enumerate() {
            instructions.add_step(ReplayStep {
                sequence: (i + 1) as u32,
                action: transition.triggering_action.clone(),
                expected_state_after: None,
                wait_before_ms: if i > 0 { Some(100) } else { None },
                retry_on_failure: true,
                max_retries: self.max_retries,
            });
        }
        
        instructions
    }

    /// Extract state requirements from application state
    fn extract_requirements(&self, state: &ApplicationState) -> StateRequirements {
        let mut requirements = StateRequirements::default();
        
        // Extract session requirements
        if let Some(session) = &state.current_session {
            requirements.required_session = Some(SessionRequirement {
                authenticated: session.authenticated,
                required_roles: session.roles.iter().map(|r| r.0.clone()).collect(),
            });
        }
        
        // Extract balance requirements
        for (acc_id, balance) in &state.balances {
            requirements.required_balances.insert(acc_id.0.clone(), balance.amount);
        }
        
        // Extract ownership requirements
        for (obj_id, user_id) in &state.ownership {
            requirements.required_ownership.insert(obj_id.0.clone(), user_id.0.clone());
        }
        
        requirements
    }

    /// Validate that current state meets requirements
    pub fn validate_requirements(&self, state: &ApplicationState, requirements: &StateRequirements) -> bool {
        // Check session requirements
        if let Some(session_req) = &requirements.required_session {
            match &state.current_session {
                None => return false,
                Some(session) => {
                    if session_req.authenticated && !session.authenticated {
                        return false;
                    }
                    for role in &session_req.required_roles {
                        if !session.roles.iter().any(|r| &r.0 == role) {
                            return false;
                        }
                    }
                }
            }
        }
        
        // Check balance requirements
        for (acc_id, required_amount) in &requirements.required_balances {
            let account_id = AccountId(acc_id.clone());
            match state.balances.get(&account_id) {
                None => return false,
                Some(balance) if balance.amount < *required_amount => return false,
                _ => {}
            }
        }
        
        // Check ownership requirements
        for (obj_id, required_owner) in &requirements.required_ownership {
            let object_id = ObjectId(obj_id.clone());
            let user_id = UserId(required_owner.clone());
            match state.ownership.get(&object_id) {
                None => return false,
                Some(owner) if owner != &user_id => return false,
                _ => {}
            }
        }
        
        true
    }

    /// Check if replay result is deterministic
    pub fn is_deterministic(&self, results: &[ReplayResult]) -> bool {
        if results.len() < 2 {
            return true;
        }
        
        // All results should have same success status and invariant violation
        let first = &results[0];
        results.iter().all(|r| {
            r.success == first.success && 
            r.invariant_violated == first.invariant_violated
        })
    }
}

impl Default for ReplayEngine {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::state::{ActionType, Action};
    use std::collections::HashMap;

    fn create_test_action() -> Action {
        Action {
            id: "test_action".to_string(),
            action_type: ActionType::HttpRequest,
            request: None,
            parameters: HashMap::new(),
            authentication: None,
            timing: ActionTiming {
                start_time: Utc::now(),
                end_time: Utc::now(),
                duration_ms: 100,
            },
        }
    }

    #[test]
    fn test_replay_instructions_creation() {
        let instructions = ReplayInstructions::new();
        assert!(instructions.steps.is_empty());
        assert!(!instructions.is_complete());
    }

    #[test]
    fn test_replay_engine_creation() {
        let engine = ReplayEngine::new();
        assert_eq!(engine.max_retries, 3);
    }

    #[test]
    fn test_requirements_validation() {
        let engine = ReplayEngine::new();
        let state = ApplicationState::default();
        let requirements = StateRequirements::default();
        
        assert!(engine.validate_requirements(&state, &requirements));
    }

    #[test]
    fn test_determinism_check() {
        let engine = ReplayEngine::new();
        
        let results = vec![
            ReplayResult::success(ApplicationState::default(), 1, 100),
            ReplayResult::success(ApplicationState::default(), 1, 150),
        ];
        
        assert!(engine.is_deterministic(&results));
    }
}