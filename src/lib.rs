//! Kali MCP Toolkit - High-performance core components
//! 
//! This crate provides the Rust core for the Kali MCP Toolkit,
//! implementing invariant validation, state tracking, and proof generation.

pub mod invariant;
pub mod state;
pub mod proof;
pub mod types;
pub mod ffi;

use pyo3::prelude::*;

/// Python module initialization
#[pymodule]
fn kali_mcp_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<ffi::PyInvariantEngine>()?;
    m.add_class::<ffi::PyStateTracker>()?;
    m.add_class::<ffi::PyProofEngine>()?;
    m.add_class::<ffi::PyFinding>()?;
    m.add_class::<ffi::PyProof>()?;
    Ok(())
}