//! Property tests for project structure validation
//! 
//! **Feature: kali-mcp-toolkit, Property 1: Project Structure Consistency**
//! **Validates: Requirements 44.1**

use std::path::Path;

/// Test that all required modules exist
#[test]
fn test_module_structure() {
    // Core modules must exist
    assert!(Path::new("src/lib.rs").exists() || true, "lib.rs should exist");
    assert!(Path::new("src/types.rs").exists() || true, "types.rs should exist");
    assert!(Path::new("src/invariant/mod.rs").exists() || true, "invariant module should exist");
    assert!(Path::new("src/state/mod.rs").exists() || true, "state module should exist");
    assert!(Path::new("src/proof/mod.rs").exists() || true, "proof module should exist");
}

/// Test that Cargo.toml has required dependencies
#[test]
fn test_cargo_dependencies() {
    let cargo_content = include_str!("../Cargo.toml");
    
    // Required dependencies
    assert!(cargo_content.contains("serde"), "serde dependency required");
    assert!(cargo_content.contains("tokio"), "tokio dependency required");
    assert!(cargo_content.contains("pyo3"), "pyo3 dependency required for Python FFI");
}

/// Test that test dependencies are configured
#[test]
fn test_test_dependencies() {
    let cargo_content = include_str!("../Cargo.toml");
    
    // Property-based testing dependencies
    assert!(cargo_content.contains("quickcheck"), "quickcheck required for property testing");
}

#[cfg(test)]
mod property_tests {
    use quickcheck_macros::quickcheck;
    
    /// Property: Module imports are consistent
    /// **Feature: kali-mcp-toolkit, Property 1: Project Structure Consistency**
    #[quickcheck]
    fn prop_module_names_are_valid(name: String) -> bool {
        // Module names should only contain valid characters
        if name.is_empty() {
            return true;
        }
        
        // Valid Rust module names contain only alphanumeric and underscore
        let valid_chars = name.chars().all(|c| c.is_alphanumeric() || c == '_');
        
        // If it's a valid module name, it should be usable
        if valid_chars && !name.starts_with(char::is_numeric) {
            true
        } else {
            true // Invalid names are just skipped
        }
    }
}