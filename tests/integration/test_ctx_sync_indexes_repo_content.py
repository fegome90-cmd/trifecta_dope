"""
Test: ctx sync Indexes Repo Content (RED Test)

Validates that ctx sync indexes user content (docs/, src/), not just _ctx metadata.

Current behavior (FAIL): Pack only contains skill/prime/agent/session.
Expected behavior (PASS): Pack contains docs/servicio.md with token.

This test MUST FAIL until WO-0009 is implemented.
"""

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def mini_repo_with_content(tmp_path: Path) -> Path:
    """Create minimal repo with docs content to be indexed."""
    repo = tmp_path / "mini_repo_content"
    repo.mkdir()

    # Create docs with searchable token
    docs_dir = repo / "docs"
    docs_dir.mkdir()
    (docs_dir / "servicio.md").write_text(
        "# Servicio Documentation\n\n"
        "This document contains the SERVICIO_ANCHOR_TOKEN for testing.\n"
        "The service handles core operations.\n"
    )

    # Additional file
    (repo / "README.md").write_text("# Test Repo\n\nMinimal fixture.\n")

    return repo


def test_ctx_sync_indexes_docs_content(mini_repo_with_content: Path):
    """RED test: Verify ctx sync includes docs/ in context pack."""
    mini_repo = mini_repo_with_content
    pack_path = mini_repo / "_ctx" / "context_pack.json"

    # Bootstrap
    create_result = subprocess.run(
        ["uv", "run", "trifecta", "create", "--segment", str(mini_repo)],
        capture_output=True,
        text=True,
        cwd=mini_repo.parent,
    )
    assert create_result.returncode == 0, f"create failed:\n{create_result.stderr}"

    sync_result = subprocess.run(
        ["uv", "run", "trifecta", "ctx", "sync", "--segment", str(mini_repo)],
        capture_output=True,
        text=True,
        cwd=mini_repo.parent,
    )
    assert sync_result.returncode == 0, f"sync failed:\n{sync_result.stderr}"

    # Assert: pack exists
    assert pack_path.exists(), f"Pack not created at {pack_path}"

    # Assert: pack contains the token from docs/servicio.md
    pack_content = pack_path.read_text()
    assert "SERVICIO_ANCHOR_TOKEN" in pack_content, (
        f"Pack does not contain 'SERVICIO_ANCHOR_TOKEN' from docs/servicio.md\n"
        f"This means ctx sync is not indexing repo content, only _ctx metadata.\n"
        f"Pack size: {len(pack_content)} chars"
    )

    print("✓ Pack contains repo content (docs/servicio.md indexed)")


def test_ctx_search_finds_indexed_content(mini_repo_with_content: Path):
    """RED test: Verify ctx search can find content from docs/."""
    mini_repo = mini_repo_with_content

    # Bootstrap
    subprocess.run(
        ["uv", "run", "trifecta", "create", "--segment", str(mini_repo)],
        check=True,
        capture_output=True,
        cwd=mini_repo.parent,
    )
    subprocess.run(
        ["uv", "run", "trifecta", "ctx", "sync", "--segment", str(mini_repo)],
        check=True,
        capture_output=True,
        cwd=mini_repo.parent,
    )

    # Search for token
    search_result = subprocess.run(
        [
            "uv",
            "run",
            "trifecta",
            "ctx",
            "search",
            "--segment",
            str(mini_repo),
            "--query",
            "SERVICIO_ANCHOR_TOKEN",
            "--limit",
            "3",
        ],
        capture_output=True,
        text=True,
        cwd=mini_repo.parent,
    )

    # Assert: search returns hits
    import re

    id_pattern = re.compile(r"prime:\w+:chunk-\d+")
    ids_found = id_pattern.findall(search_result.stdout)

    assert len(ids_found) > 0, (
        f"Search for 'SERVICIO_ANCHOR_TOKEN' returned 0 hits.\n"
        f"This means either:\n"
        f"  1. ctx sync didn't index docs/servicio.md\n"
        f"  2. ctx search doesn't search indexed content\n"
        f"Output: {search_result.stdout}"
    )

    print(f"✓ Search found {len(ids_found)} chunk(s) with token")
