//! State Ledger - Immutable record of all state transitions

use super::{ApplicationState, StateTransition, Action};
use chrono::{DateTime, Utc};
use parking_lot::RwLock;
use serde::{Deserialize, Serialize};
use sha2::{Sha256, Digest};
use std::collections::HashMap;
use uuid::Uuid;

/// Immutable snapshot of application state
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StateSnapshot {
    pub state: ApplicationState,
    pub captured_at: DateTime<Utc>,
}

impl StateSnapshot {
    pub fn new(state: ApplicationState) -> Self {
        Self {
            state,
            captured_at: Utc::now(),
        }
    }

    /// Calculate hash of the state for integrity verification
    pub fn hash(&self) -> String {
        let serialized = serde_json::to_string(&self.state).unwrap_or_default();
        let mut hasher = Sha256::new();
        hasher.update(serialized.as_bytes());
        hex::encode(hasher.finalize())
    }
}

/// Entry in the state ledger
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LedgerEntry {
    pub id: String,
    pub sequence: u64,
    pub transition: StateTransition,
    pub state_hash: String,
    pub previous_hash: Option<String>,
    pub timestamp: DateTime<Utc>,
}

/// Immutable ledger of all state transitions
pub struct StateLedger {
    entries: RwLock<Vec<LedgerEntry>>,
    snapshots: RwLock<HashMap<String, StateSnapshot>>,
    current_sequence: RwLock<u64>,
}

impl StateLedger {
    pub fn new() -> Self {
        Self {
            entries: RwLock::new(Vec::new()),
            snapshots: RwLock::new(HashMap::new()),
            current_sequence: RwLock::new(0),
        }
    }

    /// Record a state transition in the ledger
    pub fn record_transition(&self, transition: StateTransition) -> String {
        let mut entries = self.entries.write();
        let mut sequence = self.current_sequence.write();
        
        *sequence += 1;
        let entry_id = Uuid::new_v4().to_string();
        
        let snapshot = StateSnapshot::new(transition.to_state.clone());
        let state_hash = snapshot.hash();
        
        let previous_hash = entries.last().map(|e| e.state_hash.clone());
        
        let entry = LedgerEntry {
            id: entry_id.clone(),
            sequence: *sequence,
            transition,
            state_hash: state_hash.clone(),
            previous_hash,
            timestamp: Utc::now(),
        };
        
        entries.push(entry);
        
        // Store snapshot for quick access
        self.snapshots.write().insert(state_hash, snapshot);
        
        entry_id
    }

    /// Get a specific entry by ID
    pub fn get_entry(&self, id: &str) -> Option<LedgerEntry> {
        self.entries.read()
            .iter()
            .find(|e| e.id == id)
            .cloned()
    }

    /// Get entry by sequence number
    pub fn get_by_sequence(&self, sequence: u64) -> Option<LedgerEntry> {
        self.entries.read()
            .iter()
            .find(|e| e.sequence == sequence)
            .cloned()
    }

    /// Get all entries in a time range
    pub fn get_range(&self, start: DateTime<Utc>, end: DateTime<Utc>) -> Vec<LedgerEntry> {
        self.entries.read()
            .iter()
            .filter(|e| e.timestamp >= start && e.timestamp <= end)
            .cloned()
            .collect()
    }

    /// Get the latest state
    pub fn get_latest_state(&self) -> Option<ApplicationState> {
        self.entries.read()
            .last()
            .map(|e| e.transition.to_state.clone())
    }

    /// Get state at a specific sequence
    pub fn get_state_at(&self, sequence: u64) -> Option<ApplicationState> {
        self.get_by_sequence(sequence)
            .map(|e| e.transition.to_state)
    }

    /// Verify ledger integrity
    pub fn verify_integrity(&self) -> bool {
        let entries = self.entries.read();
        
        for (i, entry) in entries.iter().enumerate() {
            // Verify sequence
            if entry.sequence != (i + 1) as u64 {
                return false;
            }
            
            // Verify hash chain
            if i > 0 {
                if entry.previous_hash != Some(entries[i - 1].state_hash.clone()) {
                    return false;
                }
            }
            
            // Verify state hash
            let snapshot = StateSnapshot::new(entry.transition.to_state.clone());
            if snapshot.hash() != entry.state_hash {
                return false;
            }
        }
        
        true
    }

    /// Get total number of entries
    pub fn len(&self) -> usize {
        self.entries.read().len()
    }

    /// Check if ledger is empty
    pub fn is_empty(&self) -> bool {
        self.entries.read().is_empty()
    }

    /// Get entries for replay
    pub fn get_replay_sequence(&self, from: u64, to: u64) -> Vec<LedgerEntry> {
        self.entries.read()
            .iter()
            .filter(|e| e.sequence >= from && e.sequence <= to)
            .cloned()
            .collect()
    }

    /// Clear all entries (for testing)
    #[cfg(test)]
    pub fn clear(&self) {
        self.entries.write().clear();
        self.snapshots.write().clear();
        *self.current_sequence.write() = 0;
    }
}

impl Default for StateLedger {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::state::{ActionType, Action};
    use crate::types::ActionTiming;

    fn create_test_transition() -> StateTransition {
        StateTransition {
            id: Uuid::new_v4().to_string(),
            from_state: ApplicationState::default(),
            to_state: ApplicationState::new(),
            triggering_action: Action {
                id: Uuid::new_v4().to_string(),
                action_type: ActionType::HttpRequest,
                request: None,
                parameters: HashMap::new(),
                authentication: None,
                timing: ActionTiming {
                    start_time: Utc::now(),
                    end_time: Utc::now(),
                    duration_ms: 100,
                },
            },
            timestamp: Utc::now(),
        }
    }

    #[test]
    fn test_ledger_creation() {
        let ledger = StateLedger::new();
        assert!(ledger.is_empty());
        assert_eq!(ledger.len(), 0);
    }

    #[test]
    fn test_record_transition() {
        let ledger = StateLedger::new();
        let transition = create_test_transition();
        
        let entry_id = ledger.record_transition(transition);
        
        assert!(!entry_id.is_empty());
        assert_eq!(ledger.len(), 1);
    }

    #[test]
    fn test_integrity_verification() {
        let ledger = StateLedger::new();
        
        for _ in 0..5 {
            ledger.record_transition(create_test_transition());
        }
        
        assert!(ledger.verify_integrity());
    }

    #[test]
    fn test_get_by_sequence() {
        let ledger = StateLedger::new();
        
        ledger.record_transition(create_test_transition());
        ledger.record_transition(create_test_transition());
        
        let entry = ledger.get_by_sequence(1);
        assert!(entry.is_some());
        assert_eq!(entry.unwrap().sequence, 1);
    }

    #[test]
    fn test_replay_sequence() {
        let ledger = StateLedger::new();
        
        for _ in 0..10 {
            ledger.record_transition(create_test_transition());
        }
        
        let replay = ledger.get_replay_sequence(3, 7);
        assert_eq!(replay.len(), 5);
    }
}