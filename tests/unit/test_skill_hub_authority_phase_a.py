"""Phase A authority-boundary tests for skill_hub change."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from src.infrastructure.cli import app


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


def _write_minimal_legacy_pack(segment: Path) -> None:
    """Write a minimal valid generic-style pack to simulate stale runtime state."""
    ctx_dir = segment / "_ctx"
    pack = {
        "schema_version": 1,
        "segment": segment.name,
        "source_files": [
            {"path": "skill.md", "sha256": "abc", "mtime": 0.0, "chars": 10},
        ],
        "chunks": [
            {
                "id": "repo:skill.md:deadbeef00",
                "doc": "repo:skill.md",
                "title_path": ["skill.md"],
                "text": "# stale\n",
                "char_count": 8,
                "token_est": 2,
                "source_path": "skill.md",
                "chunking_method": "whole_file",
            }
        ],
        "index": [
            {
                "id": "repo:skill.md:deadbeef00",
                "title_path_norm": "skill.md",
                "preview": "# stale",
                "token_est": 2,
            }
        ],
        "digest": "",
    }
    (ctx_dir / "context_pack.json").write_text(json.dumps(pack))


def test_ctx_sync_fails_closed_when_skill_hub_build_errors_even_with_stale_pack(
    tmp_path: Path,
) -> None:
    """skill_hub sync must fail, not silently keep serving stale generic pack."""
    segment = tmp_path / "skills-hub"
    segment.mkdir()
    (segment / "skill.md").write_text("# Segment metadata\n")
    (segment / "AGENTS.md").write_text("# Agents\n")
    _write_skill_hub_config(segment)
    _write_required_ctx_files(segment)
    _write_minimal_legacy_pack(segment)
    # no skills_manifest.json -> build should fail in skill_hub path

    runner = CliRunner()
    result = runner.invoke(app, ["ctx", "sync", "--segment", str(segment)])

    assert result.exit_code != 0
    combined = (result.stdout + result.stderr).lower()
    assert "build complete" not in combined
    assert "build failed" in combined


def test_skill_hub_admission_normalizes_v1_manifest_and_persists_canonical(
    tmp_path: Path,
) -> None:
    """Admission boundary must persist canonical schema v2 manifest before runtime use."""
    from src.application.use_cases import BuildContextPackUseCase
    from src.domain.result import Ok
    from src.infrastructure.file_system import FileSystemAdapter

    segment = tmp_path / "skills-hub"
    segment.mkdir()
    (segment / "skill.md").write_text("# Segment metadata\n")
    _write_skill_hub_config(segment)

    # file that migration should target
    (segment / "tdd-coach.md").write_text("# Skill: tdd-coach\n")

    v1_manifest = {
        "schema_version": 1,
        "skills": [
            {
                "name": "tdd-coach",
                "source_path": "/tmp/somewhere/tdd-coach/SKILL.md",
                "description": "TDD helper",
                "source": "codex",
            }
        ],
    }
    manifest_path = segment / "_ctx" / "skills_manifest.json"
    manifest_path.write_text(json.dumps(v1_manifest))

    use_case = BuildContextPackUseCase(FileSystemAdapter())
    result = use_case.execute(segment)
    assert isinstance(result, Ok)

    persisted = json.loads(manifest_path.read_text())
    assert persisted["schema_version"] == 2
    assert persisted["skills"][0]["relative_path"] == "tdd-coach.md"
    assert persisted["skills"][0]["id"] == "skill:tdd-coach"
    assert "canonical" in persisted["skills"][0]


def test_skill_hub_admission_rejects_missing_explicit_canonical_flag(tmp_path: Path) -> None:
    """Shape gate: canonical contract requires explicit canonical field."""
    from src.application.use_cases import BuildContextPackUseCase
    from src.domain.result import Err
    from src.infrastructure.file_system import FileSystemAdapter

    segment = tmp_path / "skills-hub"
    segment.mkdir()
    (segment / "skill.md").write_text("# Segment metadata\n")
    _write_skill_hub_config(segment)
    (segment / "x.md").write_text("# x\n")

    bad_v2 = {
        "schema_version": 2,
        "skills": [
            {
                "id": "skill:x",
                "name": "x",
                "relative_path": "x.md",
                "description": "x",
                "source": "test",
                # missing canonical on purpose
            }
        ],
    }
    (segment / "_ctx" / "skills_manifest.json").write_text(json.dumps(bad_v2))

    use_case = BuildContextPackUseCase(FileSystemAdapter())
    result = use_case.execute(segment)

    assert isinstance(result, Err)
    assert any("shape" in err.lower() for err in result.error)


def test_skill_hub_admission_rejects_non_skill_id_shape_violation(tmp_path: Path) -> None:
    """Shape gate: canonical ids must use skill:* family."""
    from src.application.use_cases import BuildContextPackUseCase
    from src.domain.result import Err
    from src.infrastructure.file_system import FileSystemAdapter

    segment = tmp_path / "skills-hub"
    segment.mkdir()
    (segment / "skill.md").write_text("# Segment metadata\n")
    _write_skill_hub_config(segment)
    (segment / "x.md").write_text("# x\n")

    bad_v2 = {
        "schema_version": 2,
        "skills": [
            {
                "id": "repo:x",
                "name": "x",
                "relative_path": "x.md",
                "description": "x",
                "source": "test",
                "canonical": True,
            }
        ],
    }
    (segment / "_ctx" / "skills_manifest.json").write_text(json.dumps(bad_v2))

    result = BuildContextPackUseCase(FileSystemAdapter()).execute(segment)
    assert isinstance(result, Err)
    assert any("shape" in err.lower() and "skill:" in err.lower() for err in result.error)


def test_skill_hub_admission_rejects_policy_mismatch_before_build(tmp_path: Path) -> None:
    """Policy consistency gate rejects non-skill_hub promotion requests."""
    from src.domain.result import Err
    from src.domain.skill_manifest import SkillManifest

    segment = tmp_path / "skills-hub"
    segment.mkdir()
    manifest_path = segment / "_ctx" / "skills_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({"schema_version": 2, "skills": []}))

    result = SkillManifest.admit_and_persist(
        manifest_path,
        segment,
        declared_policy="generic",
    )

    assert isinstance(result, Err)
    assert any("policy consistency" in err.lower() for err in result.error)


def test_skill_hub_pack_admission_rejects_non_canonical_extra_entries() -> None:
    """Closure gate: pack cannot contain paths outside canonical manifest."""
    from src.domain.result import Err
    from src.domain.skill_manifest import SkillManifest, SkillManifestEntry

    manifest = SkillManifest(
        schema_version=2,
        skills=(
            SkillManifestEntry(
                id="skill:x",
                name="x",
                relative_path="x.md",
                description="x",
                source="test",
                canonical=True,
            ),
        ),
    )

    result = SkillManifest.validate_pack_admission(
        manifest,
        declared_policy="skill_hub",
        pack_chunk_ids=["skill:x:abc", "skill:y:def"],
        pack_docs=["skill", "skill"],
        pack_source_paths=["x.md", "y.md"],
    )

    assert isinstance(result, Err)
    assert any("closure" in err.lower() for err in result.error)
