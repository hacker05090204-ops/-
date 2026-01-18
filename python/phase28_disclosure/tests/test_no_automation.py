import pytest
import ast
import os
import inspect

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

def test_no_automation_functions():
    """Verify no function starts with 'auto_'."""
    sources = get_source_files()
    for source_path in sources:
        with open(source_path, "r") as f:
            tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name.startswith("auto_"):
                        pytest.fail(f"Found forbidden auto_ function: {node.name} in {source_path}")

def test_no_network_libraries():
    """Verify no import of requests, urllib, etc."""
    forbidden = ["requests", "urllib", "httpx", "aiohttp"]
    sources = get_source_files()
    for source_path in sources:
        with open(source_path, "r") as f:
            tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        if name.name in forbidden:
                            pytest.fail(f"Found forbidden network import: {name.name} in {source_path}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module in forbidden:
                        pytest.fail(f"Found forbidden network import: {node.module} in {source_path}")
