"""Unit tests for Legacy Scan Use Case."""

import json
from pathlib import Path
from src.domain.result import Ok, Err
# We will create this UseCase/function soon
# scan_legacy(repo_root: Path, manifest_path: Path) -> Result[...]


from typing import Any


def test_scan_legacy_clean(tmp_path: Path, monkeypatch: Any) -> None:
    """Test passes when no legacy files exist."""
    manifest = tmp_path / "legacy_manifest.json"
    manifest.write_text("[]")

    # Empty repo
    repo = tmp_path / "repo"
    repo.mkdir()

    # Mocking implementation for TDD
    from src.application.legacy_use_case import scan_legacy

    result = scan_legacy(repo, manifest)
    assert result.is_ok()


def test_scan_legacy_declared_passes(tmp_path: Path) -> None:
    """Test passes when found legacy is in manifest."""
    manifest = tmp_path / "legacy_manifest.json"
    manifest.write_text(
        json.dumps([{"path": "_ctx/agent.md", "reason": "test", "replacement": "fix"}])
    )

    repo = tmp_path / "repo"
    repo.mkdir()
    ctx = repo / "_ctx"
    ctx.mkdir()
    (ctx / "agent.md").touch()  # Exists and declared

    from src.application.legacy_use_case import scan_legacy

    result = scan_legacy(repo, manifest)
    assert result.is_ok()


def test_scan_legacy_undeclared_fails(tmp_path: Path) -> None:
    """Test fails when found legacy is NOT in manifest."""
    manifest = tmp_path / "legacy_manifest.json"
    manifest.write_text("[]")  # Empty manifest

    repo = tmp_path / "repo"
    repo.mkdir()
    ctx = repo / "_ctx"
    ctx.mkdir()
    (ctx / "agent.md").touch()  # Exists but undeclared

    from src.application.legacy_use_case import scan_legacy

    result = scan_legacy(repo, manifest)
    assert result.is_err()
    assert "Undeclared legacy found: _ctx/agent.md" in str(result.unwrap_err())
