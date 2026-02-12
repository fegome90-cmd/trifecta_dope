"""
Acceptance tests for ctx sync preconditions - Error Card system.

Black-box tests using subprocess (no mocks).
Tests verify Error Card classification is STRICT (only for prime file missing).
"""

import subprocess
from pathlib import Path

TRIFECTA_ROOT = Path(__file__).resolve().parents[2]


def run_trifecta(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    """Execute trifecta CLI and capture output."""
    return subprocess.run(
        ["uv", "--directory", str(TRIFECTA_ROOT), "run", "trifecta", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def test_ctx_sync_fails_when_prime_missing(tmp_path: Path):
    """ctx sync must fail with Error Card when prime file is missing."""
    segment = tmp_path / "test_segment"
    segment.mkdir()

    # Create minimal _ctx structure without prime file
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir()

    # Create pyproject.toml (required by segment resolution)
    (segment / "pyproject.toml").write_text("[project]\nname='test_segment'\nversion='0.0.1'\n")

    # ctx sync should fail with Error Card (precondition)
    p_sync = run_trifecta("ctx", "sync", "-s", str(segment), cwd=segment)
    combined = (p_sync.stdout or "") + "\n" + (p_sync.stderr or "")

    # Assertions: fail-closed with stable error card
    assert p_sync.returncode == 1, f"Expected exit 1, got {p_sync.returncode}"
    assert "TRIFECTA_ERROR_CODE: SEGMENT_NOT_INITIALIZED" in combined, combined
    assert "CLASS: PRECONDITION" in combined, combined
    assert "NEXT_STEPS:" in combined, combined
    assert "trifecta create" in combined, combined
    assert "trifecta refresh-prime" in combined, combined
    assert "Traceback" not in combined, combined


def test_ctx_sync_succeeds_after_initialization(tmp_path: Path):
    """ctx sync must succeed after create→refresh-prime workflow (real dogfooding)."""
    segment = tmp_path / "test_segment"
    segment.mkdir()

    # Create pyproject.toml (required for segment resolution)
    (segment / "pyproject.toml").write_text("[project]\nname='test_segment'\nversion='0.0.1'\n")

    # Real dogfooding: create + refresh-prime + sync
    p_create = run_trifecta("create", "-s", str(segment), cwd=segment)
    assert p_create.returncode == 0, p_create.stdout + "\n" + p_create.stderr

    p_prime = run_trifecta("refresh-prime", "-s", str(segment), cwd=segment)
    assert p_prime.returncode == 0, p_prime.stdout + "\n" + p_prime.stderr

    p_sync = run_trifecta("ctx", "sync", "-s", str(segment), cwd=segment)
    combined = (p_sync.stdout or "") + "\n" + (p_sync.stderr or "")

    assert p_sync.returncode == 0, combined
    assert "Traceback" not in combined, combined


def test_ctx_sync_succeeds_with_valid_north_star_files(tmp_path: Path):
    """ctx sync must succeed when minimal North Star files exist."""
    segment = tmp_path / "test_segment"
    segment.mkdir()

    # Manually create minimal valid structure
    (segment / "skill.md").write_text("# Skill\n")
    (segment / "AGENTS.md").write_text("# Constitution\n\nRule 1: Be strict.\n")

    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir()

    agent_file = ctx_dir / "agent_test_segment.md"
    agent_file.write_text("# Agent\n")

    prime_file = ctx_dir / "prime_test_segment.md"
    prime_file.write_text(f"# Prime: test_segment\n\n> **REPO_ROOT**: `{segment}`\n")

    session_file = ctx_dir / "session_test_segment.md"
    session_file.write_text("# Session\n")

    (segment / "pyproject.toml").write_text("[project]\nname='test_segment'\nversion='0.0.1'\n")

    p_sync = run_trifecta("ctx", "sync", "-s", str(segment), cwd=segment)
    combined = (p_sync.stdout or "") + "\n" + (p_sync.stderr or "")

    assert p_sync.returncode == 0, combined
    assert "Traceback" not in combined, combined


def test_error_card_not_emitted_for_other_file_errors(tmp_path: Path):
    """TRIPWIRE: FileNotFoundError for non-prime files must NOT be classified as SEGMENT_NOT_INITIALIZED.

    This test ensures the Error Card handler only matches prime-specific errors.
    """
    segment = tmp_path / "test_segment"
    segment.mkdir()

    # Create _ctx with prime file (so prime check passes)
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir()
    prime_file = ctx_dir / "prime_test_segment.md"
    prime_file.write_text(f"# Prime: test_segment\n\n> **REPO_ROOT**: `{segment}`\n")

    (segment / "pyproject.toml").write_text("[project]\nname='test_segment'\nversion='0.0.1'\n")

    # Run sync - should succeed or fail with different error, but NOT SEGMENT_NOT_INITIALIZED
    p_sync = run_trifecta("ctx", "sync", "-s", str(segment), cwd=segment)
    combined = (p_sync.stdout or "") + "\n" + (p_sync.stderr or "")

    # If it failed but not for prime missing, SEGMENT_NOT_INITIALIZED should NOT appear
    if p_sync.returncode != 0 and "Expected prime file not found" not in combined:
        assert "TRIFECTA_ERROR_CODE: SEGMENT_NOT_INITIALIZED" not in combined, (
            f"False positive: SEGMENT_NOT_INITIALIZED emitted for non-prime error:\n{combined}"
        )


def test_create_from_different_cwd(tmp_path: Path):
    """CRITICAL: create -s <target> must write to target, not cwd.

    This is the scenario where an agent runs create from a different directory
    (e.g., the CLI repo) targeting a remote segment path.
    """
    # Create a "remote" segment directory
    target_segment = tmp_path / "remote_segment"
    target_segment.mkdir()

    # Create pyproject.toml in target
    (target_segment / "pyproject.toml").write_text(
        "[project]\nname='remote_segment'\nversion='0.0.1'\n"
    )

    # Run create from tmp_path (NOT from target_segment)
    # This simulates an agent running from a different directory
    p_create = run_trifecta("create", "-s", str(target_segment), cwd=tmp_path)
    assert p_create.returncode == 0, p_create.stdout + "\n" + p_create.stderr

    # CRITICAL: Files must be in target_segment, NOT in tmp_path
    target_ctx = target_segment / "_ctx"
    cwd_ctx = tmp_path / "_ctx"

    assert target_ctx.exists(), f"create did not create _ctx in target: {target_segment}"
    assert not cwd_ctx.exists(), f"create wrongly created _ctx in cwd: {tmp_path}"

    # Verify correct files exist
    expected_prime = target_ctx / "prime_remote_segment.md"
    assert expected_prime.exists(), f"Prime not found: {expected_prime}"


def test_create_allows_immediate_ctx_reset(tmp_path: Path):
    """create should produce enough state so ctx reset --force works immediately."""
    segment = tmp_path / "reset_ready_segment"
    segment.mkdir()

    (segment / "pyproject.toml").write_text(
        "[project]\nname='reset_ready_segment'\nversion='0.0.1'\n"
    )

    p_create = run_trifecta("create", "-s", str(segment), cwd=segment)
    assert p_create.returncode == 0, p_create.stdout + "\n" + p_create.stderr

    p_reset = run_trifecta("ctx", "reset", "-s", str(segment), "--force", cwd=segment)
    combined = (p_reset.stdout or "") + "\n" + (p_reset.stderr or "")
    assert p_reset.returncode == 0, combined
