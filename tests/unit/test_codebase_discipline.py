import os
from pathlib import Path


def test_no_unwrap_in_src() -> None:
    """
    Strict Discipline: Prohibit usage of .unwrap() and .unwrap_err() in src/ code.

    These methods raise exceptions, which violates the "No Exceptions in Logic"
    principle of Trifecta's North Star. They should only be used in tests.
    """
    src_path = Path("src")
    if not src_path.exists():
        # If we aren't in repo root, try one level up or fail gracefully
        return

    violations: list[str] = []

    for root, _, files in os.walk(src_path):
        for file in files:
            if not file.endswith(".py"):
                continue

            file_path = Path(root) / file
            content = file_path.read_text()

            # Check for banned patterns
            lines = content.splitlines()
            for i, line in enumerate(lines, 1):
                if ".unwrap()" in line or ".unwrap_err()" in line:
                    # Ignore comments? Simple check for now.
                    # Ideally we want to allow it in comments, but strict is safer.
                    # If it's in a comment, it's likely describing it, which is edge case.
                    # Let's assume strict ban for now.
                    violations.append(f"{file_path}:{i} - {line.strip()}")

    if violations:
        formatted = "\n".join(violations)
        raise AssertionError(
            f"❌ Found banned .unwrap()/.unwrap_err() calls in src/:\n{formatted}\n"
            "Solution: Use pattern matching (match/case) or map/and_then combinators."
        )
