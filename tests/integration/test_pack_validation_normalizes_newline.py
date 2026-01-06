"""
Regression test for build/validate newline normalization contract.

CONTEXT:
- BuildContextPackUseCase normalizes files by adding '\n' if missing
- ValidateContextPackUseCase MUST apply same normalization
- Without this, files without trailing newline cause permanent hash mismatch

This test locks the contract: both phases must canonicalize content identically.
"""

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def mini_repo_no_trailing_newline(tmp_path: Path) -> Path:
    """Create minimal repo with file that lacks trailing newline."""
    repo = tmp_path / "test_repo"
    repo.mkdir()

    # Create metadata files
    (repo / "prime_test_repo.md").write_text("# Test Prime\nMinimal test segment.\n")
    (repo / "agent.md").write_text("# Agent Config\nTest agent.\n")
    (repo / "skill.md").write_text("# Skills\nTest skills.\n")

    # Create file WITHOUT trailing newline (the regression trigger)
    docs = repo / "docs"
    docs.mkdir()

    # Write content that does NOT end with newline
    test_file = docs / "no_newline.md"
    with open(test_file, "w") as f:
        f.write("# Test Document\n\nThis file lacks a trailing newline.")  # No final \n

    # Verify it really lacks newline
    content = test_file.read_text()
    assert not content.endswith("\n"), "Test setup error: file should lack trailing newline"

    return repo


def test_pack_build_and_validate_normalize_newlines_consistently(
    mini_repo_no_trailing_newline: Path,
) -> None:
    """
    Test that build + validate apply same newline normalization.

    REGRESSION: Without this, files lacking trailing newline cause:
    - Build: adds '\n', hashes normalized content
    - Validate: reads raw bytes, hash mismatch
    - Result: Infinite build->validate->fail loop

    EXPECTED: Sync completes without validation errors.
    """
    repo = mini_repo_no_trailing_newline

    # Get trifecta root for uv --directory
    trifecta_root = Path(__file__).resolve().parents[2]

    # Step 1: Bootstrap segment
    create_result = subprocess.run(
        [
            "uv",
            "--directory",
            str(trifecta_root),
            "run",
            "trifecta",
            "create",
            "--segment",
            str(repo),
        ],
        capture_output=True,
        text=True,
        cwd=repo.parent,
    )
    assert create_result.returncode == 0, f"create failed: {create_result.stderr}"

    # Step 2: Build + validate (sync includes validation by default)
    sync_result = subprocess.run(
        [
            "uv",
            "--directory",
            str(trifecta_root),
            "run",
            "trifecta",
            "ctx",
            "sync",
            "--segment",
            str(repo),
        ],
        capture_output=True,
        text=True,
        cwd=repo.parent,
    )

    # CRITICAL ASSERTION: Sync must pass validation
    # If build/validate don't normalize consistently, this will fail with hash mismatch
    assert sync_result.returncode == 0, (
        f"ctx sync failed (likely validation hash mismatch):\n"
        f"STDOUT:\n{sync_result.stdout}\n\n"
        f"STDERR:\n{sync_result.stderr}"
    )

    # Verify validation passed (not just build succeeded)
    assert "✅ Validation Passed" in sync_result.stdout, (
        f"Validation did not pass:\n{sync_result.stdout}"
    )

    # Verify no hash mismatch errors
    assert "Hash mismatch" not in sync_result.stdout, (
        f"Hash mismatch detected (normalization contract broken):\n{sync_result.stdout}"
    )

    # Verify pack was created
    pack_path = repo / "_ctx" / "context_pack.json"
    assert pack_path.exists(), "context_pack.json not created"

    # Verify pack is non-empty
    pack_size = pack_path.stat().st_size
    assert pack_size > 100, f"Pack suspiciously small: {pack_size} bytes"


def test_pack_validation_contract_documented_in_code(mini_repo_no_trailing_newline: Path) -> None:
    """
    Verify that build and validate phases document their normalization logic.

    This is a meta-test: ensures future developers see the contract explicitly.
    """
    use_cases_path = Path(__file__).resolve().parents[2] / "src" / "application" / "use_cases.py"

    content = use_cases_path.read_text()

    # Build phase should have normalization
    assert 'if not content.endswith("\\n"):' in content, (
        "BuildContextPackUseCase missing newline normalization"
    )
    assert 'content += "\\n"' in content, "BuildContextPackUseCase missing newline append"

    # This assertion ensures the contract is visible in the code
    # (Actual implementation verified by functional test above)
