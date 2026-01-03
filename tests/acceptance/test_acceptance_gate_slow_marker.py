"""Gate test: ensure slow tests are properly marked.

This tripwire ensures that env-dependent tests have @pytest.mark.slow.
"""

import ast
from pathlib import Path


def test_e2e_evidence_stop_has_slow_marker():
    """Verify test_e2e_evidence_stop_real_cli has @slow marker."""
    test_file = Path(__file__).parent / "test_pd_evidence_stop_e2e.py"
    content = test_file.read_text()

    # Parse AST to find the function
    tree = ast.parse(content)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "test_e2e_evidence_stop_real_cli":
            # Check for pytest.mark.slow decorator
            decorators = [d for d in node.decorator_list]
            decorator_names = []
            for d in decorators:
                if isinstance(d, ast.Attribute):
                    decorator_names.append(d.attr)
                elif isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute):
                    decorator_names.append(d.func.attr)

            assert "slow" in decorator_names, (
                f"test_e2e_evidence_stop_real_cli must have @pytest.mark.slow. "
                f"Found decorators: {decorator_names}"
            )
            return

    raise AssertionError("test_e2e_evidence_stop_real_cli not found in test file")
