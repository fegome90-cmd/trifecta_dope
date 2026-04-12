"""Phase C runtime gating tests for skill_hub change."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.application.context_service import ContextService
from src.application.use_cases import BuildContextPackUseCase
from src.domain.result import Ok
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


def _tamper_live_pack(segment: Path) -> None:
    pack_path = segment / "_ctx" / "context_pack.json"
    payload = json.loads(pack_path.read_text())
    payload["chunks"][0]["id"] = "repo:tampered"
    payload["index"][0]["id"] = "repo:tampered"
    pack_path.write_text(json.dumps(payload))


def test_skill_hub_runtime_uses_last_valid_promoted_set_when_live_set_is_inadmissible(
    tmp_path: Path,
) -> None:
    segment = tmp_path / "skills-hub"
    segment.mkdir()
    (segment / "skill.md").write_text("# Segment metadata\n")
    (segment / "a.md").write_text("# A\n")
    _write_skill_hub_config(segment)
    _write_manifest(segment)
    _build_promoted_set(segment)

    _tamper_live_pack(segment)

    service = ContextService(segment)
    result = service.search("a", k=5)

    assert any(hit.id.startswith("skill:") for hit in result.hits)
    assert not any(hit.id.startswith("repo:") for hit in result.hits)


def test_skill_hub_runtime_fails_closed_when_no_valid_promoted_set_exists(tmp_path: Path) -> None:
    segment = tmp_path / "skills-hub"
    segment.mkdir()
    (segment / "skill.md").write_text("# Segment metadata\n")
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

    service = ContextService(segment)
    with pytest.raises(RuntimeError, match="No valid promoted set"):
        service.search("skill", k=5)


def test_skill_hub_runtime_rejects_unsealed_candidate_pack(tmp_path: Path) -> None:
    segment = tmp_path / "skills-hub"
    segment.mkdir()
    (segment / "skill.md").write_text("# Segment metadata\n")
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

    service = ContextService(segment)
    with pytest.raises(RuntimeError, match="No valid promoted set"):
        service.search("a", k=5)
