"""Phase D integration tests (consumer cutover) for skill_hub."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from typer.testing import CliRunner

from src.infrastructure.cli_skills import skills_app


def test_extract_keywords_rejects_legacy_manifest_shape(tmp_path: Path) -> None:
    ctx_dir = tmp_path / "_ctx"
    ctx_dir.mkdir(parents=True, exist_ok=True)
    (ctx_dir / "skills_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "skills": [
                    {
                        "name": "legacy",
                        "source_path": "/tmp/legacy/SKILL.md",
                        "description": "legacy",
                    }
                ],
            }
        )
    )

    result = CliRunner().invoke(skills_app, ["--segment", str(tmp_path)])

    assert result.exit_code == 1
    assert "canonical manifest contract" in result.stderr


def test_extract_keywords_ignores_alias_side_channel_semantics(tmp_path: Path) -> None:
    ctx_dir = tmp_path / "_ctx"
    ctx_dir.mkdir(parents=True, exist_ok=True)
    (ctx_dir / "skills_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "skills": [
                    {
                        "id": "skill:python-testing",
                        "name": "python-testing",
                        "relative_path": "python-testing.md",
                        "description": "python testing workflows",
                        "source": "test",
                        "canonical": True,
                    },
                    {
                        "id": "skill:quality-review",
                        "name": "quality-review",
                        "relative_path": "quality-review.md",
                        "description": "testing quality reviews",
                        "source": "test",
                        "canonical": True,
                    },
                ],
            }
        )
    )
    (ctx_dir / "aliases.generated.yaml").write_text(
        yaml.safe_dump({"schema_version": 1, "aliases": {"testing": ["hijack-skill"]}})
    )

    result = CliRunner().invoke(
        skills_app,
        ["--segment", str(tmp_path), "--stdout", "--min-frequency", "1"],
    )

    assert result.exit_code == 0
    payload = yaml.safe_load(result.stdout)
    aliases = payload["aliases"]
    assert "testing" in aliases
    assert sorted(aliases["testing"]) == ["python-testing", "quality-review"]
