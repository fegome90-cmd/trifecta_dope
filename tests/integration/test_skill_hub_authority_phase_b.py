"""Phase B integration tests (promotion sealing) for skill_hub."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from src.infrastructure.cli import app
from src.infrastructure.file_system_utils import AtomicWriter


def _write_skill_hub_config(segment: Path, *, policy: str = "skill_hub") -> None:
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir(parents=True, exist_ok=True)
    (ctx_dir / "trifecta_config.json").write_text(
        json.dumps(
            {
                "segment": segment.name,
                "scope": "test",
                "repo_root": str(segment),
                "indexing_policy": policy,
            }
        )
    )


def _write_required_ctx_files(segment: Path) -> None:
    segment_id = segment.name
    ctx_dir = segment / "_ctx"
    (ctx_dir / f"prime_{segment_id}.md").write_text("# Prime\n")
    (ctx_dir / f"agent_{segment_id}.md").write_text("# Agent\n")
    (ctx_dir / f"session_{segment_id}.md").write_text("# Session\n")


def _write_manifest(segment: Path, *, description: str = "Skill A") -> None:
    manifest = {
        "schema_version": 2,
        "skills": [
            {
                "id": "skill:a",
                "name": "a",
                "relative_path": "a.md",
                "description": description,
                "source": "test",
                "canonical": True,
            }
        ],
    }
    (segment / "_ctx" / "skills_manifest.json").write_text(json.dumps(manifest))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_ctx_sync_skill_hub_publishes_sealed_promoted_set(tmp_path: Path) -> None:
    segment = tmp_path / "skills-hub"
    segment.mkdir()
    (segment / "skill.md").write_text("# Segment metadata\n")
    (segment / "AGENTS.md").write_text("# Agents\n")
    (segment / "a.md").write_text("# A\n")
    _write_skill_hub_config(segment)
    _write_required_ctx_files(segment)
    _write_manifest(segment)

    runner = CliRunner()
    result = runner.invoke(app, ["ctx", "sync", "--segment", str(segment)])
    assert result.exit_code == 0

    ctx_dir = segment / "_ctx"
    manifest_path = ctx_dir / "skills_manifest.json"
    pack_path = ctx_dir / "context_pack.json"
    receipt_path = ctx_dir / "skill_hub_promotion_receipt.json"
    assert manifest_path.exists()
    assert pack_path.exists()
    assert receipt_path.exists()

    receipt = json.loads(receipt_path.read_text())
    assert receipt["policy"] == "skill_hub"
    assert receipt["manifest_fingerprint"] == _sha256(manifest_path)
    assert receipt["pack_fingerprint"] == _sha256(pack_path)


def test_ctx_sync_skill_hub_keeps_last_valid_set_on_receipt_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    segment = tmp_path / "skills-hub"
    segment.mkdir()
    (segment / "skill.md").write_text("# Segment metadata\n")
    (segment / "AGENTS.md").write_text("# Agents\n")
    (segment / "a.md").write_text("# A v1\n")
    _write_skill_hub_config(segment)
    _write_required_ctx_files(segment)
    _write_manifest(segment, description="v1")

    runner = CliRunner()
    first = runner.invoke(app, ["ctx", "sync", "--segment", str(segment)])
    assert first.exit_code == 0

    ctx_dir = segment / "_ctx"
    manifest_path = ctx_dir / "skills_manifest.json"
    pack_path = ctx_dir / "context_pack.json"
    receipt_path = ctx_dir / "skill_hub_promotion_receipt.json"
    previous_manifest = manifest_path.read_text()
    previous_pack = pack_path.read_text()
    previous_receipt = receipt_path.read_text()

    (segment / "a.md").write_text("# A v2\n")
    _write_manifest(segment, description="v2")

    original_write = AtomicWriter.write

    def failing_write(path: Path, content: str) -> None:
        if path.name == "skill_hub_promotion_receipt.json":
            raise OSError("simulated receipt write failure")
        original_write(path, content)

    monkeypatch.setattr(AtomicWriter, "write", staticmethod(failing_write))

    failed = runner.invoke(app, ["ctx", "sync", "--segment", str(segment)])
    assert failed.exit_code != 0
    assert "build failed" in (failed.stdout + failed.stderr).lower()

    assert manifest_path.read_text() == previous_manifest
    assert pack_path.read_text() == previous_pack
    assert receipt_path.read_text() == previous_receipt
