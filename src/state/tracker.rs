//! State Tracker - Tracks ownership, balances, sessions, and workflows

use super::{ApplicationState, SessionState, DataObject, StateTransition, Action, ActionType};
use crate::types::*;
use chrono::{DateTime, Utc};
use parking_lot::RwLock;
use std::collections::{HashMap, HashSet};
use uuid::Uuid;

/// Main state tracker that coordinates all tracking subsystems
pub struct StateTracker {
    ownership: OwnershipTracker,
    balance: BalanceMonitor,
    session: SessionTracker,
    current_state: RwLock<ApplicationState>,
}

impl StateTracker {
    pub fn new() -> Self {
        Self {
            ownership: OwnershipTracker::new(),
            balance: BalanceMonitor::new(),
            session: SessionTracker::new(),
            current_state: RwLock::new(ApplicationState::new()),
        }
    }

    /// Capture current state snapshot
    pub fn capture_state(&self) -> ApplicationState {
        self.current_state.read().clone()
    }

    /// Update state and return the transition
    pub fn update_state(&self, new_state: ApplicationState, action: Action) -> StateTransition {
        let mut current = self.current_state.write();
        let from_state = current.clone();
        
        let transition = StateTransition {
            id: Uuid::new_v4().to_string(),
            from_state,
            to_state: new_state.clone(),
            triggering_action: action,
            timestamp: Utc::now(),
        };
        
        *current = new_state;
        transition
    }

    /// Get ownership tracker
    pub fn ownership(&self) -> &OwnershipTracker {
        &self.ownership
    }

    /// Get balance monitor
    pub fn balance(&self) -> &BalanceMonitor {
        &self.balance
    }

    /// Get session tracker
    pub fn session(&self) -> &SessionTracker {
        &self.session
    }

    /// Apply ownership change
    pub fn set_ownership(&self, object_id: ObjectId, user_id: UserId) {
        self.ownership.set_owner(object_id.clone(), user_id.clone());
        self.current_state.write().ownership.insert(object_id, user_id);
    }

    /// Apply balance change
    pub fn set_balance(&self, account_id: AccountId, balance: Balance) {
        self.balance.set_balance(account_id.clone(), balance);
        self.current_state.write().balances.insert(account_id, balance);
    }

    /// Set current session
    pub fn set_session(&self, session: SessionState) {
        self.session.set_current(session.clone());
        self.current_state.write().current_session = Some(session);
    }
}

impl Default for StateTracker {
    fn default() -> Self {
        Self::new()
    }
}

/// Tracks object ownership and access patterns
pub struct OwnershipTracker {
    ownership: RwLock<HashMap<ObjectId, UserId>>,
    access_log: RwLock<Vec<AccessRecord>>,
}

/// Record of object access
#[derive(Debug, Clone)]
pub struct AccessRecord {
    pub object_id: ObjectId,
    pub user_id: UserId,
    pub access_type: AccessType,
    pub timestamp: DateTime<Utc>,
    pub authorized: bool,
}

/// Types of access
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AccessType {
    Read,
    Write,
    Delete,
    Transfer,
}

impl OwnershipTracker {
    pub fn new() -> Self {
        Self {
            ownership: RwLock::new(HashMap::new()),
            access_log: RwLock::new(Vec::new()),
        }
    }

    /// Set owner of an object
    pub fn set_owner(&self, object_id: ObjectId, user_id: UserId) {
        self.ownership.write().insert(object_id, user_id);
    }

    /// Get owner of an object
    pub fn get_owner(&self, object_id: &ObjectId) -> Option<UserId> {
        self.ownership.read().get(object_id).cloned()
    }

    /// Check if user owns object
    pub fn is_owner(&self, object_id: &ObjectId, user_id: &UserId) -> bool {
        self.ownership.read().get(object_id).map(|o| o == user_id).unwrap_or(false)
    }

    /// Record an access attempt
    pub fn record_access(&self, object_id: ObjectId, user_id: UserId, access_type: AccessType, authorized: bool) {
        self.access_log.write().push(AccessRecord {
            object_id,
            user_id,
            access_type,
            timestamp: Utc::now(),
            authorized,
        });
    }

    /// Get access history for an object
    pub fn get_access_history(&self, object_id: &ObjectId) -> Vec<AccessRecord> {
        self.access_log.read()
            .iter()
            .filter(|r| &r.object_id == object_id)
            .cloned()
            .collect()
    }

    /// Check for unauthorized access attempts
    pub fn get_unauthorized_accesses(&self) -> Vec<AccessRecord> {
        self.access_log.read()
            .iter()
            .filter(|r| !r.authorized)
            .cloned()
            .collect()
    }
}

impl Default for OwnershipTracker {
    fn default() -> Self {
        Self::new()
    }
}

/// Monitors financial state changes
pub struct BalanceMonitor {
    balances: RwLock<HashMap<AccountId, Balance>>,
    transactions: RwLock<Vec<TransactionRecord>>,
}

/// Record of a financial transaction
#[derive(Debug, Clone)]
pub struct TransactionRecord {
    pub id: String,
    pub from_account: Option<AccountId>,
    pub to_account: Option<AccountId>,
    pub amount: i64,
    pub currency: Currency,
    pub balance_before: Option<Balance>,
    pub balance_after: Option<Balance>,
    pub timestamp: DateTime<Utc>,
}

impl BalanceMonitor {
    pub fn new() -> Self {
        Self {
            balances: RwLock::new(HashMap::new()),
            transactions: RwLock::new(Vec::new()),
        }
    }

    /// Set balance for an account
    pub fn set_balance(&self, account_id: AccountId, balance: Balance) {
        self.balances.write().insert(account_id, balance);
    }

    /// Get balance for an account
    pub fn get_balance(&self, account_id: &AccountId) -> Option<Balance> {
        self.balances.read().get(account_id).copied()
    }

    /// Record a transaction
    pub fn record_transaction(
        &self,
        from: Option<AccountId>,
        to: Option<AccountId>,
        amount: i64,
        currency: Currency,
    ) -> String {
        let id = Uuid::new_v4().to_string();
        
        let balance_before = from.as_ref().and_then(|a| self.get_balance(a));
        
        // Apply transaction
        if let Some(ref from_account) = from {
            if let Some(mut balance) = self.get_balance(from_account) {
                balance.amount -= amount;
                self.set_balance(from_account.clone(), balance);
            }
        }
        
        if let Some(ref to_account) = to {
            let mut balance = self.get_balance(to_account)
                .unwrap_or(Balance::zero(currency));
            balance.amount += amount;
            self.set_balance(to_account.clone(), balance);
        }
        
        let balance_after = from.as_ref().and_then(|a| self.get_balance(a));
        
        self.transactions.write().push(TransactionRecord {
            id: id.clone(),
            from_account: from,
            to_account: to,
            amount,
            currency,
            balance_before,
            balance_after,
            timestamp: Utc::now(),
        });
        
        id
    }

    /// Get total system balance
    pub fn get_total_balance(&self, currency: Currency) -> i64 {
        self.balances.read()
            .values()
            .filter(|b| b.currency == currency)
            .map(|b| b.amount)
            .sum()
    }

    /// Check balance conservation
    pub fn verify_conservation(&self, currency: Currency, expected_total: i64) -> bool {
        self.get_total_balance(currency) == expected_total
    }

    /// Get transaction history
    pub fn get_transactions(&self) -> Vec<TransactionRecord> {
        self.transactions.read().clone()
    }
}

impl Default for BalanceMonitor {
    fn default() -> Self {
        Self::new()
    }
}

/// Tracks user sessions and roles
pub struct SessionTracker {
    current_session: RwLock<Option<SessionState>>,
    session_history: RwLock<Vec<SessionEvent>>,
    role_changes: RwLock<Vec<RoleChangeEvent>>,
}

/// Session event record
#[derive(Debug, Clone)]
pub struct SessionEvent {
    pub session_id: SessionId,
    pub event_type: SessionEventType,
    pub timestamp: DateTime<Utc>,
}

/// Types of session events
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SessionEventType {
    Created,
    Authenticated,
    RoleChanged,
    Expired,
    Terminated,
}

/// Role change event
#[derive(Debug, Clone)]
pub struct RoleChangeEvent {
    pub session_id: SessionId,
    pub user_id: UserId,
    pub role: Role,
    pub change_type: RoleChangeType,
    pub timestamp: DateTime<Utc>,
}

/// Types of role changes
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RoleChangeType {
    Added,
    Removed,
}

impl SessionTracker {
    pub fn new() -> Self {
        Self {
            current_session: RwLock::new(None),
            session_history: RwLock::new(Vec::new()),
            role_changes: RwLock::new(Vec::new()),
        }
    }

    /// Set current session
    pub fn set_current(&self, session: SessionState) {
        let event = SessionEvent {
            session_id: session.session_id.clone(),
            event_type: if session.authenticated {
                SessionEventType::Authenticated
            } else {
                SessionEventType::Created
            },
            timestamp: Utc::now(),
        };
        
        self.session_history.write().push(event);
        *self.current_session.write() = Some(session);
    }

    /// Get current session
    pub fn get_current(&self) -> Option<SessionState> {
        self.current_session.read().clone()
    }

    /// Record role change
    pub fn record_role_change(&self, user_id: UserId, role: Role, change_type: RoleChangeType) {
        if let Some(session) = self.get_current() {
            self.role_changes.write().push(RoleChangeEvent {
                session_id: session.session_id,
                user_id,
                role,
                change_type,
                timestamp: Utc::now(),
            });
        }
    }

    /// Check if current session has role
    pub fn has_role(&self, role: &Role) -> bool {
        self.current_session.read()
            .as_ref()
            .map(|s| s.roles.contains(role))
            .unwrap_or(false)
    }

    /// Get all roles for current session
    pub fn get_roles(&self) -> HashSet<Role> {
        self.current_session.read()
            .as_ref()
            .map(|s| s.roles.clone())
            .unwrap_or_default()
    }

    /// Terminate current session
    pub fn terminate(&self) {
        if let Some(session) = self.current_session.write().take() {
            self.session_history.write().push(SessionEvent {
                session_id: session.session_id,
                event_type: SessionEventType::Terminated,
                timestamp: Utc::now(),
            });
        }
    }

    /// Get session history
    pub fn get_history(&self) -> Vec<SessionEvent> {
        self.session_history.read().clone()
    }

    /// Get role change history
    pub fn get_role_changes(&self) -> Vec<RoleChangeEvent> {
        self.role_changes.read().clone()
    }
}

impl Default for SessionTracker {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_state_tracker_creation() {
        let tracker = StateTracker::new();
        let state = tracker.capture_state();
        assert!(state.timestamp.is_some());
    }

    #[test]
    fn test_ownership_tracking() {
        let tracker = OwnershipTracker::new();
        let obj_id = ObjectId("obj1".to_string());
        let user_id = UserId("user1".to_string());
        
        tracker.set_owner(obj_id.clone(), user_id.clone());
        
        assert!(tracker.is_owner(&obj_id, &user_id));
        assert_eq!(tracker.get_owner(&obj_id), Some(user_id));
    }

    #[test]
    fn test_balance_monitoring() {
        let monitor = BalanceMonitor::new();
        let account = AccountId("acc1".to_string());
        
        monitor.set_balance(account.clone(), Balance::new(1000, Currency::USD));
        
        assert_eq!(monitor.get_balance(&account).unwrap().amount, 1000);
    }

    #[test]
    fn test_transaction_recording() {
        let monitor = BalanceMonitor::new();
        let from = AccountId("from".to_string());
        let to = AccountId("to".to_string());
        
        monitor.set_balance(from.clone(), Balance::new(1000, Currency::USD));
        monitor.set_balance(to.clone(), Balance::new(500, Currency::USD));
        
        monitor.record_transaction(Some(from.clone()), Some(to.clone()), 200, Currency::USD);
        
        assert_eq!(monitor.get_balance(&from).unwrap().amount, 800);
        assert_eq!(monitor.get_balance(&to).unwrap().amount, 700);
    }

    #[test]
    fn test_session_tracking() {
        let tracker = SessionTracker::new();
        
        let session = SessionState {
            session_id: SessionId("sess1".to_string()),
            user_id: UserId("user1".to_string()),
            roles: HashSet::from([Role("admin".to_string())]),
            authenticated: true,
            created_at: Utc::now(),
            last_activity: Utc::now(),
        };
        
        tracker.set_current(session);
        
        assert!(tracker.has_role(&Role("admin".to_string())));
        assert!(!tracker.has_role(&Role("guest".to_string())));
    }
}