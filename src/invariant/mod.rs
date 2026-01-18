//! Invariant Engine - Core security invariant definitions and validation
//! 
//! This module implements the formal verification framework for security invariants.
//!
//! **Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 43.1, 43.2, 43.4**

mod catalog;
mod validator;
mod coverage;

pub use catalog::{InvariantCatalog, SecurityInvariant, InvariantCategory};
pub use validator::{InvariantValidator, ValidationResult, ViolationDetails};
pub use coverage::{CoverageTracker, CoverageReport, CoverageGap, GapSeverity};