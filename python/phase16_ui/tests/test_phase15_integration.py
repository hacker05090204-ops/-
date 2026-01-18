"""
Phase-16 Phase-15 Integration Tests (TASK-P16-G04)

Verify Phase-15 calls follow governance rules.

GOVERNANCE CONSTRAINT:
All Phase-15 calls require human click trigger.
Phase-15 outputs must not be interpreted as verification.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestPhase15IntegrationCompliance:
    """Verify Phase-15 integration follows governance."""
    
    def test_cve_fetch_requires_human_initiated(self):
        """CVE fetch must pass human_initiated=True to Phase-15."""
        from phase16_ui.cve_panel import CVEPanel
        
        panel = CVEPanel()
        
        with patch('phase15_governance.cve_reference.fetch_cve_from_api') as mock_fetch:
            mock_fetch.return_value = {
                "cve_id": "CVE-2021-44228",
                "is_reference_only": True,
                "disclaimer": "CVE data is reference-only...",
            }
            
            # Fetch with human_initiated=True should work
            panel.fetch_cve("CVE-2021-44228", human_initiated=True)
            
            # Verify human_initiated=True was passed
            mock_fetch.assert_called_once()
            call_kwargs = mock_fetch.call_args[1]
            assert call_kwargs.get('human_initiated') is True, (
                "CVE fetch must pass human_initiated=True"
            )
    
    def test_cve_fetch_blocks_without_human_initiated(self):
        """CVE fetch must block if human_initiated=False."""
        from phase16_ui.cve_panel import CVEPanel
        from phase16_ui.errors import UIGovernanceViolation
        
        panel = CVEPanel()
        
        # Fetch without human_initiated should raise
        with pytest.raises(UIGovernanceViolation):
            panel.fetch_cve("CVE-2021-44228", human_initiated=False)
    
    def test_audit_log_called_for_ui_events(self):
        """UI events must be logged via Phase-15 audit."""
        from phase16_ui.event_logger import UIEventLogger
        
        logger = UIEventLogger(session_id="test-session")
        
        with patch('phase15_governance.audit.log_event') as mock_log:
            logger.log_click("button-confirm")
            
            mock_log.assert_called_once()
            call_kwargs = mock_log.call_args[1]
            assert call_kwargs.get('attribution') == 'HUMAN', (
                "UI events must have HUMAN attribution"
            )
    
    def test_no_phase15_state_modification(self):
        """UI must not modify Phase-15 state."""
        from phase16_ui.renderer import UIRenderer
        
        renderer = UIRenderer()
        
        # Should not have methods that modify Phase-15
        forbidden_methods = {
            "modify_phase15",
            "update_phase15",
            "write_to_phase15",
            "set_phase15_state",
        }
        
        renderer_methods = {name for name in dir(renderer) if not name.startswith('_')}
        forbidden_found = renderer_methods & forbidden_methods
        
        assert not forbidden_found, (
            f"Renderer has forbidden Phase-15 modification methods: {forbidden_found}"
        )


class TestPhase15OutputInterpretation:
    """Verify Phase-15 outputs are not interpreted as verification."""
    
    def test_cve_output_not_treated_as_verification(self):
        """CVE output must not be treated as verification."""
        from phase16_ui.cve_panel import CVEPanel
        
        panel = CVEPanel()
        
        cve_data = {
            "cve_id": "CVE-2021-44228",
            "is_reference_only": True,
            "disclaimer": "CVE data is reference-only...",
        }
        
        output = panel.render_cve(cve_data)
        
        # Output must not contain verification language
        verification_terms = ["verified", "confirmed", "validated", "proven"]
        output_lower = output.lower()
        
        for term in verification_terms:
            # Allow "NOT VERIFIED" and "does not verify"
            if term == "verified":
                if "not verified" in output_lower or "does not verify" in output_lower:
                    continue
            assert term not in output_lower, (
                f"CVE output contains verification language: {term}"
            )
    
    def test_enforcement_result_not_treated_as_approval(self):
        """Enforcement results must not be treated as approval."""
        from phase16_ui.renderer import UIRenderer
        
        renderer = UIRenderer()
        
        # Mock enforcement result
        enforcement_result = {
            "blocked": False,
            "rule": "test_rule",
        }
        
        output = renderer.render_enforcement_result(enforcement_result)
        
        # Output must not imply approval
        approval_terms = ["approved", "allowed", "permitted", "authorized"]
        output_lower = output.lower()
        
        for term in approval_terms:
            assert term not in output_lower, (
                f"Enforcement output implies approval: {term}"
            )
    
    def test_validation_result_shows_pass_fail_only(self):
        """Validation results must show pass/fail only."""
        from phase16_ui.renderer import UIRenderer
        
        renderer = UIRenderer()
        
        # Mock validation result
        validation_result = {
            "valid": True,
            "errors": [],
        }
        
        output = renderer.render_validation_result(validation_result)
        
        # Should only show pass/fail, not verification
        assert "pass" in output.lower() or "fail" in output.lower() or "valid" in output.lower(), (
            "Validation output must show pass/fail status"
        )
        
        # Must not imply verification
        assert "verified" not in output.lower(), (
            "Validation output must not imply verification"
        )


class TestPhase15CallTriggers:
    """Verify all Phase-15 calls have human triggers."""
    
    def test_enforcer_call_requires_human_trigger(self):
        """Enforcer calls must require human trigger."""
        from phase16_ui.renderer import UIRenderer
        from phase16_ui.errors import UIGovernanceViolation
        
        renderer = UIRenderer()
        
        # Call without human trigger should raise
        with pytest.raises(UIGovernanceViolation):
            renderer.call_enforcer("test_rule", human_initiated=False)
    
    def test_validator_call_requires_human_trigger(self):
        """Validator calls must require human trigger."""
        from phase16_ui.renderer import UIRenderer
        from phase16_ui.errors import UIGovernanceViolation
        
        renderer = UIRenderer()
        
        # Call without human trigger should raise
        with pytest.raises(UIGovernanceViolation):
            renderer.call_validator({"test": "data"}, human_initiated=False)
    
    def test_blocker_call_requires_human_trigger(self):
        """Blocker calls must require human trigger."""
        from phase16_ui.renderer import UIRenderer
        from phase16_ui.errors import UIGovernanceViolation
        
        renderer = UIRenderer()
        
        # Call without human trigger should raise
        with pytest.raises(UIGovernanceViolation):
            renderer.call_blocker("test_action", human_initiated=False)


class TestNoAutomaticPhase15Calls:
    """Verify no automatic Phase-15 calls."""
    
    def test_no_phase15_call_on_init(self):
        """No Phase-15 calls on UI initialization."""
        from phase16_ui.renderer import UIRenderer
        
        with patch('phase15_governance.enforcer.enforce_rule') as mock_enforce:
            with patch('phase15_governance.validator.validate_input') as mock_validate:
                with patch('phase15_governance.cve_reference.fetch_cve_from_api') as mock_cve:
                    renderer = UIRenderer()
                    
                    # No Phase-15 calls should have been made
                    mock_enforce.assert_not_called()
                    mock_validate.assert_not_called()
                    mock_cve.assert_not_called()
    
    def test_no_phase15_call_on_data_change(self):
        """No Phase-15 calls on data change."""
        from phase16_ui.state import UIState
        
        with patch('phase15_governance.enforcer.enforce_rule') as mock_enforce:
            with patch('phase15_governance.validator.validate_input') as mock_validate:
                state = UIState()
                
                if hasattr(state, 'set_data'):
                    state.set_data("test", "value")
                
                # No Phase-15 calls should have been made
                mock_enforce.assert_not_called()
                mock_validate.assert_not_called()
