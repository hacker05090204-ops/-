//! Property-based tests for state tracking and ledger system
//!
//! **Task 3: Build state tracking and ledger system**
//! **Property Tests: 3.1, 3.2**
//!
//! Requirements validated:
//! - 2A.1: Complete State Capture
//! - 2A.2: State Transition Recording
//! - 2A.3: State Integrity Verification
//! - 2A.4: Ownership and Access Tracking
//! - 2A.5: Balance Monitoring
//! - 28.1-28.5: State Ledger Requirements

use kali_mcp_core::state::{
    ApplicationState, StateTracker, StateLedger, StateSnapshot, StateTransition,
    SessionState, DataObject, Action, ActionType,
    OwnershipTracker, BalanceMonitor, SessionTracker,
};
use kali_mcp_core::types::*;
use chrono::Utc;
use std::collections::{HashMap, HashSet};

// ============================================================================
// Test Helpers
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

fn create_test_action(action_type: ActionType) -> Action {
    Action {
        id: uuid::Uuid::new_v4().to_string(),
        action_type,
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

fn create_test_transition(from: ApplicationState, to: ApplicationState) -> StateTransition {
    StateTransition {
        id: uuid::Uuid::new_v4().to_string(),
        from_state: from,
        to_state: to,
        triggering_action: create_test_action(ActionType::HttpRequest),
        timestamp: Utc::now(),
    }
}

// ============================================================================
// Property Test 3.1: Complete State Capture
// **Validates: Requirements 2A.1**
// ============================================================================

#[cfg(test)]
mod property_test_3_1 {
    use super::*;

    /// Property: State tracker captures all state components
    #[test]
    fn prop_state_captures_all_components() {
        let tracker = StateTracker::new();
        
        // Set various state components
        tracker.set_ownership(create_object_id(1), create_user_id(1));
        tracker.set_balance(create_account_id(1), Balance::new(1000, Currency::USD));
        
        let session = SessionState {
            session_id: create_session_id(1),
            user_id: create_user_id(1),
            roles: HashSet::from([Role("user".to_string())]),
            authenticated: true,
            created_at: Utc::now(),
            last_activity: Utc::now(),
        };
        tracker.set_session(session);
        
        // Capture state
        let state = tracker.capture_state();
        
        // Verify all components are captured
        assert!(state.ownership.contains_key(&create_object_id(1)));
        assert!(state.balances.contains_key(&create_account_id(1)));
        assert!(state.current_session.is_some());
        assert!(state.timestamp.is_some());
    }

    /// Property: State snapshots are immutable
    #[test]
    fn prop_state_snapshots_immutable() {
        let tracker = StateTracker::new();
        tracker.set_balance(create_account_id(1), Balance::new(1000, Currency::USD));
        
        let snapshot1 = tracker.capture_state();
        
        // Modify tracker
        tracker.set_balance(create_account_id(1), Balance::new(2000, Currency::USD));
        
        let snapshot2 = tracker.capture_state();
        
        // Snapshots should be different
        assert_ne!(
            snapshot1.balances.get(&create_account_id(1)).unwrap().amount,
            snapshot2.balances.get(&create_account_id(1)).unwrap().amount
        );
    }

    /// Property: State has timestamp
    #[test]
    fn prop_state_has_timestamp() {
        let state = ApplicationState::new();
        assert!(state.timestamp.is_some());
    }

    /// Property: Ledger records all transitions
    #[test]
    fn prop_ledger_records_all_transitions() {
        let ledger = StateLedger::new();
        
        let transitions: Vec<_> = (0..10)
            .map(|_| create_test_transition(
                ApplicationState::default(),
                ApplicationState::new()
            ))
            .collect();
        
        for transition in &transitions {
            ledger.record_transition(transition.clone());
        }
        
        assert_eq!(ledger.len(), 10);
    }

    /// Property: Ledger maintains sequence order
    #[test]
    fn prop_ledger_maintains_sequence() {
        let ledger = StateLedger::new();
        
        for _ in 0..5 {
            ledger.record_transition(create_test_transition(
                ApplicationState::default(),
                ApplicationState::new()
            ));
        }
        
        // Verify sequence numbers
        for i in 1..=5 {
            let entry = ledger.get_by_sequence(i as u64);
            assert!(entry.is_some());
            assert_eq!(entry.unwrap().sequence, i as u64);
        }
    }

    /// Property: Ledger integrity is verifiable
    #[test]
    fn prop_ledger_integrity_verifiable() {
        let ledger = StateLedger::new();
        
        for _ in 0..10 {
            ledger.record_transition(create_test_transition(
                ApplicationState::default(),
                ApplicationState::new()
            ));
        }
        
        assert!(ledger.verify_integrity());
    }

    /// Property: State snapshot hash is deterministic
    #[test]
    fn prop_snapshot_hash_deterministic() {
        let state = ApplicationState::default();
        let snapshot1 = StateSnapshot::new(state.clone());
        let snapshot2 = StateSnapshot::new(state);
        
        assert_eq!(snapshot1.hash(), snapshot2.hash());
    }
}

// ============================================================================
// Property Test 3.2: Ownership and Access Tracking
// **Validates: Requirements 2A.4**
// ============================================================================

#[cfg(test)]
mod property_test_3_2 {
    use super::*;
    use kali_mcp_core::state::AccessType;

    /// Property: Ownership is correctly tracked
    #[test]
    fn prop_ownership_correctly_tracked() {
        let tracker = OwnershipTracker::new();
        
        let obj1 = create_object_id(1);
        let obj2 = create_object_id(2);
        let user1 = create_user_id(1);
        let user2 = create_user_id(2);
        
        tracker.set_owner(obj1.clone(), user1.clone());
        tracker.set_owner(obj2.clone(), user2.clone());
        
        assert!(tracker.is_owner(&obj1, &user1));
        assert!(!tracker.is_owner(&obj1, &user2));
        assert!(tracker.is_owner(&obj2, &user2));
        assert!(!tracker.is_owner(&obj2, &user1));
    }

    /// Property: Ownership transfer is recorded
    #[test]
    fn prop_ownership_transfer_recorded() {
        let tracker = OwnershipTracker::new();
        
        let obj = create_object_id(1);
        let user1 = create_user_id(1);
        let user2 = create_user_id(2);
        
        tracker.set_owner(obj.clone(), user1.clone());
        assert_eq!(tracker.get_owner(&obj), Some(user1));
        
        tracker.set_owner(obj.clone(), user2.clone());
        assert_eq!(tracker.get_owner(&obj), Some(user2));
    }

    /// Property: Access attempts are logged
    #[test]
    fn prop_access_attempts_logged() {
        let tracker = OwnershipTracker::new();
        
        let obj = create_object_id(1);
        let user = create_user_id(1);
        
        tracker.record_access(obj.clone(), user.clone(), AccessType::Read, true);
        tracker.record_access(obj.clone(), user.clone(), AccessType::Write, false);
        
        let history = tracker.get_access_history(&obj);
        assert_eq!(history.len(), 2);
    }

    /// Property: Unauthorized accesses are identifiable
    #[test]
    fn prop_unauthorized_accesses_identifiable() {
        let tracker = OwnershipTracker::new();
        
        let obj = create_object_id(1);
        let user1 = create_user_id(1);
        let user2 = create_user_id(2);
        
        tracker.record_access(obj.clone(), user1, AccessType::Read, true);
        tracker.record_access(obj.clone(), user2, AccessType::Write, false);
        
        let unauthorized = tracker.get_unauthorized_accesses();
        assert_eq!(unauthorized.len(), 1);
    }

    /// Property: Balance monitor tracks all accounts
    #[test]
    fn prop_balance_monitor_tracks_accounts() {
        let monitor = BalanceMonitor::new();
        
        for i in 0..10 {
            monitor.set_balance(
                create_account_id(i),
                Balance::new((i as i64) * 100, Currency::USD)
            );
        }
        
        // Verify all balances
        for i in 0..10 {
            let balance = monitor.get_balance(&create_account_id(i));
            assert!(balance.is_some());
            assert_eq!(balance.unwrap().amount, (i as i64) * 100);
        }
    }

    /// Property: Balance transactions are atomic
    #[test]
    fn prop_balance_transactions_atomic() {
        let monitor = BalanceMonitor::new();
        
        let from = create_account_id(1);
        let to = create_account_id(2);
        
        monitor.set_balance(from.clone(), Balance::new(1000, Currency::USD));
        monitor.set_balance(to.clone(), Balance::new(500, Currency::USD));
        
        let initial_total = monitor.get_total_balance(Currency::USD);
        
        // Perform transaction
        monitor.record_transaction(Some(from.clone()), Some(to.clone()), 200, Currency::USD);
        
        let final_total = monitor.get_total_balance(Currency::USD);
        
        // Total should be conserved
        assert_eq!(initial_total, final_total);
        
        // Individual balances should be updated
        assert_eq!(monitor.get_balance(&from).unwrap().amount, 800);
        assert_eq!(monitor.get_balance(&to).unwrap().amount, 700);
    }

    /// Property: Session tracker maintains session state
    #[test]
    fn prop_session_tracker_maintains_state() {
        let tracker = SessionTracker::new();
        
        let session = SessionState {
            session_id: create_session_id(1),
            user_id: create_user_id(1),
            roles: HashSet::from([Role("admin".to_string()), Role("user".to_string())]),
            authenticated: true,
            created_at: Utc::now(),
            last_activity: Utc::now(),
        };
        
        tracker.set_current(session);
        
        assert!(tracker.has_role(&Role("admin".to_string())));
        assert!(tracker.has_role(&Role("user".to_string())));
        assert!(!tracker.has_role(&Role("guest".to_string())));
        
        let roles = tracker.get_roles();
        assert_eq!(roles.len(), 2);
    }

    /// Property: Session termination clears state
    #[test]
    fn prop_session_termination_clears_state() {
        let tracker = SessionTracker::new();
        
        let session = SessionState {
            session_id: create_session_id(1),
            user_id: create_user_id(1),
            roles: HashSet::from([Role("user".to_string())]),
            authenticated: true,
            created_at: Utc::now(),
            last_activity: Utc::now(),
        };
        
        tracker.set_current(session);
        assert!(tracker.get_current().is_some());
        
        tracker.terminate();
        assert!(tracker.get_current().is_none());
    }

    /// Property: Session history is maintained
    #[test]
    fn prop_session_history_maintained() {
        let tracker = SessionTracker::new();
        
        for i in 0..5 {
            let session = SessionState {
                session_id: create_session_id(i),
                user_id: create_user_id(i),
                roles: HashSet::new(),
                authenticated: true,
                created_at: Utc::now(),
                last_activity: Utc::now(),
            };
            tracker.set_current(session);
        }
        
        let history = tracker.get_history();
        assert_eq!(history.len(), 5);
    }
}

// ============================================================================
// Integration Tests
// ============================================================================

#[cfg(test)]
mod integration_tests {
    use super::*;

    /// Test complete state tracking workflow
    #[test]
    fn test_complete_state_tracking_workflow() {
        let tracker = StateTracker::new();
        let ledger = StateLedger::new();
        
        // Initial state
        let initial_state = tracker.capture_state();
        
        // Make changes
        tracker.set_ownership(create_object_id(1), create_user_id(1));
        tracker.set_balance(create_account_id(1), Balance::new(1000, Currency::USD));
        
        let session = SessionState {
            session_id: create_session_id(1),
            user_id: create_user_id(1),
            roles: HashSet::from([Role("user".to_string())]),
            authenticated: true,
            created_at: Utc::now(),
            last_activity: Utc::now(),
        };
        tracker.set_session(session);
        
        // Capture new state
        let new_state = tracker.capture_state();
        
        // Record transition
        let transition = create_test_transition(initial_state, new_state);
        let entry_id = ledger.record_transition(transition);
        
        // Verify
        assert!(!entry_id.is_empty());
        assert_eq!(ledger.len(), 1);
        assert!(ledger.verify_integrity());
    }

    /// Test ledger replay capability
    #[test]
    fn test_ledger_replay_capability() {
        let ledger = StateLedger::new();
        
        // Record multiple transitions
        for i in 0..10 {
            let mut from = ApplicationState::default();
            let mut to = ApplicationState::new();
            
            to.balances.insert(
                create_account_id(i),
                Balance::new((i as i64) * 100, Currency::USD)
            );
            
            ledger.record_transition(create_test_transition(from, to));
        }
        
        // Get replay sequence
        let replay = ledger.get_replay_sequence(3, 7);
        assert_eq!(replay.len(), 5);
        
        // Verify sequence order
        for (i, entry) in replay.iter().enumerate() {
            assert_eq!(entry.sequence, (i + 3) as u64);
        }
    }

    /// Test state at specific point in time
    #[test]
    fn test_state_at_point_in_time() {
        let ledger = StateLedger::new();
        
        for i in 0..5 {
            let mut to = ApplicationState::new();
            to.balances.insert(
                create_account_id(0),
                Balance::new((i as i64 + 1) * 100, Currency::USD)
            );
            
            ledger.record_transition(create_test_transition(
                ApplicationState::default(),
                to
            ));
        }
        
        // Get state at sequence 3
        let state = ledger.get_state_at(3);
        assert!(state.is_some());
        
        let state = state.unwrap();
        assert_eq!(
            state.balances.get(&create_account_id(0)).unwrap().amount,
            300
        );
    }
}
