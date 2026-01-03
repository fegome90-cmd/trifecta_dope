import re
from pathlib import Path
import pytest


def test_prime_paths_strict_format():
    """Tripwire: Prime MUST contain strictly relative paths, no noise."""
    prime_path = Path("_ctx/prime_trifecta_dope.md")
    if not prime_path.exists():
        pytest.skip("Prime file not found")

    content = prime_path.read_text()
    lines = content.splitlines()

    # 1. Check Contract Header existence
    assert "Prime contiene SOLO paths" in content, "Missing Prime Contract Header"

    # Extract numbered items 1-10
    # Logic: Look for lines starting with digit + "."
    item_lines = [line.strip() for line in lines if re.match(r"^\d+\.", line.strip())]

    assert len(item_lines) >= 9, f"Expected at least 9 high priority items, found {len(item_lines)}"

    repo_root_marker = "**REPO_ROOT**: "
    _repo_root_line = next((line for line in lines if repo_root_marker in line), None)
    repo_root = Path("..").resolve()  # Default assumption based on cwd=trifecta_dope

    for line in item_lines:
        # VALIDATION RULES

        # 1. Length < 200
        assert len(line) < 200, f"Line too long (chunk detected?): {line[:50]}..."

        # 2. No markdown headers or code blocks
        assert "```" not in line, f"Code block detected in item: {line}"
        assert not line.startswith("#"), f"Markdown header detected in item: {line}"

        # 3. No double spaces (formatting cleanliness)
        assert "  " not in line, f"Double spaces detected (formatting error?): {line}"

        # 4. No weird chunks or tags
        assert "chunk" not in line.lower(), f"'chunk' keyword detected: {line}"
        assert ": " not in line, f"Possible metadata key-value detected: {line}"

        # 5. Must extract a valid path
        # Format: "N. `path`"
        match = re.match(r"^\d+\.\s+`([^`]+)`$", line)
        if not match:
            # Maybe it's "N. path" without backticks? Strict rule says backticks usually safer but user said "solo path"
            # Previous replace put backticks.
            # Let's check if it matches loose format
            pytest.fail(f"Invalid item format. Expected 'N. `path`'. Got: {line}")

        path_str = match.group(1)

        # 6. Path Validity
        assert not path_str.startswith("/"), f"Absolute path prohibited: {path_str}"
        assert not path_str.startswith("http"), f"URL prohibited: {path_str}"

        # 7. Existence Check
        # We assume path is relative to repo root if it starts with 'trifecta_dope/'
        # Current CWD is 'trifecta_dope/' (the segment root).
        # So 'trifecta_dope/src/...' is actually '../trifecta_dope/src/...'

        real_path = repo_root / path_str
        # Fallback: maybe relative to segment?
        if not real_path.exists():
            real_path = Path(path_str)  # Relative to cwd

        assert real_path.exists(), f"Path does not exist on disk: {path_str} (Checked: {real_path})"
        assert real_path.is_file(), f"Path is not a file: {path_str}"
