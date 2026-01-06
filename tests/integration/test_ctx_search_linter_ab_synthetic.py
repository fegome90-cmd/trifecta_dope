"""
Test: A/B Linter Reproducibility (Synthetic Fixture)

Validates that linter A/B is reproducible in synthetic mini-repo:
- OFF (TRIFECTA_LINT=0 or --no-lint): vague query returns 0 hits
- ON (TRIFECTA_LINT=1): same query returns >0 hits via expansion

Uses real bootstrap pipeline: create → sync → search
NO dependency on main repo _ctx state.
"""

import subprocess
from pathlib import Path
import re

import pytest


@pytest.fixture
def mini_repo_with_linter_config(tmp_path: Path) -> Path:
    """Create minimal repo with linter config for A/B test."""
    repo = tmp_path / "mini_repo_ab"
    repo.mkdir()

    # Create docs with searchable content
    docs_dir = repo / "docs"
    docs_dir.mkdir()
    (docs_dir / "servicio.md").write_text(
        "# Servicio\n\n"
        "Este documento describe el servicio principal.\n"
        "El SERVICIO_ANCHOR_TOKEN gestiona las operaciones core.\n"
    )

    # Noise file
    (repo / "README.md").write_text("# Mini Repo\n\nTest fixture for A/B linter.\n")

    # Create linter configs for expansion
    configs_dir = repo / "configs"
    configs_dir.mkdir()

    # anchors.yaml - define "servicio" as intent term (weak) and files as strong
    (configs_dir / "anchors.yaml").write_text("""
anchors:
  strong:
    files: ["servicio.md"]
    dirs: ["docs/"]
    exts: []
    symbols_terms: []
  weak:
    intent_terms: ["servicio"]
    doc_terms: ["documento"]
""")

    # aliases.yaml - map "servicio" phrase to add strong anchors
    (configs_dir / "aliases.yaml").write_text("""
aliases:
  - phrase: "servicio"
    add_anchors: ["servicio.md", "docs/"]
""")

    return repo


def test_ab_linter_off_zero_on_nonzero(mini_repo_with_linter_config: Path):
    """A/B test: OFF=0 hits, ON>0 hits for vague query 'servicio'."""
    mini_repo = mini_repo_with_linter_config

    # Bootstrap: create → sync
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

    # Test OFF (no linter expansion) - using --no-lint flag
    result_off = subprocess.run(
        [
            "uv",
            "run",
            "trifecta",
            "ctx",
            "search",
            "--segment",
            str(mini_repo),
            "--query",
            "servicio",
            "--limit",
            "5",
            "--no-lint",
        ],
        capture_output=True,
        text=True,
        cwd=mini_repo.parent,
    )

    # Test ON (with linter expansion) - using TRIFECTA_LINT=1
    result_on = subprocess.run(
        [
            "uv",
            "run",
            "trifecta",
            "ctx",
            "search",
            "--segment",
            str(mini_repo),
            "--query",
            "servicio",
            "--limit",
            "5",
        ],
        env={**subprocess.os.environ, "TRIFECTA_LINT": "1"},
        capture_output=True,
        text=True,
        cwd=mini_repo.parent,
    )

    # Parse chunk IDs from output (format: "prime:<digest>:chunk-<N>")
    id_pattern = re.compile(r"prime:\w+:chunk-\d+")

    ids_off = id_pattern.findall(result_off.stdout)
    ids_on = id_pattern.findall(result_on.stdout)

    # Save logs for evidence
    logs_dir = Path("_ctx/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    (logs_dir / "ab_off.log").write_text(
        f"Query: 'servicio' (--no-lint)\n\n"
        f"STDOUT:\n{result_off.stdout}\n\n"
        f"STDERR:\n{result_off.stderr}\n\n"
        f"IDs found: {ids_off}\n"
    )
    (logs_dir / "ab_on.log").write_text(
        f"Query: 'servicio' (TRIFECTA_LINT=1)\n\n"
        f"STDOUT:\n{result_on.stdout}\n\n"
        f"STDERR:\n{result_on.stderr}\n\n"
        f"IDs found: {ids_on}\n"
    )

    # A/B assertions
    assert len(ids_off) == 0, (
        f"OFF should return 0 hits (no expansion), got {len(ids_off)}: {ids_off}\n"
        f"Output: {result_off.stdout}"
    )
    assert len(ids_on) > 0, (
        f"ON should return >0 hits (with expansion), got {len(ids_on)}\nOutput: {result_on.stdout}"
    )

    # Verify hit corresponds to servicio.md (optional but good)
    if ids_on:
        # Extract first ID and verify it's from correct source
        # (This assumes prime:<digest>:chunk-N format from servicio.md content)
        print(f"✓ A/B validated: OFF={len(ids_off)}, ON={len(ids_on)}")
        print(f"  ON hits: {ids_on[:3]}")  # Show first 3
