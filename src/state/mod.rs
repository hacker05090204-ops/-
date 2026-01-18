//! State Tracking Module - Maintains authoritative state records
//! 
//! This module implements the state ledger and tracking systems for
//! ownership, balances, roles, and workflow positions.

mod ledger;
mod tracker;

pub use ledger::{StateLedger, StateSnapshot};
pub use tracker::{StateTracker, OwnershipTracker, BalanceMonitor, SessionTracker, AccessType};

use crate::types::*;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};

/// Complete application state at a point in time
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct ApplicationState {
    pub timestamp: Option<DateTime<Utc>>,
    pub ownership: HashMap<ObjectId, UserId>,
    pub balances: HashMap<AccountId, Balance>,
    pub workflow_positions: HashMap<SessionId, WorkflowStep>,
    pub current_session: Option<SessionState>,
    pub data_objects: HashMap<ObjectId, DataObject>,
    pub authorization_events: Vec<AuthorizationEvent>,
    pub financial_transactions: Vec<FinancialTransaction>,
    pub overdraft_permissions: HashSet<AccountId>,
    pub trust_decisions: Vec<TrustDecision>,
    pub workflow_completions: Vec<WorkflowCompletion>,
}

/// Session state information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionState {
    pub session_id: SessionId,
    pub user_id: UserId,
    pub roles: HashSet<Role>,
    pub authenticated: bool,
    pub created_at: DateTime<Utc>,
    pub last_activity: DateTime<Utc>,
}

/// Data object representation
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DataObject {
    pub id: ObjectId,
    pub data_type: String,
    pub content_hash: String,
    pub last_modified: DateTime<Utc>,
    pub version: u64,
}

/// Authorization event record
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuthorizationEvent {
    pub event_type: String,
    pub user_id: UserId,
    pub target_role: Option<Role>,
    pub timestamp: DateTime<Utc>,
    pub authorized_by: Option<UserId>,
}

/// Financial transaction record
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FinancialTransaction {
    pub id: String,
    pub from_account: Option<AccountId>,
    pub to_account: Option<AccountId>,
    pub amount: i64,
    pub currency: Currency,
    pub is_external: bool,
    pub timestamp: DateTime<Utc>,
}

/// Trust decision record
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrustDecision {
    pub decision_type: String,
    pub based_on_client_input: bool,
    pub input_validated: bool,
    pub timestamp: DateTime<Utc>,
}

/// Workflow completion record
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowCompletion {
    pub workflow_id: String,
    pub is_critical: bool,
    pub all_steps_completed: bool,
    pub completed_steps: Vec<u32>,
    pub timestamp: DateTime<Utc>,
}

/// State transition between two application states
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StateTransition {
    pub id: String,
    pub from_state: ApplicationState,
    pub to_state: ApplicationState,
    pub triggering_action: Action,
    pub timestamp: DateTime<Utc>,
}

/// Action that triggered a state transition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Action {
    pub id: String,
    pub action_type: ActionType,
    pub request: Option<HttpRequest>,
    pub parameters: HashMap<String, serde_json::Value>,
    pub authentication: Option<AuthToken>,
    pub timing: ActionTiming,
}

/// Types of actions
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ActionType {
    HttpRequest,
    DatabaseQuery,
    FileOperation,
    Authentication,
    Authorization,
    Payment,
    WorkflowStep,
    Custom(String),
}

impl ApplicationState {
    pub fn new() -> Self {
        Self {
            timestamp: Some(Utc::now()),
            ..Default::default()
        }
    }

    /// Create a snapshot of the current state
    pub fn snapshot(&self) -> StateSnapshot {
        StateSnapshot {
            state: self.clone(),
            captured_at: Utc::now(),
        }
    }

    /// Check if a user owns an object
    pub fn user_owns(&self, user_id: &UserId, object_id: &ObjectId) -> bool {
        self.ownership.get(object_id).map(|o| o == user_id).unwrap_or(false)
    }

    /// Get balance for an account
    pub fn get_balance(&self, account_id: &AccountId) -> Option<&Balance> {
        self.balances.get(account_id)
    }

    /// Get current workflow step for a session
    pub fn get_workflow_step(&self, session_id: &SessionId) -> Option<&WorkflowStep> {
        self.workflow_positions.get(session_id)
    }
}