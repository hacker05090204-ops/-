"""
Phase-16 Forbidden Language Tests (TASK-P16-T06)

Verify no forbidden language in UI text.

GOVERNANCE CONSTRAINT:
UI must not contain verification, recommendation, scoring, or AI language.
"""

import pytest
from pathlib import Path


# Forbidden language categories
VERIFICATION_LANGUAGE = [
    "verified",
    "confirmed",
    "validated",
    "proven",
    "established",
    "authenticated",
]

RECOMMENDATION_LANGUAGE = [
    "recommended",
    "suggested",
    "advised",
    "should",
    "ought to",
    "best practice",
    "we recommend",
    "you should",
]

SCORING_LANGUAGE = [
    "score",
    "rank",
    "rating",
    "priority",
    "severity",
    "critical",
    "high",
    "medium",
    "low",
    "importance",
]

CONFIDENCE_LANGUAGE = [
    "confidence",
    "accuracy",
    "precision",
    "likelihood",
    "probability",
    "likely",
    "probably",
    "certainly",
]

AI_LANGUAGE = [
    "intelligent",
    "smart",
    "AI",
    "artificial intelligence",
    "machine learning",
    "ML",
    "neural",
    "deep learning",
    "automated analysis",
]

URGENCY_LANGUAGE = [
    "act now",
    "urgent",
    "immediately",
    "hurry",
    "limited time",
    "expires",
    "deadline",
    "asap",
]

# Combined forbidden list
ALL_FORBIDDEN = (
    VERIFICATION_LANGUAGE +
    RECOMMENDATION_LANGUAGE +
    SCORING_LANGUAGE +
    CONFIDENCE_LANGUAGE +
    AI_LANGUAGE +
    URGENCY_LANGUAGE
)


class TestNoForbiddenLanguageInStrings:
    """Verify string registry has no forbidden language."""
    
    def test_string_registry_no_verification_language(self):
        """String registry must not contain verification language."""
        from phase16_ui.strings import UIStrings
        
        # Get all string values from UIStrings
        string_values = [
            getattr(UIStrings, attr)
            for attr in dir(UIStrings)
            if not attr.startswith('_') and 
               isinstance(getattr(UIStrings, attr), str) and
               attr != 'FORBIDDEN_STRINGS'
        ]
        
        for string_val in string_values:
            string_lower = string_val.lower()
            for forbidden in VERIFICATION_LANGUAGE:
                # Allow "NOT VERIFIED" as it's the required label
                if forbidden == "verified" and "not verified" in string_lower:
                    continue
                # Allow "has not been verified" in disclaimers
                if forbidden == "verified" and "has not been verified" in string_lower:
                    continue
                # Allow in disclaimer context
                if "does not verify" in string_lower:
                    continue
                assert forbidden not in string_lower, (
                    f"String contains forbidden verification language '{forbidden}': "
                    f"{string_val[:50]}..."
                )
    
    def test_string_registry_no_recommendation_language(self):
        """String registry must not contain recommendation language."""
        from phase16_ui.strings import UIStrings
        
        string_values = [
            getattr(UIStrings, attr)
            for attr in dir(UIStrings)
            if not attr.startswith('_') and 
               isinstance(getattr(UIStrings, attr), str) and
               attr != 'FORBIDDEN_STRINGS'
        ]
        
        for string_val in string_values:
            string_lower = string_val.lower()
            for forbidden in RECOMMENDATION_LANGUAGE:
                assert forbidden not in string_lower, (
                    f"String contains forbidden recommendation language '{forbidden}': "
                    f"{string_val[:50]}..."
                )
    
    def test_string_registry_no_scoring_language(self):
        """String registry must not contain scoring language."""
        from phase16_ui.strings import UIStrings
        
        string_values = [
            getattr(UIStrings, attr)
            for attr in dir(UIStrings)
            if not attr.startswith('_') and 
               isinstance(getattr(UIStrings, attr), str) and
               attr != 'FORBIDDEN_STRINGS'
        ]
        
        for string_val in string_values:
            string_lower = string_val.lower()
            for forbidden in SCORING_LANGUAGE:
                assert forbidden not in string_lower, (
                    f"String contains forbidden scoring language '{forbidden}': "
                    f"{string_val[:50]}..."
                )
    
    def test_string_registry_no_ai_language(self):
        """String registry must not contain AI language."""
        from phase16_ui.strings import UIStrings
        
        string_values = [
            getattr(UIStrings, attr)
            for attr in dir(UIStrings)
            if not attr.startswith('_') and 
               isinstance(getattr(UIStrings, attr), str) and
               attr != 'FORBIDDEN_STRINGS'
        ]
        
        for string_val in string_values:
            string_lower = string_val.lower()
            for forbidden in AI_LANGUAGE:
                assert forbidden.lower() not in string_lower, (
                    f"String contains forbidden AI language '{forbidden}': "
                    f"{string_val[:50]}..."
                )


class TestNoForbiddenLanguageInCode:
    """Verify UI code has no forbidden language in user-facing strings."""
    
    def test_no_forbidden_in_ui_modules(self):
        """UI modules must not have forbidden language in user-facing strings."""
        ui_dir = Path(__file__).parent.parent
        
        # User-facing forbidden terms (not governance descriptions)
        user_facing_forbidden = [
            "verified",
            "confirmed", 
            "validated",
            "recommend",
            "suggested",
            "likely",
            "probably",
            "important",
            "critical",
            "high priority",
            "low priority",
            "confidence",
            "accuracy",
            "intelligent",
            "smart",
            "ai-powered",
            "machine learning",
            "act now",
            "limited time",
            "urgent",
            "hurry",
        ]
        
        for py_file in ui_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            if py_file.name == "strings.py":
                continue  # Tested separately
            
            source = py_file.read_text()
            
            # Find string literals in actual code (not docstrings)
            import ast
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    string_val = node.value.lower()
                    
                    # Skip docstrings (long strings)
                    if len(node.value) > 100:
                        continue
                    
                    # Skip strings that are clearly not user-facing
                    if any(x in string_val for x in ['governance', 'constraint', 'module', 'phase-', 'must', 'prohibited']):
                        continue
                    
                    for forbidden in user_facing_forbidden:
                        # Allow specific exceptions
                        if forbidden == "verified" and "not verified" in string_val:
                            continue
                        if "does not verify" in string_val:
                            continue
                        if "reference-only" in string_val:
                            continue
                        
                        if forbidden.lower() in string_val:
                            # Check if it's in a test context
                            if "forbidden" in string_val or "test" in string_val:
                                continue
                            assert False, (
                                f"Forbidden language '{forbidden}' in {py_file.name}: "
                                f"{node.value[:50]}..."
                            )


class TestForbiddenLanguageValidator:
    """Test the forbidden language validator function."""
    
    def test_validator_rejects_verification(self):
        """Validator must reject verification language."""
        from phase16_ui.strings import UIStrings
        
        assert not UIStrings.validate_no_forbidden("This is verified")
        assert not UIStrings.validate_no_forbidden("Confirmed vulnerability")
    
    def test_validator_rejects_recommendation(self):
        """Validator must reject recommendation language."""
        from phase16_ui.strings import UIStrings
        
        # "recommend" is in the forbidden list
        assert not UIStrings.validate_no_forbidden("We recommend this")
    
    def test_validator_rejects_scoring(self):
        """Validator must reject scoring language."""
        from phase16_ui.strings import UIStrings
        
        assert not UIStrings.validate_no_forbidden("High severity")
        assert not UIStrings.validate_no_forbidden("Priority: Critical")
    
    def test_validator_rejects_ai(self):
        """Validator must reject AI language."""
        from phase16_ui.strings import UIStrings
        
        assert not UIStrings.validate_no_forbidden("AI-powered analysis")
        assert not UIStrings.validate_no_forbidden("Intelligent detection")
    
    def test_validator_accepts_neutral(self):
        """Validator must accept neutral language."""
        from phase16_ui.strings import UIStrings
        
        # These should pass - no forbidden words
        assert UIStrings.validate_no_forbidden("CVE reference")
        assert UIStrings.validate_no_forbidden("Evidence preview")
        assert UIStrings.validate_no_forbidden("Data display")
