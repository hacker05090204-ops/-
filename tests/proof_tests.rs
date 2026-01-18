//! Property-based tests for proof engine and causal attribution
//!
//! **Task 4: Create proof engine and causal attribution system**
//! **Property Tests: 4.1, 4.2**
//!
//! Requirements validated:
//! - 16.1-16.5: Proof Generation Requirements
//! - 29.1-29.5: Replay Requirements
//! - 35.1-35.5: Causal Attribution Requirements

use kali_mcp_core::proof::{
    CausalEngine, CausalChain, CausalLink,
    ReplayEngine, ReplayResult, ReplayInstructions,
    EvidenceCollector, Evidence, EvidenceType,
    StateChange, StateChangeType, StateRequirements, EvidenceArtifact,
};
use kali_mcp_core::state::{
    ApplicationState, StateTransition, Action, ActionType,
};
use kali_mcp_core::types::*;
use chrono::Utc;
use std::collections::HashMap;

// ============================================================================
// Test Helpers
// ============================================================================

fn create_account_id(id: u32) -> AccountId {
    AccountId(format!("account_{}", id))
}

fn create_test_action(action_type: ActionType) -> Action {
    Action {
        id: uuid::Uuid::new_v4().to_string(),
        action_type,
        request: Some(HttpRequest {
            method: HttpMethod::POST,
            url: "https://example.com/api/transfer".to_string(),
            headers: HashMap::new(),
            body: None,
            timestamp: Utc::now(),
        }),
        parameters: HashMap::new(),
        authentication: None,
        timing: ActionTiming {
            start_time: Utc::now(),
            end_time: Utc::now(),
            duration_ms: 100,
        },
    }
}

fn create_test_transition() -> StateTransition {
    let mut from = ApplicationState::default();
    let mut to = ApplicationState::new();
    
    // Add a balance change
    from.balances.insert(create_account_id(1), Balance::new(1000, Currency::USD));
    to.balances.insert(create_account_id(1), Balance::new(800, Currency::USD));
    to.balances.insert(create_account_id(2), Balance::new(200, Currency::USD));
    
    StateTransition {
        id: uuid::Uuid::new_v4().to_string(),
        from_state: from,
        to_state: to,
        triggering_action: create_test_action(ActionType::Payment),
        timestamp: Utc::now(),
    }
}

// ============================================================================
// Property Test 4.1: Causal Attribution
// **Validates: Requirements 35.1, 35.2, 35.3**
// ============================================================================

#[cfg(test)]
mod property_test_4_1 {
    use super::*;

    /// Property: Causal engine detects state changes
    #[test]
    fn prop_causal_engine_detects_changes() {
        let engine = CausalEngine::new();
        let transition = create_test_transition();
        
        let chain = engine.build_chain(&transition);
        
        // Should detect the balance changes
        assert!(!chain.is_empty());
        assert!(chain.links.iter().any(|link| {
            link.state_changes.iter().any(|c| {
                matches!(c.change_type, StateChangeType::BalanceChange)
            })
        }));
    }

    /// Property: Causal chain has root action
    #[test]
    fn prop_causal_chain_has_root_action() {
        let engine = CausalEngine::new();
        let transition = create_test_transition();
        
        let chain = engine.build_chain(&transition);
        
        if !chain.is_empty() {
            assert!(chain.root_action.is_some());
        }
    }

    /// Property: Causal chain has final effect
    #[test]
    fn prop_causal_chain_has_final_effect() {
        let engine = CausalEngine::new();
        let transition = create_test_transition();
        
        let chain = engine.build_chain(&transition);
        
        if !chain.is_empty() {
            assert!(chain.final_effect.is_some());
        }
    }

    /// Property: Causal confidence is between 0 and 1
    #[test]
    fn prop_causal_confidence_bounded() {
        let engine = CausalEngine::new();
        let transition = create_test_transition();
        
        let chain = engine.build_chain(&transition);
        
        assert!(chain.confidence >= 0.0);
        assert!(chain.confidence <= 1.0);
        
        for link in &chain.links {
            assert!(link.confidence >= 0.0);
            assert!(link.confidence <= 1.0);
        }
    }

    /// Property: Payment actions attribute to balance changes
    #[test]
    fn prop_payment_attributes_to_balance() {
        let engine = CausalEngine::new();
        
        let action = create_test_action(ActionType::Payment);
        let effect = StateChange {
            change_type: StateChangeType::BalanceChange,
            field: "balances.account_1".to_string(),
            old_value: Some(serde_json::json!(1000)),
            new_value: Some(serde_json::json!(800)),
        };
        
        assert!(engine.validate_causality(&action, &effect));
        
        let confidence = engine.get_causality_confidence(&action, &effect);
        assert!(confidence > 0.9); // Payment -> Balance should be high confidence
    }

    /// Property: Auth actions attribute to session changes
    #[test]
    fn prop_auth_attributes_to_session() {
        let engine = CausalEngine::new();
        
        let action = create_test_action(ActionType::Authentication);
        let effect = StateChange {
            change_type: StateChangeType::SessionChange,
            field: "current_session".to_string(),
            old_value: None,
            new_value: Some(serde_json::json!("session_123")),
        };
        
        assert!(engine.validate_causality(&action, &effect));
    }

    /// Property: Empty transitions produce empty chains
    #[test]
    fn prop_empty_transition_empty_chain() {
        let engine = CausalEngine::new();
        
        let transition = StateTransition {
            id: uuid::Uuid::new_v4().to_string(),
            from_state: ApplicationState::default(),
            to_state: ApplicationState::default(),
            triggering_action: create_test_action(ActionType::HttpRequest),
            timestamp: Utc::now(),
        };
        
        let chain = engine.build_chain(&transition);
        
        // No state changes = empty chain
        assert!(chain.is_empty());
    }

    /// Property: Chain completion is accurate
    #[test]
    fn prop_chain_completion_accurate() {
        let mut chain = CausalChain::new();
        
        // Empty chain is not complete
        assert!(!chain.is_complete());
        
        // Add a link
        chain.add_link(CausalLink {
            action: create_test_action(ActionType::HttpRequest),
            state_changes: vec![StateChange {
                change_type: StateChangeType::BalanceChange,
                field: "test".to_string(),
                old_value: None,
                new_value: Some(serde_json::json!(100)),
            }],
            confidence: 0.9,
            timestamp: Utc::now(),
        });
        
        chain.complete();
        
        // Now should be complete
        assert!(chain.is_complete());
    }
}

// ============================================================================
// Property Test 4.2: Proof Generation
// **Validates: Requirements 16.1, 16.2, 16.3**
// ============================================================================

#[cfg(test)]
mod property_test_4_2 {
    use super::*;

    /// Property: Replay instructions are generated from transitions
    #[test]
    fn prop_replay_instructions_generated() {
        let engine = ReplayEngine::new();
        let transition = create_test_transition();
        
        let instructions = engine.generate_instructions(&transition);
        
        assert!(!instructions.steps.is_empty());
    }

    /// Property: Replay instructions preserve action sequence
    #[test]
    fn prop_replay_preserves_sequence() {
        let engine = ReplayEngine::new();
        
        let transitions: Vec<_> = (0..5)
            .map(|_| create_test_transition())
            .collect();
        
        let instructions = engine.generate_from_sequence(&transitions);
        
        assert_eq!(instructions.steps.len(), 5);
        
        // Verify sequence numbers
        for (i, step) in instructions.steps.iter().enumerate() {
            assert_eq!(step.sequence, (i + 1) as u32);
        }
    }

    /// Property: State requirements are extracted
    #[test]
    fn prop_state_requirements_extracted() {
        let engine = ReplayEngine::new();
        let transition = create_test_transition();
        
        let instructions = engine.generate_instructions(&transition);
        
        // Should have balance requirements from the from_state
        assert!(!instructions.initial_state_requirements.required_balances.is_empty());
    }

    /// Property: Requirements validation is accurate
    #[test]
    fn prop_requirements_validation_accurate() {
        let engine = ReplayEngine::new();
        
        let mut state = ApplicationState::default();
        state.balances.insert(create_account_id(1), Balance::new(1000, Currency::USD));
        
        let mut requirements = StateRequirements::default();
        requirements.required_balances.insert("account_1".to_string(), 500);
        
        // State has 1000, requirement is 500 - should pass
        assert!(engine.validate_requirements(&state, &requirements));
        
        // Require more than available
        requirements.required_balances.insert("account_1".to_string(), 2000);
        assert!(!engine.validate_requirements(&state, &requirements));
    }

    /// Property: Determinism check is accurate
    #[test]
    fn prop_determinism_check_accurate() {
        let engine = ReplayEngine::new();
        
        // Same results = deterministic
        let results = vec![
            ReplayResult::success(ApplicationState::default(), 3, 100),
            ReplayResult::success(ApplicationState::default(), 3, 150),
            ReplayResult::success(ApplicationState::default(), 3, 120),
        ];
        
        assert!(engine.is_deterministic(&results));
        
        // Different results = non-deterministic
        let mixed_results = vec![
            ReplayResult::success(ApplicationState::default(), 3, 100),
            ReplayResult::failure("error".to_string(), 2, 3),
        ];
        
        assert!(!engine.is_deterministic(&mixed_results));
    }

    /// Property: Evidence collection captures all types
    #[test]
    fn prop_evidence_collection_complete() {
        let mut collector = EvidenceCollector::new();
        
        let request = HttpRequest {
            method: HttpMethod::POST,
            url: "https://example.com/api".to_string(),
            headers: HashMap::new(),
            body: Some(b"test body".to_vec()),
            timestamp: Utc::now(),
        };
        
        let response = HttpResponse {
            status_code: 200,
            headers: HashMap::new(),
            body: b"OK".to_vec(),
            timestamp: Utc::now(),
            duration_ms: 100,
        };
        
        collector.add_http_request(&request);
        collector.add_http_response(&response);
        collector.add_dom_snapshot("<html><body>Test</body></html>");
        collector.add_screenshot(vec![0x89, 0x50, 0x4E, 0x47], "test screenshot");
        
        let evidence = collector.finalize();
        
        assert!(evidence.is_complete);
        assert_eq!(evidence.artifacts.len(), 4);
        assert!(evidence.has_required_types(&[EvidenceType::HttpRequest, EvidenceType::HttpResponse]));
    }

    /// Property: Evidence integrity is verifiable
    #[test]
    fn prop_evidence_integrity_verifiable() {
        let mut collector = EvidenceCollector::new();
        
        collector.add_http_request(&HttpRequest {
            method: HttpMethod::GET,
            url: "https://example.com".to_string(),
            headers: HashMap::new(),
            body: None,
            timestamp: Utc::now(),
        });
        
        collector.add_http_response(&HttpResponse {
            status_code: 200,
            headers: HashMap::new(),
            body: b"test".to_vec(),
            timestamp: Utc::now(),
            duration_ms: 50,
        });
        
        let evidence = collector.finalize();
        
        assert!(evidence.verify_all_integrity());
    }

    /// Property: Evidence artifacts have unique IDs
    #[test]
    fn prop_evidence_artifacts_unique_ids() {
        let mut collector = EvidenceCollector::new();
        
        for _ in 0..10 {
            collector.add_custom("test", vec![1, 2, 3]);
        }
        
        let evidence = collector.finalize();
        
        let mut ids: Vec<_> = evidence.artifacts.iter().map(|a| &a.id).collect();
        let original_len = ids.len();
        ids.sort();
        ids.dedup();
        
        assert_eq!(ids.len(), original_len, "All artifact IDs should be unique");
    }

    /// Property: Evidence content hash is deterministic
    #[test]
    fn prop_evidence_hash_deterministic() {
        // EvidenceArtifact is imported at the top of the file
        
        let content = b"test content".to_vec();
        
        let artifact1 = EvidenceArtifact::new(EvidenceType::Custom("test".to_string()), content.clone());
        let artifact2 = EvidenceArtifact::new(EvidenceType::Custom("test".to_string()), content);
        
        assert_eq!(artifact1.content_hash, artifact2.content_hash);
    }
}

// ============================================================================
// Integration Tests
// ============================================================================

#[cfg(test)]
mod integration_tests {
    use super::*;

    /// Test complete proof generation workflow
    #[test]
    fn test_complete_proof_workflow() {
        let causal_engine = CausalEngine::new();
        let replay_engine = ReplayEngine::new();
        let mut evidence_collector = EvidenceCollector::new();
        
        // Create a transition with a violation
        let transition = create_test_transition();
        
        // Build causal chain
        let chain = causal_engine.build_chain(&transition);
        assert!(!chain.is_empty());
        
        // Generate replay instructions
        let instructions = replay_engine.generate_instructions(&transition);
        assert!(!instructions.steps.is_empty());
        
        // Collect evidence
        if let Some(request) = &transition.triggering_action.request {
            evidence_collector.add_http_request(request);
        }
        
        evidence_collector.add_http_response(&HttpResponse {
            status_code: 200,
            headers: HashMap::new(),
            body: b"Transfer successful".to_vec(),
            timestamp: Utc::now(),
            duration_ms: 100,
        });
        
        evidence_collector.add_state_snapshot(&transition.from_state);
        evidence_collector.add_state_snapshot(&transition.to_state);
        
        let evidence = evidence_collector.finalize();
        
        // Verify complete proof components
        assert!(chain.is_complete());
        assert!(evidence.is_complete);
        assert!(evidence.verify_all_integrity());
    }

    /// Test causal chain with multiple state changes
    #[test]
    fn test_multiple_state_changes() {
        let engine = CausalEngine::new();
        
        let mut from = ApplicationState::default();
        let mut to = ApplicationState::new();
        
        // Multiple changes
        from.balances.insert(create_account_id(1), Balance::new(1000, Currency::USD));
        to.balances.insert(create_account_id(1), Balance::new(500, Currency::USD));
        to.balances.insert(create_account_id(2), Balance::new(500, Currency::USD));
        
        from.ownership.insert(ObjectId("obj1".to_string()), UserId("user1".to_string()));
        to.ownership.insert(ObjectId("obj1".to_string()), UserId("user2".to_string()));
        
        let transition = StateTransition {
            id: uuid::Uuid::new_v4().to_string(),
            from_state: from,
            to_state: to,
            triggering_action: create_test_action(ActionType::HttpRequest),
            timestamp: Utc::now(),
        };
        
        let chain = engine.build_chain(&transition);
        
        // Should detect multiple changes
        let total_changes: usize = chain.links.iter()
            .map(|l| l.state_changes.len())
            .sum();
        
        assert!(total_changes >= 2);
    }

    /// Test replay with session requirements
    #[test]
    fn test_replay_session_requirements() {
        let engine = ReplayEngine::new();
        
        let mut from = ApplicationState::default();
        from.current_session = Some(kali_mcp_core::state::SessionState {
            session_id: SessionId("sess1".to_string()),
            user_id: UserId("user1".to_string()),
            roles: std::collections::HashSet::from([Role("admin".to_string())]),
            authenticated: true,
            created_at: Utc::now(),
            last_activity: Utc::now(),
        });
        
        let transition = StateTransition {
            id: uuid::Uuid::new_v4().to_string(),
            from_state: from,
            to_state: ApplicationState::new(),
            triggering_action: create_test_action(ActionType::HttpRequest),
            timestamp: Utc::now(),
        };
        
        let instructions = engine.generate_instructions(&transition);
        
        // Should have session requirements
        assert!(instructions.initial_state_requirements.required_session.is_some());
        
        let session_req = instructions.initial_state_requirements.required_session.unwrap();
        assert!(session_req.authenticated);
        assert!(session_req.required_roles.contains(&"admin".to_string()));
    }
}
