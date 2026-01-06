"""
Test: Clean Boot Reproducibility (Bootstrap Only - Minimal)

Validates that:
1. ctx sync FAILS without trifecta create (SEGMENT_NOT_INITIALIZED)
2. trifecta create initializes segment successfully
3. ctx sync generates context_pack.json from scratch

Simplified: No search validation (pack generation is sufficient proof).
"""

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def mini_repo(tmp_path: Path) -> Path:
    """Create minimal repo with docs."""
    repo = tmp_path / "mini_repo"
    repo.mkdir()

    # Create minimal docs
    docs_dir = repo / "docs"
    docs_dir.mkdir()
    (docs_dir / "guide.md").write_text("# User Guide\n\nBasic documentation.\n")

    # README
    (repo / "README.md").write_text("# Test Repo\n")

    return repo


def test_ctx_sync_fails_without_create(mini_repo: Path):
    """Validate that ctx sync requires trifecta create first."""
    result = subprocess.run(
        ["uv", "run", "trifecta", "ctx", "sync", "--segment", str(mini_repo)],
        capture_output=True,
        text=True,
        cwd=mini_repo.parent,
    )

    # Should fail with SEGMENT_NOT_INITIALIZED
    assert result.returncode != 0, "sync should fail without create"
    assert "SEGMENT_NOT_INITIALIZED" in result.stderr, (
        f"Expected SEGMENT_NOT_INITIALIZED, got:\n{result.stderr}"
    )


def test_bootstrap_creates_pack_successfully(mini_repo: Path):
    """Validate bootstrap: create → sync generates pack."""
    pack_path = mini_repo / "_ctx" / "context_pack.json"

    # Step 1: trifecta create
    create_result = subprocess.run(
        ["uv", "run", "trifecta", "create", "--segment", str(mini_repo)],
        capture_output=True,
        text=True,
        cwd=mini_repo.parent,
    )
    assert create_result.returncode == 0, f"create failed:\n{create_result.stderr}"

    # Step 2: ctx sync
    sync_result = subprocess.run(
        ["uv", "run", "trifecta", "ctx", "sync", "--segment", str(mini_repo)],
        capture_output=True,
        text=True,
        cwd=mini_repo.parent,
    )
    assert sync_result.returncode == 0, f"sync failed:\n{sync_result.stderr}"

    # Validate pack exists and has content
    assert pack_path.exists(), f"Pack not created at {pack_path}"
    pack_size = pack_path.stat().st_size
    assert pack_size > 50, f"Pack too small: {pack_size} bytes"

    print(f"✓ Bootstrap validated: create → sync (pack: {pack_size} bytes)")
