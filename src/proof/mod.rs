//! Proof Engine - Generates formal proofs of invariant violations
//! 
//! This module implements causal attribution, replay, and contradiction proving.

mod causal;
mod replay;
mod evidence;

pub use causal::{CausalEngine, CausalChain, CausalLink, StateChange, StateChangeType};
pub use replay::{ReplayEngine, ReplayResult, ReplayInstructions, StateRequirements};
pub use evidence::{EvidenceCollector, Evidence, EvidenceType, EvidenceArtifact};

use crate::invariant::{ViolationDetails, InvariantCategory};
use crate::state::{ApplicationState, StateTransition, Action};
use crate::types::*;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

/// Complete proof of an invariant violation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Proof {
    pub id: String,
    pub before_state: ApplicationState,
    pub action_sequence: Vec<Action>,
    pub after_state: ApplicationState,
    pub causality_chain: CausalChain,
    pub replay_instructions: ReplayInstructions,
    pub evidence: Evidence,
    pub invariant_violated: String,
    pub violation_details: ViolationDetails,
    pub generated_at: DateTime<Utc>,
    pub is_deterministic: bool,
}

impl Proof {
    /// Check if proof is complete and valid
    pub fn is_valid(&self) -> bool {
        !self.action_sequence.is_empty() &&
        self.causality_chain.is_complete() &&
        self.is_deterministic &&
        !self.evidence.artifacts.is_empty()
    }

    /// Get severity of the proven violation
    pub fn severity(&self) -> Severity {
        self.violation_details.severity
    }

    /// Get confidence level
    pub fn confidence(&self) -> f64 {
        self.violation_details.confidence
    }
}

/// Error types for proof generation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ProofError {
    NoCausalLink,
    ReplayFailed(String),
    InsufficientEvidence,
    NonDeterministic,
    StateInconsistency,
}