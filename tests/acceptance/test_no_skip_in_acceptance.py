"""Gate test: Enforce no pytest.skip in acceptance tests.

This tripwire ensures all acceptance tests are fail-closed, not skip-based.
"""

import ast
from pathlib import Path


def test_no_skip_in_acceptance_tests():
    """Verify that acceptance tests do not use pytest.skip().

    Policy: Acceptance tests must be fail-closed.
    - Use pytest.fail() for precondition failures
    - Use deterministic fixtures that guarantee preconditions
    - Use @pytest.mark.slow for environment-dependent tests

    Skip-based tests create "verde falso" (false green) in CI.
    """
    acceptance_dir = Path(__file__).parent

    violations = []

    for test_file in acceptance_dir.glob("test_*.py"):
        # Skip this meta-test file
        if test_file.name == "test_no_skip_in_acceptance.py":
            continue

        content = test_file.read_text()
        tree = ast.parse(content)

        for node in ast.walk(tree):
            # Check for pytest.skip() calls
            if isinstance(node, ast.Call):
                func = node.func

                # Pattern 1: pytest.skip(...)
                if isinstance(func, ast.Attribute):
                    if func.attr == "skip":
                        if isinstance(func.value, ast.Name) and func.value.id == "pytest":
                            violations.append(f"{test_file.name}:{node.lineno}: pytest.skip() call")

            # Check for @pytest.mark.skip decorator
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Attribute):
                        if decorator.attr == "skip":
                            violations.append(
                                f"{test_file.name}:{node.lineno}: @pytest.mark.skip on {node.name}"
                            )
                    elif isinstance(decorator, ast.Call):
                        func = decorator.func
                        if isinstance(func, ast.Attribute) and func.attr == "skip":
                            violations.append(
                                f"{test_file.name}:{node.lineno}: @pytest.mark.skip on {node.name}"
                            )

    assert len(violations) == 0, (
        f"Found {len(violations)} skip violations in acceptance tests:\n"
        + "\n".join(f"  - {v}" for v in violations)
        + "\n\nPolicy: Use pytest.fail() or deterministic fixtures instead of pytest.skip()"
    )


def test_no_xfail_in_acceptance_tests():
    """Verify that acceptance tests do not use pytest.xfail().

    xfail creates "expected failures" that can mask real bugs.
    """
    acceptance_dir = Path(__file__).parent

    violations = []

    for test_file in acceptance_dir.glob("test_*.py"):
        if test_file.name == "test_no_skip_in_acceptance.py":
            continue

        content = test_file.read_text()
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute):
                    if func.attr == "xfail":
                        violations.append(f"{test_file.name}:{node.lineno}: pytest.xfail() call")

    assert len(violations) == 0, f"Found {len(violations)} xfail violations:\n" + "\n".join(
        f"  - {v}" for v in violations
    )
