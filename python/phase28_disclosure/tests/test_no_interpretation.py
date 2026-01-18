import pytest
import ast
import os

def get_source_files():
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sources = []
    for root, _, files in os.walk(base_path):
        if "tests" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                sources.append(os.path.join(root, file))
    return sources

def test_no_score_rank_logic():
    """Verify no logic for scoring or ranking."""
    forbidden_terms = ["score", "rank", "priority", "severity", "confidence"]
    # Exception: we can use them in Types definitions if needed for formatting input, 
    # but not for calculation. Static check is strict for now.
    
    sources = get_source_files()
    for source_path in sources:
        with open(source_path, "r") as f:
            content = f.read().lower()
            # This is a heuristic text scan
            # We strictly ban these words in function names for now
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for term in forbidden_terms:
                        if term in node.name.lower():
                             pytest.fail(f"Found forbidden interpretation term '{term}' in function {node.name} in {source_path}")

def test_no_nlp_libraries():
    """Verify no NLP libs."""
    forbidden = ["nltk", "spacy", "transformers", "textblob"]
    sources = get_source_files()
    for source_path in sources:
        with open(source_path, "r") as f:
            tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        if name.name in forbidden:
                            pytest.fail(f"Found forbidden NLP import: {name.name} in {source_path}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module in forbidden:
                         pytest.fail(f"Found forbidden NLP import: {node.module} in {source_path}")
