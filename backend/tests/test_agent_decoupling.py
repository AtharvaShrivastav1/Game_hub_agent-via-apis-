import ast
import os
import pytest

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS_DIR = os.path.join(BACKEND_DIR, "app", "agents")
TOOLS_DIR = os.path.join(BACKEND_DIR, "app", "tools")
GRAPH_DIR = os.path.join(BACKEND_DIR, "app", "graph")

FORBIDDEN_MODULE_SUBSTRINGS = [
    "app.database",
    "app.repositories",
    "app.services.cart_service",
    "app.services.purchase_service",
    "app.services.game_service",
    "app.services.chroma_service",
    "chromadb",
]

FORBIDDEN_NAMES = [
    "SessionLocal",
    "GameRepository",
    "LibraryRepository",
    "CartRepository",
    "UserRepository",
    "CartService",
    "PurchaseService",
    "GameService",
    "chroma_service",
]

def check_file_imports(filepath: str):
    """Parse python file AST and assert no forbidden modules or names are imported."""
    with open(filepath, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=filepath)

    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for forbidden in FORBIDDEN_MODULE_SUBSTRINGS:
                    if forbidden in alias.name:
                        violations.append(f"Import '{alias.name}' contains forbidden '{forbidden}'")
                for forbidden in FORBIDDEN_NAMES:
                    if forbidden == alias.name:
                        violations.append(f"Import '{alias.name}' matches forbidden name '{forbidden}'")

        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for forbidden in FORBIDDEN_MODULE_SUBSTRINGS:
                if forbidden in mod:
                    violations.append(f"ImportFrom module '{mod}' contains forbidden '{forbidden}'")
            for alias in node.names:
                for forbidden in FORBIDDEN_NAMES:
                    if forbidden == alias.name:
                        violations.append(f"ImportFrom symbol '{alias.name}' from '{mod}' is forbidden")

    return violations

def test_tools_layer_is_decoupled():
    """Verify app.tools has ZERO imports of database, repositories, services, or ChromaDB."""
    for root, _, files in os.walk(TOOLS_DIR):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                violations = check_file_imports(path)
                assert not violations, f"Architectural violation in {file}:\n" + "\n".join(violations)

def test_agents_layer_is_decoupled():
    """Verify app.agents has ZERO imports of database, repositories, domain services, or ChromaDB."""
    for root, _, files in os.walk(AGENTS_DIR):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                violations = check_file_imports(path)
                assert not violations, f"Architectural violation in {file}:\n" + "\n".join(violations)

def test_graph_nodes_layer_is_decoupled():
    """Verify app.graph has ZERO imports of database, repositories, domain services, or ChromaDB."""
    for root, _, files in os.walk(GRAPH_DIR):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                violations = check_file_imports(path)
                assert not violations, f"Architectural violation in {file}:\n" + "\n".join(violations)
