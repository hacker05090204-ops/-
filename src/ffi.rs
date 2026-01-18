//! FFI Module - Python bindings for Rust components

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::sync::Arc;

use crate::invariant::{InvariantCatalog, InvariantValidator, InvariantCategory, ValidationResult};
use crate::state::{StateTracker, ApplicationState, StateLedger};
use crate::proof::{CausalEngine, ReplayEngine, EvidenceCollector, Proof, Evidence};
use crate::types::*;

/// Python wrapper for InvariantEngine
#[pyclass]
pub struct PyInvariantEngine {
    catalog: Arc<InvariantCatalog>,
    validator: InvariantValidator,
}

#[pymethods]
impl PyInvariantEngine {
    #[new]
    pub fn new() -> Self {
        let catalog = Arc::new(InvariantCatalog::new());
        let validator = InvariantValidator::new(Arc::clone(&catalog));
        Self { catalog, validator }
    }

    /// Get count of registered invariants
    pub fn invariant_count(&self) -> usize {
        self.catalog.count()
    }

    /// Get invariant IDs by category
    pub fn get_invariants_by_category(&self, category: &str) -> Vec<String> {
        let cat = match category {
            "authorization" => InvariantCategory::Authorization,
            "monetary" => InvariantCategory::Monetary,
            "workflow" => InvariantCategory::Workflow,
            "trust" => InvariantCategory::Trust,
            "data_integrity" => InvariantCategory::DataIntegrity,
            "session" => InvariantCategory::SessionManagement,
            "input" => InvariantCategory::InputValidation,
            _ => InvariantCategory::Custom,
        };
        
        self.catalog.get_by_category(cat)
            .iter()
            .map(|inv| inv.id.clone())
            .collect()
    }

    /// Validate state transition (simplified for Python)
    pub fn validate(&self, before_json: &str, after_json: &str) -> PyResult<PyValidationResult> {
        let before: ApplicationState = serde_json::from_str(before_json)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
        let after: ApplicationState = serde_json::from_str(after_json)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
        
        let result = self.validator.validate_transition(&before, &after);
        Ok(PyValidationResult::from(result))
    }
}

/// Python-friendly validation result
#[pyclass]
pub struct PyValidationResult {
    #[pyo3(get)]
    pub is_valid: bool,
    #[pyo3(get)]
    pub violation_count: usize,
    #[pyo3(get)]
    pub violations: Vec<String>,
    #[pyo3(get)]
    pub checked_invariants: Vec<String>,
}

impl From<ValidationResult> for PyValidationResult {
    fn from(result: ValidationResult) -> Self {
        Self {
            is_valid: result.is_valid,
            violation_count: result.violations.len(),
            violations: result.violations.iter()
                .map(|v| format!("{}: {}", v.invariant_id, v.message))
                .collect(),
            checked_invariants: result.checked_invariants,
        }
    }
}

/// Python wrapper for StateTracker
#[pyclass]
pub struct PyStateTracker {
    tracker: StateTracker,
    ledger: StateLedger,
}

#[pymethods]
impl PyStateTracker {
    #[new]
    pub fn new() -> Self {
        Self {
            tracker: StateTracker::new(),
            ledger: StateLedger::new(),
        }
    }

    /// Capture current state as JSON
    pub fn capture_state(&self) -> PyResult<String> {
        let state = self.tracker.capture_state();
        serde_json::to_string(&state)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))
    }

    /// Set ownership
    pub fn set_ownership(&self, object_id: &str, user_id: &str) {
        self.tracker.set_ownership(
            ObjectId(object_id.to_string()),
            UserId(user_id.to_string())
        );
    }

    /// Set balance
    pub fn set_balance(&self, account_id: &str, amount: i64, currency: &str) {
        let curr = match currency {
            "USD" => Currency::USD,
            "EUR" => Currency::EUR,
            "GBP" => Currency::GBP,
            "BTC" => Currency::BTC,
            "ETH" => Currency::ETH,
            _ => Currency::Credits,
        };
        
        self.tracker.set_balance(
            AccountId(account_id.to_string()),
            Balance::new(amount, curr)
        );
    }

    /// Get ledger entry count
    pub fn ledger_size(&self) -> usize {
        self.ledger.len()
    }

    /// Verify ledger integrity
    pub fn verify_integrity(&self) -> bool {
        self.ledger.verify_integrity()
    }
}

/// Python wrapper for ProofEngine
#[pyclass]
pub struct PyProofEngine {
    causal: CausalEngine,
    replay: ReplayEngine,
}

#[pymethods]
impl PyProofEngine {
    #[new]
    pub fn new() -> Self {
        Self {
            causal: CausalEngine::new(),
            replay: ReplayEngine::new(),
        }
    }

    /// Check if action could cause effect
    pub fn validate_causality(&self, action_json: &str, effect_json: &str) -> PyResult<bool> {
        let action: crate::state::Action = serde_json::from_str(action_json)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
        let effect: crate::proof::StateChange = serde_json::from_str(effect_json)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
        
        Ok(self.causal.validate_causality(&action, &effect))
    }

    /// Get causality confidence
    pub fn get_causality_confidence(&self, action_json: &str, effect_json: &str) -> PyResult<f64> {
        let action: crate::state::Action = serde_json::from_str(action_json)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
        let effect: crate::proof::StateChange = serde_json::from_str(effect_json)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
        
        Ok(self.causal.get_causality_confidence(&action, &effect))
    }
}

/// Python wrapper for Finding
#[pyclass]
#[derive(Clone)]
pub struct PyFinding {
    #[pyo3(get)]
    pub id: String,
    #[pyo3(get)]
    pub invariant_violated: String,
    #[pyo3(get)]
    pub severity: String,
    #[pyo3(get)]
    pub confidence: f64,
    #[pyo3(get)]
    pub classification: String,
}

#[pymethods]
impl PyFinding {
    #[new]
    pub fn new(
        id: String,
        invariant_violated: String,
        severity: String,
        confidence: f64,
        classification: String,
    ) -> Self {
        Self {
            id,
            invariant_violated,
            severity,
            confidence,
            classification,
        }
    }

    pub fn to_json(&self) -> PyResult<String> {
        Ok(format!(
            r#"{{"id":"{}","invariant":"{}","severity":"{}","confidence":{},"classification":"{}"}}"#,
            self.id, self.invariant_violated, self.severity, self.confidence, self.classification
        ))
    }
}

/// Python wrapper for Proof
#[pyclass]
#[derive(Clone)]
pub struct PyProof {
    #[pyo3(get)]
    pub id: String,
    #[pyo3(get)]
    pub invariant_violated: String,
    #[pyo3(get)]
    pub is_deterministic: bool,
    #[pyo3(get)]
    pub action_count: usize,
    #[pyo3(get)]
    pub evidence_count: usize,
}

#[pymethods]
impl PyProof {
    #[new]
    pub fn new(
        id: String,
        invariant_violated: String,
        is_deterministic: bool,
        action_count: usize,
        evidence_count: usize,
    ) -> Self {
        Self {
            id,
            invariant_violated,
            is_deterministic,
            action_count,
            evidence_count,
        }
    }

    pub fn is_valid(&self) -> bool {
        self.is_deterministic && self.action_count > 0 && self.evidence_count > 0
    }
}