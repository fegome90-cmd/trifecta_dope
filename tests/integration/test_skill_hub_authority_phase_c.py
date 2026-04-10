"""Phase C integration tests (runtime gating) for skill_hub."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from src.application.use_cases import BuildContextPackUseCase
from src.domain.result import Ok
from src.infrastructure.cli import app
from src.infrastructure.file_system import FileSystemAdapter


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


def _build_promoted_set(segment: Path) -> None:
    result = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)
    assert isinstance(result, Ok)


def test_ctx_search_skill_hub_fails_closed_without_valid_promoted_set(tmp_path: Path) -> None:
    segment = tmp_path / "skills-hub"
    segment.mkdir()
    (segment / "skill.md").write_text("# Segment metadata\n")
    (segment / "AGENTS.md").write_text("# Agents\n")
    (segment / "a.md").write_text("# A\n")
    _write_skill_hub_config(segment)
    _write_manifest(segment)
    _build_promoted_set(segment)

    ctx_dir = segment / "_ctx"
    (ctx_dir / "skill_hub_promotion_receipt.json").unlink()
    last_valid_dir = ctx_dir / ".skill_hub_last_valid"
    for path in last_valid_dir.iterdir():
        path.unlink()
    last_valid_dir.rmdir()

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["ctx", "search", "--segment", str(segment), "--query", "skill", "--limit", "5"],
    )

    assert result.exit_code != 0
    assert "no valid promoted set" in result.output.lower()


def test_ctx_search_skill_hub_uses_last_valid_promoted_set_when_live_is_inadmissible(
    tmp_path: Path,
) -> None:
    segment = tmp_path / "skills-hub"
    segment.mkdir()
    (segment / "skill.md").write_text("# Segment metadata\n")
    (segment / "AGENTS.md").write_text("# Agents\n")
    (segment / "a.md").write_text("# A\n")
    _write_skill_hub_config(segment)
    _write_manifest(segment)
    _build_promoted_set(segment)

    pack_path = segment / "_ctx" / "context_pack.json"
    payload = json.loads(pack_path.read_text())
    payload["chunks"][0]["id"] = "repo:tampered"
    payload["index"][0]["id"] = "repo:tampered"
    pack_path.write_text(json.dumps(payload))

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["ctx", "search", "--segment", str(segment), "--query", "a.md", "--limit", "5"],
    )

    assert result.exit_code == 0
    assert "skill:" in result.output
    assert "repo:tampered" not in result.output


def test_ctx_get_skill_hub_fails_closed_without_valid_promoted_set(tmp_path: Path) -> None:
    segment = tmp_path / "skills-hub"
    segment.mkdir()
    (segment / "skill.md").write_text("# Segment metadata\n")
    (segment / "AGENTS.md").write_text("# Agents\n")
    (segment / "a.md").write_text("# A\n")
    _write_skill_hub_config(segment)
    _write_manifest(segment)
    _build_promoted_set(segment)

    ctx_dir = segment / "_ctx"
    pack = json.loads((ctx_dir / "context_pack.json").read_text())
    valid_chunk_id = pack["chunks"][0]["id"]

    (ctx_dir / "skill_hub_promotion_receipt.json").unlink()
    last_valid_dir = ctx_dir / ".skill_hub_last_valid"
    for path in last_valid_dir.iterdir():
        path.unlink()
    last_valid_dir.rmdir()

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["ctx", "get", "--segment", str(segment), "--ids", valid_chunk_id, "--mode", "excerpt"],
    )

    assert result.exit_code != 0
    assert "no valid promoted set" in result.output.lower()
